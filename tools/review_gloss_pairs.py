#!/usr/bin/env python3
"""Review paired SVG candidates with real pixels; never award aesthetic approval.

CLI example: python tools/review_gloss_pairs.py --pair-dir <round> --output <evidence>
Repeat --pair-dir for other subjects. Each round contains short.svg and full.svg.
The CLI worker has a 50-second process-tree deadline. Imported API callers must
provide their own deadline, as the repository's other rendering adapters do.
"""

import argparse
import copy
import hashlib
import io
import json
import math
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import render_svg as renderer
from tools.run_visual_e2e import run_bounded

NS = renderer.SVG_NS
DRAWABLES = {"path", "rect", "circle", "ellipse", "line", "polyline", "polygon"}
DEFINITION_TAGS = {"defs", "clipPath", "mask", "linearGradient", "radialGradient", "stop", "metadata", "title", "desc"}
GEOMETRY_ATTRIBUTES = {"d", "points", "x", "y", "x1", "x2", "y1", "y2", "cx", "cy", "r", "rx", "ry", "width", "height", "transform", "viewBox", "preserveAspectRatio", "fill-rule", "clip-rule", "stroke-width", "stroke-linecap", "stroke-linejoin", "stroke-miterlimit", "stroke-dasharray", "stroke-dashoffset", "vector-effect", "display", "visibility"}
NUMBER_PATTERN = re.compile(r"[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?")
SIZES = (1024, 128, 48, 24)
MAX_DRAWABLES = 300
MAX_GRADIENTS = 64
MAX_GEOMETRY_NUMBERS = 24000


def local(element):
    return element.tag.rsplit("}", 1)[-1]


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def properties(element):
    result = dict(element.attrib)
    for declaration in element.get("style", "").split(";"):
        key, separator, value = declaration.partition(":")
        if separator:
            result[key.strip().lower()] = value.strip()
    return result


def unit(value):
    value = value.strip()
    number = float(value[:-1]) / 100 if value.endswith("%") else float(value)
    if not math.isfinite(number) or not 0 <= number <= 1:
        raise ValueError("Gradient stop offset/opacity must be finite and between 0 and 1")
    return number


def _normalized(value):
    # Numeric spellings and whitespace alone do not constitute new geometry.
    return NUMBER_PATTERN.sub(lambda match: format(float(match.group()), ".12g"), re.sub(r"\s+", " ", value.strip())).replace(",", " ")


def geometry_signature(root):
    """Ignore IDs, color, gradient coordinates, and descriptive metadata.

    Referenced clipping geometry remains part of the signature. This catches
    recolor-only pairs; it is not a mathematical equivalence proof for every
    possible SVG path encoding. Actual thumbnail pixel differences supplement it.
    """
    ids = {element.get("id"): element for element in root.iter() if element.get("id")}

    def node(element, visiting=frozenset(), definition=False):
        tag = local(element)
        if not definition and tag in DEFINITION_TAGS:
            return None
        if tag in {"linearGradient", "radialGradient", "stop", "title", "desc", "metadata"}:
            return None
        props = properties(element)
        if props.get("display") == "none" or props.get("visibility") in {"hidden", "collapse"}:
            return None
        attrs = {key: _normalized(value) for key, value in props.items() if key in GEOMETRY_ATTRIBUTES}
        for key in ("clip-path", "mask"):
            value = props.get(key, "none")
            if value != "none":
                match = renderer.URL_PATTERN.fullmatch(value)
                if not match:
                    raise ValueError("Unsupported clipping reference")
                name = match.group(2)[1:]
                if name in visiting:
                    raise ValueError("Cyclic clipping geometry")
                attrs[key] = node(ids[name], visiting | {name}, True)
        # Whether a shape is filled/stroked affects geometry; its color does not.
        if tag in DRAWABLES:
            attrs["has_fill"] = props.get("fill", "inherit") != "none"
            attrs["has_stroke"] = props.get("stroke", "none") != "none"
        children = [child for item in element for child in [node(item, visiting, definition)] if child is not None]
        if tag not in DRAWABLES and not children:
            return None
        return [tag, attrs, children]

    data = json.dumps(node(root), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(data)


def analyze_svg(svg_text):
    root = renderer.validate_svg(svg_text)
    drawables = [element for element in root.iter() if local(element) in DRAWABLES]
    gradients = [element for element in root.iter() if local(element) in {"linearGradient", "radialGradient"}]
    if len(drawables) > MAX_DRAWABLES or len(gradients) > MAX_GRADIENTS:
        raise ValueError("Candidate exceeds the 300-drawable or 64-gradient budget")
    number_count = sum(len(NUMBER_PATTERN.findall(element.get("d", "") + " " + element.get("points", ""))) for element in drawables)
    if number_count > MAX_GEOMETRY_NUMBERS:
        raise ValueError("Candidate exceeds the 24000 path-coordinate budget")
    ids = {element.get("id"): element for element in root.iter() if element.get("id")}
    for name in ("eye-left", "eye-right"):
        if name not in ids or local(ids[name]) not in DRAWABLES:
            raise ValueError("Require one drawable primary capsule with id=" + name)

    def stops(element, visited=frozenset()):
        name = element.get("id")
        if name in visited:
            raise ValueError("Cyclic gradient inheritance")
        own = [item for item in element if local(item) == "stop"]
        inherited = element.get("href", element.get("{" + renderer.XLINK_NS + "}href", ""))
        if own:
            return own
        if inherited:
            parent = ids[inherited[1:]]
            if local(parent) not in {"linearGradient", "radialGradient"}:
                raise ValueError("Gradient inheritance must reference a gradient")
            return stops(parent, visited | {name})
        return []

    gradient_reports = []
    for gradient in gradients:
        effective = stops(gradient)
        if not 2 <= len(effective) <= 6:
            raise ValueError("Each effective gradient requires 2 to 6 stops")
        offsets = [unit(properties(stop).get("offset", "0")) for stop in effective]
        if offsets != sorted(offsets):
            raise ValueError("Gradient stops must be ordered")
        opacities = [unit(properties(stop).get("stop-opacity", "1")) for stop in effective]
        gradient_reports.append({"id": gradient.get("id"), "type": local(gradient), "stops": len(effective), "offsets": offsets, "has_translucent_stops": any(value < 1 for value in opacities)})
    return root, {"drawable_count_including_definitions": len(drawables), "gradient_count": len(gradients), "path_coordinate_count": number_count, "geometry_sha256": geometry_signature(root), "gradients": gradient_reports}


def rgba(png):
    import numpy as np
    from PIL import Image
    with Image.open(io.BytesIO(png)) as image:
        if image.size[0] > 4096 or image.size[1] > 4096:
            raise ValueError("PNG dimensions exceed the renderer budget")
        image.load()
        return np.asarray(image.convert("RGBA"))


def compare_cached_png(cache, actual):
    """Compare decoded pixels, not compressor choices or PNG metadata."""
    import numpy as np
    cache = Path(cache)
    if not cache.exists():
        return {"status": "not_present"}
    if cache.stat().st_size > 32_000_000:
        raise ValueError("Cached preview exceeds the 32 MB file budget")
    cached_bytes = cache.read_bytes()
    cached = rgba(cached_bytes)
    equal = cached.shape == actual.shape and np.array_equal(cached, actual)
    return {"status": "match" if equal else "mismatch", "file": str(cache), "png_sha256": sha256(cached_bytes), "rgba_sha256": sha256(cached.tobytes()), "mismatched_pixels": int(np.any(cached != actual, axis=2).sum()) if cached.shape == actual.shape else None}


def _eye_markup(root, eye_id, visible):
    """Create a depth matte: named eye white, subsequent surfaces black.

    Eye-specific overlays named <eye-id>-* remain part of that capsule. The
    expected matte removes clipping to expose clipped/cropped primary eyes.
    """
    result = copy.deepcopy(root)

    def visit(element, inside_defs=False):
        tag = local(element)
        inside_defs = inside_defs or tag in {"defs", "clipPath", "mask"}
        if inside_defs:
            return
        props = properties(element)
        element.attrib.pop("style", None)
        for key, value in props.items():
            if key != "style":
                element.set(key, value)
        if not visible:
            element.attrib.pop("clip-path", None)
            element.attrib.pop("mask", None)
        if tag in DRAWABLES:
            name = element.get("id", "")
            selected = name == eye_id or (visible and name.startswith(eye_id + "-"))
            if not visible and not selected:
                element.set("display", "none")
            else:
                if props.get("fill", "black") != "none":
                    element.set("fill", "#ffffff" if selected else "#000000")
                if props.get("stroke", "none") != "none":
                    element.set("stroke", "#ffffff" if selected else "#000000")
        for child in element:
            visit(child, inside_defs)

    visit(result)
    return ET.tostring(result, encoding="unicode")


def geometry_boundary_pixels(root, size=128):
    """Render visible shape boundaries with identical paint for both profiles.

    One normalized diagnostic stroke is added to each painted primitive. This
    does not rate the artwork; it prevents hidden shapes plus recoloring from
    being reported as a visible profile-geometry difference.
    """
    result = copy.deepcopy(root)
    viewbox = NUMBER_PATTERN.findall(result.get("viewBox", ""))
    width = float(viewbox[2]) if len(viewbox) == 4 else float(result.get("width", "1024"))

    def visit(element, inherited_fill="black", inherited_stroke="none"):
        if local(element) in DEFINITION_TAGS:
            return
        props = properties(element)
        element.attrib.pop("style", None)
        for key, value in props.items():
            if key != "style":
                element.set(key, value)
        fill = props.get("fill", inherited_fill)
        stroke = props.get("stroke", inherited_stroke)
        if local(element) in DRAWABLES and (fill != "none" or stroke != "none"):
            element.set("fill", "#ffffff" if fill != "none" else "none")
            element.set("stroke", "#000000")
            element.set("stroke-width", str(width / size))
            element.set("stroke-linejoin", "round")
            element.attrib.pop("stroke-dasharray", None)
            element.attrib.pop("stroke-dashoffset", None)
        for child in element:
            visit(child, fill, stroke)

    visit(result)
    return rgba(renderer.render_svg_text(ET.tostring(result, encoding="unicode"), size))


def inspect_pixels(root, pixels, size):
    import numpy as np
    from scipy import ndimage as ndi
    alpha = pixels[:, :, 3]
    occupied = alpha > 0
    # A square neighborhood excludes diagonal AA as well as axis-aligned AA.
    # The two-device-pixel floor matters even for the small test renderer sizes.
    erosion = max(2, round(size * 3 / 1024))
    # Unknown pixels outside the viewport are not evidence of material. Padding
    # with occupied=True incorrectly calls a normal silhouette ending at the
    # bottom crop an interior defect. Require a completely observed neighborhood.
    interior = ndi.binary_erosion(occupied, structure=np.ones((3, 3), bool), iterations=erosion, border_value=0)
    viewport_band = np.ones_like(occupied)
    viewport_band[erosion:-erosion, erosion:-erosion] = False
    boundary_candidates = viewport_band & occupied & (alpha < 254)
    defects = []
    if not occupied.any():
        defects.append("empty_render")
    if not (alpha == 0).any():
        defects.append("no_transparent_canvas")
    translucent = interior & (alpha < 254)
    if int(translucent.sum()):
        defects.append("translucent_material_interior")
    alpha_report = {"transparent_pixels": int((alpha == 0).sum()), "occupied_pixels": int(occupied.sum()), "opaque_pixels": int((alpha == 255).sum()), "interior_pixels": int(interior.sum()), "interior_alpha_below_254": int((interior & (alpha < 254)).sum()), "erosion_pixels": erosion, "erosion_neighborhood": "square"}
    ys, xs = np.where(translucent)
    alpha_report["defect_sample_xy_alpha"] = [[int(x), int(y), int(alpha[y, x])] for x, y in list(zip(xs, ys))[:32]]
    alpha_report["defect_bbox_xyxy"] = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1] if len(xs) else None
    boundary_ys, boundary_xs = np.where(boundary_candidates)
    alpha_report["viewport_boundary"] = {"status": "not_classified_as_material_interior", "band_width_pixels": erosion, "partial_alpha_candidates": int(boundary_candidates.sum()), "sample_xy_alpha": [[int(x), int(y), int(alpha[y, x])] for x, y in list(zip(boundary_xs, boundary_ys))[:32]], "meaning": "Incomplete viewport neighborhood; may be legitimate silhouette AA or a seam. Inspect an expanded viewport or review visually; no interior-pass claim for these pixels."}
    eyes = {}
    eye_masks = []
    for name in ("eye-left", "eye-right"):
        expected = rgba(renderer.render_svg_text(_eye_markup(root, name, False), size))
        matte = rgba(renderer.render_svg_text(_eye_markup(root, name, True), size))
        ideal = expected[:, :, 3] >= 250
        eye_masks.append(ideal)
        visible = ideal & (matte[:, :, :3].min(axis=2) >= 245) & (matte[:, :, 3] >= 250)
        area = int(ideal.sum())
        visible_count = int(visible.sum())
        ratio = visible_count / area if area else 0.0
        touches = bool(ideal[0].any() or ideal[-1].any() or ideal[:, 0].any() or ideal[:, -1].any())
        components = int(ndi.label(ideal)[1])
        eyes[name] = {"expected_opaque_pixels": area, "visible_pixels": visible_count, "visible_fraction": ratio, "touches_canvas_edge": touches, "components": components, "method": "actual rendered depth matte; declared eye-specific overlays included"}
        if area < 16 or ratio < .98 or touches or components != 1:
            defects.append(name + "_not_fully_visible")
    if (eye_masks[0] & eye_masks[1]).any():
        defects.append("primary_eyes_overlap")
    # No pass/fail threshold: final composited edges and legal gloss contribute.
    luminance = pixels[:, :, :3].astype(float) @ np.array([.2126, .7152, .0722])
    highpass = luminance - ndi.gaussian_filter(luminance, 1)
    texture = {"status": "advisory_only", "luminance_highpass_rms": float(np.sqrt(np.mean(highpass[interior] ** 2))) if interior.any() else None, "sigma_pixels": 1, "scope": "opaque silhouette interior; contains legal internal edges/gloss; not a noise verdict or art score"}
    return {"alpha": alpha_report, "eyes": eyes, "texture": texture, "issues": defects}


def review_pair(pair_dir, output, sizes=SIZES):
    import numpy as np
    pair_dir, output = Path(pair_dir), Path(output)
    output.mkdir(parents=True, exist_ok=True)
    result = {"pair_dir": str(pair_dir), "status": "fail", "profiles": {}, "issues": [], "visual_review": "not_assessed", "user_acceptance": "not_claimed"}
    images = {}
    boundaries = {}
    for profile in ("short", "full"):
        record = {"status": "fail", "issues": [], "renders": []}
        result["profiles"][profile] = record
        try:
            source = pair_dir / (profile + ".svg")
            with source.open("rb") as stream:
                data = stream.read(renderer.MAX_SVG_BYTES + 1)
            if len(data) > renderer.MAX_SVG_BYTES:
                raise ValueError("SVG exceeds the 2 MB validation budget")
            record.update({"source": str(source), "svg_sha256": sha256(data)})
            root, structure = analyze_svg(data.decode("utf-8-sig"))
            record["structure"] = structure
            boundaries[profile] = geometry_boundary_pixels(root, 128)
            record["visible_geometry_boundary_rgba_sha256"] = sha256(boundaries[profile].tobytes())
            rendered = {}
            for size in sizes:
                png = renderer.render_svg_text(data.decode("utf-8-sig"), size)
                pixels = rgba(png)
                if pixels.shape[:2] != (size, size):
                    raise ValueError("Icon canvas must render square")
                target = output / (profile + "-" + str(size) + ".png")
                target.write_bytes(png)
                cache = compare_cached_png(pair_dir / target.name, pixels)
                if cache["status"] == "mismatch":
                    record["issues"].append("cached_png_pixel_mismatch_at_" + str(size))
                record["renders"].append({"size": size, "file": str(target), "png_sha256": sha256(png), "rgba_sha256": sha256(pixels.tobytes()), "cached_preview": cache})
                rendered[size] = pixels
            largest = max(sizes)
            canonical = rgba(renderer.render_svg_text(ET.tostring(root, encoding="unicode"), largest))
            canonical_equal = np.array_equal(canonical, rendered[largest])
            record["canonical_rerender_pixels_equal"] = canonical_equal
            if not canonical_equal:
                record["issues"].append("canonical_rerender_mismatch")
            record["pixels"] = inspect_pixels(root, rendered[largest], largest)
            record["issues"].extend(record["pixels"]["issues"])
            images[profile] = rendered
            record["status"] = "pass" if not record["issues"] else "fail"
        except (ValueError, OSError, RuntimeError, ET.ParseError) as error:
            record["issues"].append(str(error))
    if len(images) == 2:
        left, right = result["profiles"]["short"], result["profiles"]["full"]
        if left["svg_sha256"] == right["svg_sha256"]:
            result["issues"].append("exact_duplicate_svg")
        if left["structure"]["geometry_sha256"] == right["structure"]["geometry_sha256"]:
            result["issues"].append("same_geometry_recolor_only")
        boundary_changed = int(np.any(boundaries["short"] != boundaries["full"], axis=2).sum())
        result["geometry_boundary_difference"] = {"size": 128, "changed_pixels": boundary_changed, "meaning": "visible diagnostic geometry contours, not artistic improvement"}
        if boundary_changed == 0:
            result["issues"].append("no_visible_geometry_difference_at_128")
        differences = []
        for size in sizes:
            a, b = images["short"][size], images["full"][size]
            alpha_a, alpha_b = a[:, :, 3] >= 128, b[:, :, 3] >= 128
            union = int((alpha_a | alpha_b).sum())
            changed = int(np.any(a != b, axis=2).sum())
            # Premultiplied RGB avoids invisible RGB affecting apparent delta.
            pa = a[:, :, :3].astype(float) * a[:, :, 3:4] / 255
            pb = b[:, :, :3].astype(float) * b[:, :, 3:4] / 255
            differences.append({"size": size, "changed_rgba_pixels": changed, "changed_fraction": changed / (size * size), "alpha_iou": int((alpha_a & alpha_b).sum()) / union if union else None, "premultiplied_rgb_mean_absolute_difference": float(np.mean(np.abs(pa - pb))), "meaning": "difference magnitude, not similarity target or aesthetic score"})
            if changed == 0:
                result["issues"].append("identical_render_at_" + str(size))
        result["differences"] = differences
    result["status"] = "pass" if not result["issues"] and all(value["status"] == "pass" for value in result["profiles"].values()) else "fail"
    return result


def review_pairs(pair_dirs, output, sizes=SIZES):
    pair_dirs = [Path(path).resolve() for path in pair_dirs]
    if not pair_dirs or len(pair_dirs) > 3 or len(set(pair_dirs)) != len(pair_dirs):
        raise ValueError("Provide one to three distinct pair directories")
    if not sizes or len(sizes) > 4 or len(set(sizes)) != len(sizes) or any(isinstance(size, bool) or not isinstance(size, int) or not 24 <= size <= 1024 for size in sizes):
        raise ValueError("Provide up to four distinct integer review sizes from 24 to 1024")
    output = Path(output).resolve()
    if output in pair_dirs:
        raise ValueError("Evidence output must differ from source pair directory")
    output.mkdir(parents=True, exist_ok=True)
    pairs = [review_pair(directory, output / (str(index + 1).zfill(2) + "-" + directory.parent.name + "-" + directory.name), tuple(sizes)) for index, directory in enumerate(pair_dirs)]
    report = {"schema": "aikon.gloss-pairs.v1", "status": "pass" if all(pair["status"] == "pass" for pair in pairs) else "fail", "backend": renderer.backend_info(), "sizes": list(sizes), "pairs": pairs, "visual_review": "not_assessed", "user_acceptance": "not_claimed", "scope": "Static vector budgets, actual alpha/eye-depth checks, source-to-PNG provenance and pair differences. Gradients/gloss are legal. Existing paint-v1 thresholds are unchanged. No naturalness, identity, or cross-model quality claim."}
    (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return report


def evidence_line(report):
    return {"schema": report["schema"], "status": report["status"], "backend": report["backend"], "pairs": [{"pair_dir": pair["pair_dir"], "status": pair["status"], "issues": pair["issues"], "profiles": {name: {key: profile.get(key) for key in ("status", "svg_sha256", "issues", "renders")} for name, profile in pair["profiles"].items()}} for pair in report["pairs"]], "visual_review": "not_assessed", "user_acceptance": "not_claimed"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pair-dir", action="append", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if not args.worker:
        command = [sys.executable, "-B", str(Path(__file__).resolve()), "--worker", "--output", str(args.output)]
        for directory in args.pair_dir:
            command.extend(["--pair-dir", str(directory)])
        try:
            return run_bounded(command, timeout=50)
        except Exception as error:
            print(json.dumps({"status": "fail", "error": type(error).__name__ + ": " + str(error)}), file=sys.stderr)
            return 2
    try:
        report = review_pairs(args.pair_dir, args.output)
        print("AIKON_GLOSS_EVIDENCE " + json.dumps(evidence_line(report), ensure_ascii=True, separators=(",", ":"), allow_nan=False))
        return 0 if report["status"] == "pass" else 1
    except (ValueError, OSError, RuntimeError) as error:
        print(json.dumps({"status": "fail", "error": str(error)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
