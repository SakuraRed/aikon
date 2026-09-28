#!/usr/bin/env python3
"""Offline layered vector approximation for a single RGBA calibration image.

Requires existing numpy, scipy and Pillow. No network, browser, raster embedding,
or assertion of artistic quality. SVG clip paths are real vector geometry.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import sys
import time
import xml.etree.ElementTree as ET

for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[variable] = "1"

import numpy as np
from PIL import Image, ImageFilter, __version__ as PILLOW_VERSION
import scipy
from scipy import ndimage

VERSION = "0.1.1"
SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)


class Deadline:
    def __init__(self, seconds: float):
        self.started = time.monotonic()
        self.seconds = seconds

    def check(self) -> None:
        if time.monotonic() - self.started > self.seconds:
            raise TimeoutError("Internal processing deadline exceeded")


def tag(name: str) -> str:
    return "{" + SVG_NS + "}" + name


def hex_color(rgb: np.ndarray) -> str:
    return "#" + "".join(f"{int(round(float(value))):02x}" for value in rgb)


def keep_components(mask: np.ndarray, minimum: int) -> tuple[np.ndarray, int]:
    labels, count = ndimage.label(mask)
    areas = np.bincount(labels.ravel())
    keep = areas >= minimum
    keep[0] = False
    cleaned = keep[labels]
    return cleaned, int(np.count_nonzero(mask & ~cleaned))


def infer_eyes(rgb: np.ndarray, foreground: np.ndarray, deadline: Deadline) -> tuple[list[dict], dict]:
    """Heuristic: isolated dark components inside a mostly light skin surround."""
    h, w = foreground.shape
    dark = foreground & (rgb.max(axis=2) < 82) & (rgb.min(axis=2) < 65)
    dark[:int(h * 0.44)] = False
    labels, _ = ndimage.label(dark)
    areas = np.bincount(labels.ravel())
    regions = ndimage.find_objects(labels)
    candidates = []
    for component in np.flatnonzero((areas > h * w * 0.0015) & (areas < h * w * 0.04)):
        deadline.check()
        if component == 0:
            continue
        region = regions[component - 1]
        if region is None:
            continue
        component_mask = labels == component
        yy, xx = np.nonzero(component_mask)
        center = np.array([xx.mean(), yy.mean()])
        xy = np.column_stack((xx - center[0], yy - center[1]))
        values, vectors = np.linalg.eigh((xy.T @ xy) / len(xy))
        projections = xy @ vectors
        extents = np.ptp(projections, axis=0) + 1
        ratio = float(extents[1] / max(extents[0], 1))
        if not 1.5 <= ratio <= 4.2:
            continue
        surround = ndimage.binary_dilation(component_mask, iterations=max(4, round(w * 0.006))) & ~component_mask
        warm_light = (rgb[:, :, 0] > 185) & (rgb[:, :, 1] > 155) & (rgb[:, :, 2] > 130)
        light_fraction = float(np.count_nonzero(surround & warm_light) / max(1, np.count_nonzero(surround)))
        if light_fraction < 0.65:
            continue
        candidates.append({"component": int(component), "area": int(areas[component]), "center": center.tolist(), "ratio": ratio, "light_surround_fraction": light_fraction, "bbox": [region[1].start, region[0].start, region[1].stop, region[0].stop]})
    pairs = []
    for i, left in enumerate(candidates):
        for right in candidates[i + 1:]:
            if abs(left["center"][0] - right["center"][0]) < 0.15 * w:
                continue
            area_ratio = left["area"] / right["area"]
            if 0.55 < area_ratio < 1.8:
                score = left["light_surround_fraction"] + right["light_surround_fraction"] - abs(math.log(area_ratio)) * 0.1
                pairs.append((score, left, right))
    if not pairs:
        return [], {"status": "not_identified", "candidates": candidates, "limitation": "No reliable two-component pair; dark regions remain palette paths."}
    _, first, second = max(pairs, key=lambda value: value[0])
    selected = sorted((first, second), key=lambda value: value["center"][0])
    result = []
    for name, item in zip(("eye-left", "eye-right"), selected):
        mask = labels == item["component"]
        result.append({"id": name, "mask": mask, "fill": hex_color(np.median(rgb[mask], axis=0)), "measurements": item})
    return result, {"status": "heuristically_identified", "candidates": candidates, "selected": [{"id": item["id"], **item["measurements"]} for item in result], "limitation": "Dark isolated components surrounded by pale color are inferred eyes, not guaranteed semantic segmentation; inspect both IDs after rendering."}


def quantize(rgb: np.ndarray, alpha: np.ndarray, foreground: np.ndarray, colors: int, blur: float, minimum: int, mode_size: int, deadline: Deadline) -> tuple[np.ndarray, np.ndarray, dict]:
    weight = alpha.astype(np.float32) / 255
    denominator = ndimage.gaussian_filter(weight, blur)
    numerator = ndimage.gaussian_filter(rgb.astype(np.float32) * weight[:, :, None], (blur, blur, 0))
    smooth = np.clip(numerator / np.maximum(denominator[:, :, None], 1e-5), 0, 255).astype(np.uint8)
    samples = smooth[foreground]
    image = Image.fromarray(samples[np.newaxis, :, :])
    packed = image.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    index = np.asarray(packed)[0]
    palette = np.asarray(packed.getpalette(), dtype=np.uint8).reshape(-1, 3)[:colors]
    labels = np.full(foreground.shape, -1, dtype=np.int16)
    labels[foreground] = index
    changed_by_mode = 0
    if mode_size > 1:
        filtered = np.asarray(Image.fromarray(np.where(foreground, labels, 255).astype(np.uint8)).filter(ImageFilter.ModeFilter(size=mode_size))).astype(np.int16)
        filtered[filtered == 255] = -1
        changed_by_mode = int(np.count_nonzero(foreground & (filtered != labels)))
        labels[foreground] = filtered[foreground]
    removed = 0
    removed_components = 0
    for color_index in np.unique(index):
        deadline.check()
        mask = labels == color_index
        components, _ = ndimage.label(mask)
        areas = np.bincount(components.ravel())
        small = (areas < minimum) & (areas > 0)
        small[0] = False
        rejected = small[components]
        labels[rejected] = -1
        removed += int(np.count_nonzero(rejected))
        removed_components += int(np.count_nonzero(small))
    missing = foreground & (labels < 0)
    if np.any(missing):
        if not np.any(labels >= 0):
            raise ValueError("All palette components removed; lower --min-area")
        nearest = ndimage.distance_transform_edt(labels < 0, return_distances=False, return_indices=True)
        labels[missing] = labels[nearest[0][missing], nearest[1][missing]]
    return labels, palette, {"palette_requested": colors, "palette_used": int(len(np.unique(labels[foreground]))), "mode_filter_size": mode_size, "mode_filter_changed_pixels": changed_by_mode, "merged_small_region_pixels": removed, "merged_small_components": removed_components, "merge_rule": "Optional local mode filter regularizes label boundaries; 4-connected color regions below min-area are reassigned to the nearest retained opaque color pixel; foreground alpha shape unchanged."}


def trace_boundaries(mask: np.ndarray, deadline: Deadline) -> tuple[list[np.ndarray], int]:
    """Directed pixel-cell edges; foreground stays on the right, holes reverse."""
    h, w = mask.shape
    p = np.pad(mask, 1)
    conditions = (mask & ~p[:-2, 1:-1], mask & ~p[1:-1, 2:], mask & ~p[2:, 1:-1], mask & ~p[1:-1, :-2])
    starts, ends = [], []
    stride = w + 1
    for direction, condition in enumerate(conditions):
        y, x = np.nonzero(condition)
        if direction == 0:
            a, b = y * stride + x, y * stride + x + 1
        elif direction == 1:
            a, b = y * stride + x + 1, (y + 1) * stride + x + 1
        elif direction == 2:
            a, b = (y + 1) * stride + x + 1, (y + 1) * stride + x
        else:
            a, b = (y + 1) * stride + x, y * stride + x
        starts.extend(a.tolist())
        ends.extend(b.tolist())
    outgoing: dict[int, list[int]] = {}
    for a, b in zip(starts, ends):
        outgoing.setdefault(a, []).append(b)
    loops = []
    steps = 0
    direction_of = {1: 0, stride: 1, -1: 2, -stride: 3}
    priority = {1: 0, 0: 1, 3: 2, 2: 3}
    while outgoing:
        beginning = next(iter(outgoing))
        current = beginning
        previous_direction = None
        vertices = []
        while True:
            vertices.append((current % stride, current // stride))
            choices = outgoing.get(current)
            if not choices:
                raise ValueError("Open contour in directed edge walk")
            if len(choices) == 1 or previous_direction is None:
                following = choices.pop()
            else:
                following = min(choices, key=lambda nxt: priority[(direction_of[nxt - current] - previous_direction) % 4])
                choices.remove(following)
            if not choices:
                del outgoing[current]
            previous_direction = direction_of[following - current]
            current = following
            steps += 1
            if steps % 4096 == 0:
                deadline.check()
            if current == beginning:
                break
            if steps > len(starts):
                raise ValueError("Boundary walk did not close")
        loops.append(np.asarray(vertices, dtype=np.float64))
    area = sum(float(np.sum(loop[:, 0] * np.roll(loop[:, 1], -1) - np.roll(loop[:, 0], -1) * loop[:, 1])) / 2 for loop in loops)
    if abs(area - np.count_nonzero(mask)) > 0.01:
        raise ValueError("Contour area does not equal source mask area")
    return loops, len(starts)


def simplify_open(points: np.ndarray, tolerance: float) -> np.ndarray:
    retained = np.zeros(len(points), dtype=bool)
    retained[[0, -1]] = True
    pending = [(0, len(points) - 1)]
    while pending:
        first, last = pending.pop()
        if last <= first + 1:
            continue
        baseline = points[last] - points[first]
        offsets = points[first + 1:last] - points[first]
        length = float(np.linalg.norm(baseline))
        if length:
            distances = np.abs(offsets[:, 0] * baseline[1] - offsets[:, 1] * baseline[0]) / length
        else:
            distances = np.linalg.norm(offsets, axis=1)
        index = int(np.argmax(distances))
        if distances[index] > tolerance:
            split = first + 1 + index
            retained[split] = True
            pending.extend(((first, split), (split, last)))
    return points[retained]


def simplify_closed(points: np.ndarray, tolerance: float, smooth: float) -> np.ndarray:
    if len(points) <= 4:
        return points
    if smooth:
        points = ndimage.gaussian_filter1d(points, smooth, axis=0, mode="wrap")
    split = int(np.argmax(np.sum((points - points[0]) ** 2, axis=1)))
    left = simplify_open(points[:split + 1], tolerance)
    right = simplify_open(np.vstack((points[split:], points[:1])), tolerance)
    simplified = np.vstack((left[:-1], right[:-1]))
    return simplified if len(simplified) >= 3 else points[::max(1, len(points) // 4)][:4]


def curve_path(points: np.ndarray) -> str:
    """Corner-aware cubic interpolation with short, bounded tangent handles."""
    previous = np.roll(points, 1, axis=0)
    following = np.roll(points, -1, axis=0)
    incoming, outgoing = points - previous, following - points
    before, after = np.linalg.norm(incoming, axis=1), np.linalg.norm(outgoing, axis=1)
    cosine = np.sum(incoming * outgoing, axis=1) / np.maximum(before * after, 1e-9)
    direction = following - previous
    direction /= np.maximum(np.linalg.norm(direction, axis=1)[:, None], 1e-9)
    handles = direction * (np.minimum(before, after) * 0.28)[:, None]
    handles[cosine < math.cos(math.radians(42))] = 0
    def pair(point: np.ndarray) -> str:
        return f"{point[0]:.2f},{point[1]:.2f}"
    commands = ["M" + pair(points[0])]
    for i in range(len(points)):
        nxt = (i + 1) % len(points)
        if not np.any(handles[i]) and not np.any(handles[nxt]):
            commands.append("L" + pair(points[nxt]))
        else:
            commands.append("C" + pair(points[i] + handles[i]) + " " + pair(points[nxt] - handles[nxt]) + " " + pair(points[nxt]))
    return " ".join(commands) + " Z"


def mask_path(mask: np.ndarray, tolerance: float, smooth: float, deadline: Deadline) -> tuple[str, dict]:
    loops, edges = trace_boundaries(mask, deadline)
    simplified = [simplify_closed(loop, tolerance, smooth) for loop in loops]
    return " ".join(curve_path(loop) for loop in simplified), {"loops": len(loops), "raw_boundary_edges": edges, "curve_vertices": sum(map(len, simplified)), "grid_area_preserved_before_simplification": True}


def semantic_group(color: np.ndarray) -> str:
    r, g, b = map(float, color)
    if r > 205 and g > 160 and b > 135:
        return "face"
    if g > r * 1.08 and b > r * 1.02:
        return "halo"
    if r > g * 1.17 and r > b * 1.04:
        return "coral"
    if max(r, g, b) < 175 and max(r, g, b) - min(r, g, b) < 65:
        return "hair"
    return "other"


def rgba_metrics(reference: np.ndarray, actual: np.ndarray, mask: np.ndarray | None = None) -> dict:
    a = reference[:, :, 3].astype(np.float32) / 255
    b = actual[:, :, 3].astype(np.float32) / 255
    support = (a > 0) | (b > 0) if mask is None else mask
    left = reference[:, :, :3].astype(np.float32) * a[:, :, None]
    right = actual[:, :, :3].astype(np.float32) * b[:, :, None]
    black = left - right
    white = (left + 255 * (1 - a[:, :, None])) - (right + 255 * (1 - b[:, :, None]))
    selected = black[support]
    amask, bmask = a >= 0.5, b >= 0.5
    return {"support_pixels": int(support.sum()), "premultiplied_rgb_mae_0_255": float(np.mean(np.abs(selected))), "premultiplied_rgb_rmse_0_255": float(np.sqrt(np.mean(selected ** 2))), "white_composite_mae_0_255": float(np.mean(np.abs(white[support]))), "alpha_mae_0_255": float(np.mean(np.abs(a[support] - b[support])) * 255), "alpha_iou_at_128": float(np.count_nonzero(amask & bmask & support) / max(1, np.count_nonzero((amask | bmask) & support))), "pixels_rgb_max_error_over_20": int(np.count_nonzero(support & (np.max(np.abs(black), axis=2) > 20)))}


def run_diagnostics(args: argparse.Namespace) -> None:
    deadline = Deadline(args.max_seconds)
    previous = json.loads(Path(args.diagnose_log).read_text(encoding="utf-8"))
    settings = previous["parameters"]
    source = Path(args.input)
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    if source_hash != previous["input_sha256"]:
        raise ValueError("Diagnostic input differs from original vectorization source")
    original = np.asarray(Image.open(source).convert("RGBA"))
    actual = np.asarray(Image.open(args.actual_render).convert("RGBA"))
    if actual.shape != original.shape:
        raise ValueError("Actual render must have source dimensions; no silent resizing")
    rgb, alpha = original[:, :, :3], original[:, :, 3]
    foreground, _ = keep_components(alpha >= settings["alpha_threshold"], settings["alpha_min_area"])
    labels, palette, quantization = quantize(rgb, alpha, foreground, settings["colors"], settings["rgb_blur"], settings["min_area"], settings.get("mode_filter", 1), deadline)
    eyes, eye_report = infer_eyes(rgb, foreground, deadline)
    quantized = original.copy()
    quantized[foreground, :3] = palette[labels[foreground]]
    vector_input = np.zeros_like(original)
    vector_input[foreground, :3] = palette[labels[foreground]]
    interior = ndimage.binary_erosion(foreground, iterations=3)
    median_alpha = round(float(np.median(alpha[interior if interior.any() else foreground])))
    vector_input[foreground, 3] = median_alpha
    for eye in eyes:
        color = np.array([int(eye["fill"][i:i + 2], 16) for i in (1, 3, 5)], dtype=np.uint8)
        vector_input[eye["mask"], :3] = color
    prefix = Path(args.output)
    quantized_file = prefix.with_name(prefix.name + "-quantized-rgba.png")
    input_file = prefix.with_name(prefix.name + "-vector-input-rgba.png")
    report_file = prefix.with_name(prefix.name + "-comparison.json")
    if any(file.exists() for file in (quantized_file, input_file, report_file)):
        raise FileExistsError("Refusing to overwrite diagnostic files")
    prefix.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(quantized).save(quantized_file)
    Image.fromarray(vector_input).save(input_file)
    h, w = alpha.shape
    regions = {"whole_image": None}
    probes = [(784, 566), (476, 936), (164, 930), (727, 1125), (552, 462)]
    for name, bounds in {"face_center": (380, 800, 610, 1050), "left_blush": (90, 855, 255, 980), "hair_anomalous_patch": (740, 475, 870, 655), "hair_main": (470, 390, 790, 670)}.items():
        mask = np.zeros((h, w), dtype=bool)
        x0, y0, x1, y1 = bounds
        mask[y0:y1, x0:x1] = True
        regions[name] = mask
    comparisons = {}
    for name, mask in regions.items():
        comparisons[name] = {"source_to_quantization": rgba_metrics(original, quantized, mask), "quantization_to_vector_input": rgba_metrics(quantized, vector_input, mask), "vector_input_to_svg_render": rgba_metrics(vector_input, actual, mask), "source_to_svg_render": rgba_metrics(original, actual, mask)}
    report = {"schema": "aikon.vector-loss-decomposition.v1", "source": str(source), "source_sha256": source_hash, "previous_vector_log": args.diagnose_log, "actual_svg_render": args.actual_render, "settings_replayed": settings, "quantization_replay": quantization, "eye_replay": eye_report, "quantized_rgba": str(quantized_file), "vector_input_rgba": str(input_file), "definitions": {"quantized_rgba": "Replayed labels/palette inside alpha>=threshold; original alpha retained and low-alpha fringe colors untouched, isolating quantization color loss.", "vector_input_rgba": "Same replayed labels/palette plus the exact median-color eye substitution and threshold silhouette with median interior alpha used before vector paths.", "source_to_quantization": "Color quantization / smoothing / mode cleanup loss, before any paths.", "quantization_to_vector_input": "Eye fill simplification and alpha threshold / group opacity preparation.", "vector_input_to_svg_render": "Additional contour simplification / cubic fit / regrouping / overlap stroke / raster antialiasing effects.", "metrics": "Same-source sRGB numeric approximation diagnostics only; MAE/RMSE are not artistic scores and are not algebraically additive."}, "comparisons": comparisons, "pixel_probes": [{"xy": [x, y], "source": original[y, x].tolist(), "quantized": quantized[y, x].tolist(), "vector_input": vector_input[y, x].tolist(), "svg_render": actual[y, x].tolist(), "palette_index": int(labels[y, x])} for x, y in probes], "runtime_seconds": round(time.monotonic() - deadline.started, 3)}
    with report_file.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"report": str(report_file), "whole_image": comparisons["whole_image"]}, ensure_ascii=False))


def largest_component(mask: np.ndarray) -> np.ndarray:
    labels, _ = ndimage.label(mask)
    sizes = np.bincount(labels.ravel())
    if len(sizes) < 2:
        return np.zeros_like(mask)
    sizes[0] = 0
    return labels == int(np.argmax(sizes))


def regularize_region(mask: np.ndarray, sigma: float, minimum: int) -> np.ndarray:
    result = ndimage.gaussian_filter(mask.astype(np.float32), sigma) >= 0.5
    result, _ = keep_components(result, minimum)
    holes = ndimage.binary_fill_holes(result) & ~result
    labels, _ = ndimage.label(holes)
    sizes = np.bincount(labels.ravel())
    small = sizes < minimum
    small[0] = False
    return result | small[labels]


def fitted_ellipse(mask: np.ndarray) -> dict:
    y, x = np.nonzero(mask)
    if len(x) < 100:
        raise ValueError("Insufficient component pixels for smooth shape fit")
    center = np.array([x.mean(), y.mean()])
    xy = np.column_stack((x - center[0], y - center[1]))
    values, vectors = np.linalg.eigh(xy.T @ xy / len(xy))
    major = vectors[:, 1]
    return {"center": center.tolist(), "rx": float(2 * math.sqrt(values[1])), "ry": float(2 * math.sqrt(values[0])), "angle": math.degrees(math.atan2(major[1], major[0])), "area_pixels": len(x)}


def fitted_capsule(mask: np.ndarray) -> dict:
    y, x = np.nonzero(mask)
    center = np.array([x.mean(), y.mean()])
    xy = np.column_stack((x - center[0], y - center[1]))
    values, vectors = np.linalg.eigh(xy.T @ xy / len(xy))
    projected = xy @ vectors
    low, high = np.percentile(projected, [0.2, 99.8], axis=0)
    extent = high - low + 1
    adjusted = center + vectors @ ((high + low) / 2)
    major = vectors[:, 1]
    return {"center": adjusted.tolist(), "width": float(extent[0]), "height": float(extent[1]), "angle": math.degrees(math.atan2(major[1], major[0])) - 90, "trimmed_projection_percentiles": [0.2, 99.8], "source_component_pixels": len(x)}


def semantic_tones(rgb: np.ndarray, region: np.ndarray, colors: int, deadline: Deadline) -> tuple[np.ndarray, np.ndarray]:
    weight = region.astype(np.float32)
    denominator = ndimage.gaussian_filter(weight, 1.45)
    numerator = ndimage.gaussian_filter(rgb.astype(np.float32) * weight[:, :, None], (1.45, 1.45, 0))
    smooth = np.clip(numerator / np.maximum(denominator[:, :, None], 1e-5), 0, 255)
    samples = smooth[region].astype(np.uint8)
    result = Image.fromarray(samples[np.newaxis, :, :]).quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    palette = np.asarray(result.getpalette(), dtype=np.uint8).reshape(-1, 3)[:colors]
    # Reassign by actual nearest RGB, within this semantic family only.
    assignments = np.empty(len(samples), dtype=np.int16)
    for start in range(0, len(samples), 100000):
        deadline.check()
        chunk = samples[start:start + 100000].astype(np.float32)
        distances = np.sum((chunk[:, None, :] - palette[None, :, :].astype(np.float32)) ** 2, axis=2)
        assignments[start:start + len(chunk)] = np.argmin(distances, axis=1)
    labels = np.full(region.shape, -1, dtype=np.int16)
    labels[region] = assignments
    return labels, palette


def run_semantic_study(args: argparse.Namespace) -> None:
    """Case-specific reconstruction: analytic face/eyes/blush, traced major hair tones."""
    deadline = Deadline(args.max_seconds)
    source = Path(args.input)
    destination = Path(args.output)
    report_path = destination.with_suffix(".json")
    if destination.exists() or report_path.exists():
        raise FileExistsError("Semantic output already exists")
    rgba = np.asarray(Image.open(source).convert("RGBA"))
    rgb, alpha = rgba[:, :, :3], rgba[:, :, 3]
    h, w = alpha.shape
    foreground, _ = keep_components(alpha >= 128, 8)
    red, green, blue = [rgb[:, :, i].astype(np.float32) for i in range(3)]
    warm = foreground & (red > 185) & (green > 160) & (blue > 130) & (red >= green - 8)
    warm[:int(h * 0.42)] = False
    face_raw = ndimage.binary_fill_holes(largest_component(warm)) & foreground
    face = regularize_region(face_raw, 0.95, 100) & foreground
    eyes, eye_report = infer_eyes(rgb, foreground, deadline)
    if len(eyes) != 2:
        raise ValueError("This semantic study needs two inspected eye components; manual reconstruction required")
    face |= eyes[0]["mask"] | eyes[1]["mask"]
    mask_map = np.full((h, w), -1, dtype=np.int16)
    mask_map[face] = 0
    available = foreground & ~face
    halo = available & (green > red * 1.08) & (blue > red * 1.04) & (green > 75)
    coral = available & (red > green + 26) & (red > blue + 12) & (red > 130)
    hair = available & ~halo & ~coral & (rgb.max(axis=2) < 180)
    mask_map[hair], mask_map[coral], mask_map[halo] = 1, 2, 3
    unknown = foreground & (mask_map < 0)
    if unknown.any():
        nearest = ndimage.distance_transform_edt(mask_map < 0, return_distances=False, return_indices=True)
        mask_map[unknown] = mask_map[nearest[0][unknown], nearest[1][unknown]]
    definitions = [("hair", 1, 4, 180), ("coral", 2, 5, 140), ("halo", 3, 4, 110)]
    root = ET.Element(tag("svg"), {"viewBox": f"0 0 {w} {h}", "width": str(w), "height": str(h)})
    defs = ET.SubElement(root, tag("defs"))
    alpha_d, alpha_stats = mask_path(foreground, 0.6, 0.85, deadline)
    outer_clip = ET.SubElement(defs, tag("clipPath"), {"id": "alpha-silhouette", "clipPathUnits": "userSpaceOnUse"})
    ET.SubElement(outer_clip, tag("path"), {"d": alpha_d, "clip-rule": "evenodd", "fill-rule": "evenodd"})
    opacity = float(np.median(alpha[ndimage.binary_erosion(foreground, iterations=3)])) / 255
    artwork = ET.SubElement(root, tag("g"), {"id": "artwork", "clip-path": "url(#alpha-silhouette)", "opacity": f"{opacity:.8f}"})
    ET.SubElement(artwork, tag("path"), {"id": "coverage-underpaint", "d": alpha_d, "fill": "#4a4652", "fill-rule": "evenodd"})
    skin = face & (green > 225) & ((red - green) < 30)
    skin_samples = rgb[skin].astype(np.float32)
    skin_median = np.median(skin_samples, axis=0)
    light_color = skin_median * 0.6 + np.percentile(skin_samples, 90, axis=0) * 0.4
    edge_color = skin_median * 0.6 + np.percentile(skin_samples, 25, axis=0) * 0.4
    luminance = rgb.astype(np.float32).mean(axis=2)
    bright = skin & (luminance >= np.percentile(luminance[skin], 90))
    cy, cx = np.mean(np.nonzero(bright), axis=1)
    gradient = ET.SubElement(defs, tag("radialGradient"), {"id": "face-tone", "gradientUnits": "userSpaceOnUse", "cx": f"{cx:.2f}", "cy": f"{cy:.2f}", "r": f"{min(w, h) * 0.63:.2f}"})
    ET.SubElement(gradient, tag("stop"), {"offset": "0", "stop-color": hex_color(light_color)})
    ET.SubElement(gradient, tag("stop"), {"offset": "1", "stop-color": hex_color(edge_color)})
    face_d, face_stats = mask_path(face, 0.9, 1.8, deadline)
    face_group = ET.SubElement(artwork, tag("g"), {"id": "face"})
    ET.SubElement(face_group, tag("path"), {"id": "face-visible-region", "d": face_d, "fill": "url(#face-tone)", "fill-rule": "evenodd"})
    layers_report = []
    for name, code, colors, minimum in definitions:
        deadline.check()
        raw_region = mask_map == code
        region = regularize_region(raw_region, 0.8, 20) & foreground & ~face
        region_d, region_stats = mask_path(region, 0.9, 1.7, deadline)
        clip = ET.SubElement(defs, tag("clipPath"), {"id": name + "-boundary", "clipPathUnits": "userSpaceOnUse"})
        ET.SubElement(clip, tag("path"), {"d": region_d, "clip-rule": "evenodd", "fill-rule": "evenodd"})
        group = ET.SubElement(artwork, tag("g"), {"id": name, "clip-path": "url(#" + name + "-boundary)"})
        labels, palette = semantic_tones(rgb, region, colors, deadline)
        counts = np.bincount(labels[region], minlength=colors)
        base = int(np.argmax(counts))
        ET.SubElement(group, tag("path"), {"id": name + "-base", "d": region_d, "fill": hex_color(palette[base]), "fill-rule": "evenodd"})
        tones = []
        for index in sorted(range(colors), key=lambda index: int(counts[index]), reverse=True):
            if index == base:
                continue
            raw_tone = labels == index
            tone = regularize_region(raw_tone, 1.8, minimum) & region
            if not tone.any():
                continue
            d, stats = mask_path(tone, 1.1, 2.2, deadline)
            ET.SubElement(group, tag("path"), {"id": name + "-tone-" + str(index), "d": d, "fill": hex_color(palette[index]), "fill-rule": "evenodd"})
            tones.append({"index": index, "fill": hex_color(palette[index]), "raw_pixels": int(raw_tone.sum()), "retained_pixels": int(tone.sum()), **stats})
        layers_report.append({"name": name, "raw_pixels": int(raw_region.sum()), "region_pixels": int(region.sum()), "palette_size": colors, "small_region_threshold": minimum, "base_fill": hex_color(palette[base]), "region_contour": region_stats, "tones": tones})
    cheek_group = ET.SubElement(artwork, tag("g"), {"id": "cheeks"})
    cheek_records = []
    cheek_windows = [(0.065, 0.68, 0.215, 0.8), (0.51, 0.855, 0.655, 0.96)]
    for name, normalized in zip(("cheek-left", "cheek-right"), cheek_windows):
        x0, y0, x1, y1 = [round(normalized[i] * (w if i % 2 == 0 else h)) for i in range(4)]
        region = np.zeros((h, w), dtype=bool)
        region[y0:y1, x0:x1] = True
        blush = region & face & (red > 230) & (green < 231) & (blue < 228) & (red - green > 22) & (red - blue > 22)
        blush = largest_component(blush)
        fitted = fitted_ellipse(blush)
        x, y = fitted["center"]
        color = hex_color(np.median(rgb[blush], axis=0))
        ET.SubElement(cheek_group, tag("ellipse"), {"id": name, "cx": f"{x:.3f}", "cy": f"{y:.3f}", "rx": f"{fitted['rx']:.3f}", "ry": f"{fitted['ry']:.3f}", "transform": f"rotate({fitted['angle']:.4f} {x:.3f} {y:.3f})", "fill": color})
        cheek_records.append({"id": name, "source_roi": [x0, y0, x1, y1], "color": color, **fitted})
    eye_group = ET.SubElement(artwork, tag("g"), {"id": "eyes"})
    pooled = eyes[0]["mask"] | eyes[1]["mask"]
    eye_color = hex_color(np.median(rgb[pooled], axis=0))
    eye_records = []
    for eye in eyes:
        fitted = fitted_capsule(eye["mask"])
        x, y = fitted["center"]
        width, height = fitted["width"], fitted["height"]
        ET.SubElement(eye_group, tag("rect"), {"id": eye["id"], "x": f"{x - width / 2:.3f}", "y": f"{y - height / 2:.3f}", "width": f"{width:.3f}", "height": f"{height:.3f}", "rx": f"{width / 2:.3f}", "ry": f"{width / 2:.3f}", "transform": f"rotate({fitted['angle']:.4f} {x:.3f} {y:.3f})", "fill": eye_color})
        eye_records.append({"id": eye["id"], "fill": eye_color, **fitted})
    data = ET.tostring(root, encoding="utf-8", xml_declaration=True) + b"\n"
    ET.fromstring(data)
    if b"<image" in data or b"base64" in data or b"href=" in data or b"<text" in data:
        raise ValueError("Unexpected non-vector content")
    preview = np.zeros_like(rgba)
    debug_colors = np.array([[255, 229, 194], [91, 89, 111], [245, 102, 147], [50, 201, 182]], dtype=np.uint8)
    preview[foreground, :3] = debug_colors[mask_map[foreground]]
    preview[foreground, 3] = 255
    destination.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(preview).save(destination.with_name(destination.stem + "-source-regions.png"))
    report = {"schema": "aikon.semantic-vector-study.v3", "source": str(source), "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "svg_sha256": hashlib.sha256(data).hexdigest(), "case_scope": "Illustration diagnostic PNG only; not a general-purpose semantic segmenter", "method": "Region reconstruction with analytic face gradient, PCA-fitted independent capsules and blush ellipses; class-local limited-color masks for major hair/coral/halo planes.", "source_regions": {"face_pixels": int(face.sum()), "unknown_pixels_reassigned": int(unknown.sum()), "rule": "Largest lower warm/light region filled across eye holes; remaining pixels classified by source RGB color families then spatially completed."}, "face": {"path": face_stats, "gradient": {"light": hex_color(light_color), "edge": hex_color(edge_color), "center": [float(cx), float(cy)], "radius": min(w, h) * 0.63}, "note": "Single visible face-region path replaces quantized skin blotches; no round-head template imposed."}, "eyes": eye_records, "cheeks": cheek_records, "layers": layers_report, "alpha": {"threshold": 128, "outer_contour": alpha_stats, "group_opacity": opacity, "raster_fidelity": "pending_root_render"}, "path_count": sum(element.tag == tag("path") for element in root.iter()), "basic_shape_count": 4, "svg_bytes": len(data), "runtime_seconds": round(time.monotonic() - deadline.started, 3), "validation": {"xml_vector_structure": "passed", "semantic_segmentation": "heuristic_requires_visual_review", "rendered_pixel_error": "not_run", "artistic_acceptance": "not_claimed", "user_acceptance": "pending"}, "manual_rebuild_limits": ["Face color/gradient is a deliberate smooth approximation, not a pixel-exact skin reconstruction.", "Cheek windows are case-specific; automatic detection is not claimed for arbitrary images.", "Hair/coral/halo masks are color-family regions. Turquoise ties and the halo share a group, and dark outlines may be grouped with hair.", "PCA capsule fitting preserves separate eye IDs but does not guarantee exact agreement with non-capsule source contours.", "Remaining long-range shading and individual overlapping hair locks may still need manual path redesign after viewing."], "no_new_generation_model": True}
    with destination.open("xb") as stream:
        stream.write(data)
    with report_path.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(destination), "metadata": str(report_path), "paths": report["path_count"], "bytes": len(data), "seconds": report["runtime_seconds"], "visual": "unverified"}, ensure_ascii=False))


def run(args: argparse.Namespace) -> None:
    deadline = Deadline(args.max_seconds)
    source = Path(args.input)
    destination = Path(args.output)
    metadata_path = destination.with_suffix(".json")
    if destination.exists() or metadata_path.exists():
        raise FileExistsError("Refusing to overwrite an existing SVG or parameter log")
    raw = source.read_bytes()
    image = Image.open(source).convert("RGBA")
    rgba = np.asarray(image)
    rgb, alpha = rgba[:, :, :3], rgba[:, :, 3]
    original_foreground = alpha >= args.alpha_threshold
    foreground, alpha_removed = keep_components(original_foreground, args.alpha_min_area)
    if not foreground.any():
        raise ValueError("No foreground at configured alpha threshold")
    eyes, eye_report = infer_eyes(rgb, foreground, deadline)
    labels, palette, quantization = quantize(rgb, alpha, foreground, args.colors, args.rgb_blur, args.min_area, args.mode_filter, deadline)
    eye_mask = np.zeros(foreground.shape, dtype=bool)
    for eye in eyes:
        eye_mask |= eye["mask"]
    labels[eye_mask] = -1
    h, w = foreground.shape
    root = ET.Element(tag("svg"), {"viewBox": f"0 0 {w} {h}", "width": str(w), "height": str(h)})
    defs = ET.SubElement(root, tag("defs"))
    clip = ET.SubElement(defs, tag("clipPath"), {"id": "alpha-silhouette", "clipPathUnits": "userSpaceOnUse"})
    alpha_d, alpha_stats = mask_path(foreground, min(args.tolerance, 0.55), min(args.smooth, 0.55), deadline)
    ET.SubElement(clip, tag("path"), {"d": alpha_d, "fill-rule": "evenodd", "clip-rule": "evenodd"})
    interior = ndimage.binary_erosion(foreground, iterations=3)
    foreground_alpha_median = float(np.median(alpha[interior if interior.any() else foreground]))
    artwork = ET.SubElement(root, tag("g"), {"id": "artwork", "clip-path": "url(#alpha-silhouette)", "opacity": f"{foreground_alpha_median / 255:.8f}"})
    valid = labels[labels >= 0]
    most_common = int(np.argmax(np.bincount(valid, minlength=args.colors)))
    ET.SubElement(artwork, tag("path"), {"id": "coverage-underpaint", "d": alpha_d, "fill-rule": "evenodd", "fill": hex_color(palette[most_common])})
    groups = {name: ET.SubElement(artwork, tag("g"), {"id": name}) for name in ("face", "hair", "coral", "halo", "other")}
    color_report = []
    for index in sorted(np.unique(valid), key=lambda i: int(np.count_nonzero(labels == i)), reverse=True):
        deadline.check()
        mask = labels == index
        d, statistics = mask_path(mask, args.tolerance, args.smooth, deadline)
        color = palette[index]
        group = semantic_group(color)
        identifier = f"palette-{int(index):02d}"
        attrs = {"id": identifier, "d": d, "fill": hex_color(color), "fill-rule": "evenodd"}
        if args.stroke_width:
            attrs.update({"stroke": hex_color(color), "stroke-width": str(args.stroke_width), "stroke-linejoin": "round"})
        ET.SubElement(groups[group], tag("path"), attrs)
        color_report.append({"id": identifier, "semantic_group": group, "fill": hex_color(color), "pixels": int(mask.sum()), **statistics})
    eye_group = ET.SubElement(artwork, tag("g"), {"id": "eyes"})
    for eye in eyes:
        deadline.check()
        d, statistics = mask_path(eye["mask"], min(0.35, args.tolerance), min(0.6, args.smooth), deadline)
        ET.SubElement(eye_group, tag("path"), {"id": eye["id"], "d": d, "fill": eye["fill"], "fill-rule": "evenodd"})
        eye_report.setdefault("vector_paths", []).append({"id": eye["id"], "fill": eye["fill"], **statistics})
    data = ET.tostring(root, encoding="utf-8", xml_declaration=True) + b"\n"
    parsed = ET.fromstring(data)
    allowed = {tag(name) for name in ("svg", "defs", "clipPath", "g", "path")}
    if any(element.tag not in allowed for element in parsed.iter()):
        raise ValueError("Unexpected non-vector SVG element")
    if b"base64" in data or b"href=" in data or b"<image" in data or b"<text" in data:
        raise ValueError("Unexpected external/embedded/text content")
    path_count = sum(element.tag == tag("path") for element in root.iter())
    report = {"schema": "aikon.vector-study.v1", "algorithm_version": VERSION, "input": str(source), "input_sha256": hashlib.sha256(raw).hexdigest(), "svg_sha256": hashlib.sha256(data).hexdigest(), "parameters": vars(args), "image_size": [w, h], "algorithm": ["alpha-weighted Gaussian RGB denoise", "Pillow RGB median-cut quantization without dithering", "small 4-connected color-region merge into nearest retained opaque palette region", "directed pixel-cell boundary loops with exact signed-area verification", "circular Gaussian contour smoothing and closed Ramer-Douglas-Peucker simplification", "corner-aware cubic interpolation", "vector alpha silhouette clip with even-odd holes"], "quantization": quantization, "alpha": {"threshold": args.alpha_threshold, "source_nonzero_pixels": int(np.count_nonzero(alpha)), "source_partial_alpha_pixels": int(np.count_nonzero((alpha > 0) & (alpha < 255))), "threshold_foreground_pixels": int(original_foreground.sum()), "retained_foreground_pixels": int(foreground.sum()), "removed_small_component_pixels": alpha_removed, "contour": alpha_stats, "raster_alpha_fidelity": "unverified_until_rerender"}, "palette_paths": color_report, "eye_detection": eye_report, "semantic_rule": {"face": "RGB high-light warm colors; includes blush and may include pale highlights elsewhere", "halo": "green/blue greater than red; also groups turquoise hair-tie accents", "coral": "red significantly greater than green/blue", "hair": "dark or mid near-neutral colors, excluding inferred eye masks", "other": "remaining palette colors", "limitation": "Color grouping is a heuristic, not automatic object segmentation. Each palette path can contain disconnected subpaths; moving a whole semantic group can affect unrelated equal-colored accents."}, "path_count": path_count, "curve_vertices": sum(item["curve_vertices"] for item in color_report) + alpha_stats["curve_vertices"] * 2 + sum(item["curve_vertices"] for item in eye_report.get("vector_paths", [])), "svg_bytes": len(data), "runtime_seconds": round(time.monotonic() - deadline.started, 3), "runtime": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__, "Pillow": PILLOW_VERSION, "thread_limits": 1}, "validation": {"xml_and_vector_only": "passed", "raw_contour_signed_area": "passed", "rendered_pixel_comparison": "not_run", "visual_acceptance": "not_run", "user_acceptance": "pending"}, "limitations": ["This is a raster-to-vector approximation of a diagnostic image, not an authoritative character reference or user-approved gold image.", "Palette count/contour tolerance are approximation levels, not Aikon short/full profiles.", "Partial edge alpha is reconstructed by vector antialiasing around a threshold silhouette; exact source alpha values are not encoded.", "Color quantization and small-region merging can remove fine strands or subtle shading; compare actual rerenders.", "Coverage underpaint and tiny same-color strokes limit seams, but can slightly change color-boundary pixels.", "No artistic, model-consistency, watermark-detection or semantic-editability guarantee."]}
    report["algorithm"].insert(2, "optional local palette-label mode filter before connected-region cleanup")
    report["alpha"]["source_interior_alpha_median"] = foreground_alpha_median
    report["alpha"]["artwork_group_opacity"] = foreground_alpha_median / 255
    report["limitations"][2] = "Partial edge alpha is reconstructed by vector antialiasing around a threshold silhouette; artwork opacity uses source interior median alpha, not a per-pixel alpha reconstruction."
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as stream:
        stream.write(data)
    with metadata_path.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(destination), "metadata": str(metadata_path), "paths": path_count, "vertices": report["curve_vertices"], "bytes": len(data), "seconds": report["runtime_seconds"], "eyes": eye_report["status"]}, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--colors", type=int, default=24)
    parser.add_argument("--min-area", type=int, default=24)
    parser.add_argument("--mode-filter", type=int, choices=(1, 3, 5), default=3)
    parser.add_argument("--alpha-threshold", type=int, default=128)
    parser.add_argument("--alpha-min-area", type=int, default=8)
    parser.add_argument("--rgb-blur", type=float, default=0.65)
    parser.add_argument("--tolerance", type=float, default=0.85)
    parser.add_argument("--smooth", type=float, default=0.8)
    parser.add_argument("--stroke-width", type=float, default=0.55)
    parser.add_argument("--max-seconds", type=float, default=50)
    parser.add_argument("--diagnose-log", help="Replay a prior parameter log and save pre-vectorization RGBA intermediates")
    parser.add_argument("--actual-render", help="Existing source-sized RGBA render for --diagnose-log")
    parser.add_argument("--semantic-study", action="store_true", help="Case-specific face/eyes/blush reconstruction with limited major color planes")
    args = parser.parse_args()
    if not 4 <= args.colors <= 128 or args.min_area < 1 or args.alpha_min_area < 1 or not 1 <= args.alpha_threshold <= 255:
        parser.error("Invalid color/area/alpha configuration")
    if not (0 < args.tolerance <= 3 and 0 <= args.smooth <= 2 and 0 < args.rgb_blur <= 2 and 0 <= args.stroke_width <= 2 and 0 < args.max_seconds <= 55):
        parser.error("Invalid tolerance/smoothing/stroke/time configuration")
    if bool(args.diagnose_log) != bool(args.actual_render):
        parser.error("--diagnose-log and --actual-render must be used together")
    if args.semantic_study and args.diagnose_log:
        parser.error("Choose diagnostic replay or semantic reconstruction")
    if args.diagnose_log:
        run_diagnostics(args)
    elif args.semantic_study:
        run_semantic_study(args)
    else:
        run(args)


if __name__ == "__main__":
    main()
