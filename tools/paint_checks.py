"""Offline checks against complete vector-derived material masks.

Mechanical anchor rules detect a limited defect class, not plausible lighting.
No handpicked safe region is used to certify the generated fixtures.
"""
import hashlib
import io
import json
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

try:
    from . import render_svg
except ImportError:
    import render_svg

NS = "http://www.w3.org/2000/svg"
SHAPES = {"path", "rect", "ellipse", "circle", "polygon", "polyline", "line"}
GEOMETRY = {"d", "x", "y", "width", "height", "rx", "ry", "r", "cx", "cy", "points", "transform", "fill-rule", "clip-rule"}
LOCAL_URL = re.compile(r"url\(\s*(['\"]?)#([A-Za-z_][A-Za-z0-9_.:-]*)\1\s*\)\Z", re.I)


def local(node):
    return node.tag.rsplit("}", 1)[-1]


def drawing_nodes(root):
    result = []
    def walk(node, definition=False):
        definition = definition or local(node) == "defs"
        if local(node) in SHAPES and not definition:
            result.append(node)
        for child in node:
            walk(child, definition)
    walk(root)
    return result


def geometry_manifest(source, identifiers, ownership_wrappers=None):
    root = ET.fromstring(source)
    parents = {child: parent for parent in root.iter() for child in parent}
    all_ids = {node.get("id"): node for node in root.iter() if node.get("id")}
    nodes = {node.get("id"): node for node in drawing_nodes(root)}
    records, clips, visiting = {}, {}, set()
    ownership_wrappers = ownership_wrappers or {}
    def record_clip(value):
        if value == "none":
            return
        match = LOCAL_URL.fullmatch(value)
        if not match:
            raise ValueError("Geometry clip must be a local reference or none")
        identifier = match.group(2)
        if identifier in visiting:
            raise ValueError("Cyclic geometry clip dependency")
        if identifier in clips:
            return
        node = all_ids.get(identifier)
        if node is None or local(node) != "clipPath":
            raise ValueError("Missing geometry clip definition")
        visiting.add(identifier)
        def outline(element):
            if element.get("clip-path"):
                record_clip(element.get("clip-path"))
            attrs = {key: value for key, value in element.attrib.items() if key in GEOMETRY | {"clip-path", "clipPathUnits", "viewBox", "preserveAspectRatio"}}
            return {"tag": local(element), "geometry": attrs, "children": [outline(child) for child in element]}
        clips[identifier] = outline(node)
        visiting.remove(identifier)
    for identifier in identifiers:
        node = nodes[identifier]
        chain, clip_chain, ancestor = [], [], node
        while ancestor is not None:
            if ancestor.get("transform"):
                chain.append(ancestor.get("transform"))
            clip = ancestor.get("clip-path")
            added_wrapper = ownership_wrappers.get(identifier)
            is_added_ownership = added_wrapper and ancestor.get("id") == added_wrapper[0] and clip == added_wrapper[1]
            if clip and not is_added_ownership:
                record_clip(clip)
                clip_chain.append({"tag": local(ancestor), "clip-path": clip, "transform": ancestor.get("transform")})
            ancestor = parents.get(ancestor)
        records[identifier] = {"tag": local(node), "geometry": {key: value for key, value in node.attrib.items() if key in GEOMETRY}, "transforms": chain, "clip_chain": clip_chain}
    return {"canvas": {key: root.get(key) for key in ("viewBox", "width", "height", "preserveAspectRatio")}, "layers": records, "clip_definitions": clips}


def check_geometry_lock(before, after, plan):
    identifiers = [layer["id"] for layer in plan["layers"]]
    # Only the compiler's new receiver wrapper is paint ownership. Existing
    # own/ancestor clips and their transitive geometry remain part of the lock.
    wrappers = {layer["id"]: ("paint-ownership-" + layer["id"], "url(#paint-receiver-" + layer["owner"] + ")") for layer in plan["layers"] if "owner" in layer}
    if geometry_manifest(before, identifiers) != geometry_manifest(after, identifiers, wrappers):
        raise ValueError("Selected geometry or coordinate system changed")


def check_compiled_structure(svg, plan):
    root = render_svg.validate_svg(svg.decode("utf-8") if isinstance(svg, bytes) else svg)
    all_ids = {node.get("id"): node for node in root.iter() if node.get("id")}
    def number(value):
        try:
            result = float(value)
        except (ValueError, TypeError, OverflowError) as error:
            raise ValueError("Compiled paint has a nonnumeric field") from error
        if not math.isfinite(result):
            raise ValueError("Compiled paint must use finite fields")
        return result
    for node in root.iter():
        if "style" in node.attrib:
            raise ValueError("Compiled paint must not be overridden by inline styles")
        if any(number(node.get(attribute, "1")) != 1. for attribute in ("opacity", "fill-opacity", "stroke-opacity")):
            raise ValueError("Compiled paint must be opaque at every ancestor")
        if node.get("stroke", "none") != "none":
            raise ValueError("Compiled paint contains an unplanned stroke")
        if node.get("color-interpolation", "sRGB") != "sRGB":
            raise ValueError("Compiled paint changes the sRGB interpolation contract")
    expected = {layer["id"]: layer for layer in plan["layers"]}
    nodes = drawing_nodes(root)
    actual = [node.get("id") for node in nodes]
    if set(actual) != set(expected) or len(actual) != len(expected):
        raise ValueError("Compiled SVG contains missing, duplicate or unplanned paint shapes")
    for node in nodes:
        layer = expected[node.get("id")]
        if layer["paint"]["type"] == "solid" and node.get("fill", "").lower() != layer["paint"]["color"].lower():
            raise ValueError("Compiled solid paint differs from its explicit plan")
        if layer["paint"]["type"] == "linear":
            match = LOCAL_URL.fullmatch(node.get("fill", ""))
            gradient = all_ids.get(match.group(2)) if match else None
            if gradient is None or local(gradient) != "linearGradient":
                raise ValueError("Compiled surface must reference its linear field")
            allowed_attributes = {"id", "gradientUnits", "x1", "y1", "x2", "y2", "spreadMethod", "color-interpolation"}
            if set(gradient.attrib) - allowed_attributes or gradient.get("gradientUnits") != "userSpaceOnUse" or gradient.get("spreadMethod", "pad") != "pad":
                raise ValueError("Compiled linear field changes units, transform or inheritance")
            actual_points = [number(gradient.get(key)) for key in ("x1", "y1", "x2", "y2")]
            expected_points = layer["paint"]["from"] + layer["paint"]["to"]
            if actual_points != expected_points:
                raise ValueError("Compiled linear field coordinates differ from plan")
            stops = list(gradient)
            if len(stops) != 2 or any(local(stop) != "stop" for stop in stops):
                raise ValueError("Compiled linear field requires exactly two stops")
            for offset, stop, color in zip((0., 1.), stops, layer["paint"]["colors"]):
                if set(stop.attrib) - {"offset", "stop-color", "stop-opacity"} or number(stop.get("offset")) != offset or stop.get("stop-color", "").lower() != color.lower() or number(stop.get("stop-opacity", "1")) != 1.:
                    raise ValueError("Compiled gradient stops differ from the opaque paint plan")
    return actual


def check_profile_pair(outputs):
    if set(outputs) != {"short", "full"}:
        raise ValueError("A round requires both short and full SVG outputs")
    if not all(isinstance(value, bytes) and value for value in outputs.values()):
        raise ValueError("Both profiles must contain SVG bytes")
    if outputs["short"] == outputs["full"]:
        raise ValueError("Short and full are identical bytes, not two distinct profile treatments")
    return {key: hashlib.sha256(value).hexdigest() for key, value in outputs.items()}


def check_reference_binding(root, binding_path):
    data = json.loads(Path(binding_path).read_text(encoding="utf-8"))
    binding = data.get("bindings", {}).get("deepseek", {})
    if binding.get("reference") != "ref/user-mode/r1.png" or not {"subject", "style"}.issubset(set(binding.get("roles", []))):
        raise ValueError("DeepSeek must bind r1 as both subject and style reference")
    source = Path(root) / binding["reference"]
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if binding.get("sha256") != digest:
        raise ValueError("DeepSeek r1 reference hash mismatch")
    return {"subject": "deepseek", "reference": binding["reference"], "sha256": digest, "roles": binding["roles"], "status": "matched", "legacy_whale_default": "not_used"}


def isolated_mask_svg(svg, target):
    root = ET.fromstring(svg)
    found = []
    def prune(node, definition=False):
        definition = definition or local(node) == "defs"
        for child in list(node):
            if not definition and local(child) in SHAPES:
                if child.get("id") != target:
                    node.remove(child)
                    continue
                child.set("fill", "#ffffff")
                for attribute in ("stroke", "stroke-width", "opacity", "fill-opacity", "stroke-opacity"):
                    child.attrib.pop(attribute, None)
                found.append(child)
            prune(child, definition)
    prune(root)
    if len(found) != 1:
        raise ValueError("A mask requires exactly one visible drawing target: " + target)
    return ET.tostring(root, encoding="unicode")


def raster_masks(svg, plan, size=1024, output=None):
    """Render every planned layer with all source definitions and transforms."""
    masks = {}
    if output:
        Path(output).mkdir(parents=True, exist_ok=True)
    for layer in plan["layers"]:
        identifier = layer["id"]
        png = render_svg.render_svg_text(isolated_mask_svg(svg, identifier), size)
        if output:
            (Path(output) / (identifier + ".png")).write_bytes(png)
        with Image.open(io.BytesIO(png)) as image:
            masks[identifier] = np.array(image.getchannel("A"), copy=True)
        if not (masks[identifier] >= 128).any():
            raise ValueError("Selected paint layer has no measurable rendered coverage: " + identifier)
    return masks


def ownership_checks(masks, plan, size=1024):
    """Check clipping and connection to the actual receiver outline.

    Significant component >=12px at 1024. Boundary distance <=2px at 1024;
    rescale these geometric units only for smaller independent unit fixtures.
    """
    reports, issues = [], []
    area_min = max(1, round(12 * (size / 1024) ** 2))
    distance_max = max(1., 2 * size / 1024)
    for layer in plan["layers"]:
        if layer["role"] not in {"occlusion-shadow", "blush"}:
            continue
        pixels, owner_alpha = masks[layer["id"]], masks[layer["owner"]]
        owner = owner_alpha >= 128
        component_mask = pixels >= 128
        boundary = owner & ~ndi.binary_erosion(owner, border_value=0)
        distances = ndi.distance_transform_edt(~boundary)
        leakage = component_mask & (owner_alpha == 0)
        failures = ["pixels_outside_receiver"] if leakage.any() else []
        components = []
        if layer["role"] == "occlusion-shadow":
            labels, count = ndi.label(component_mask)
            sizes = np.bincount(labels.ravel())
            for index in range(1, count + 1):
                area = int(sizes[index])
                if area < area_min:
                    continue
                component = labels == index
                distance = float(distances[component].min())
                anchored = distance <= distance_max
                components.append({"area_pixels": area, "min_distance_to_owner_boundary_px": distance, "anchored": anchored})
                if not anchored:
                    failures.append("floating_shadow_component")
            if not components:
                failures.append("no_significant_shadow_component")
        reports.append({"id": layer["id"], "role": layer["role"], "owner": layer["owner"], "outside_receiver_pixels": int(leakage.sum()), "components": components, "failures": sorted(set(failures)), "status": "fail" if failures else "no_rule_failure"})
        issues.extend({"layer": layer["id"], "code": failure} for failure in sorted(set(failures)))
    return {"size": size, "significant_area_min_px": area_min, "boundary_distance_max_px": distance_max, "layers": reports, "issues": issues, "status": "fail" if issues else "no_rule_failure", "naturalness": "not_automatically_assessed"}


def visible_material_contract(svg, masks, plan, rules):
    """Deduct real later-painted layers, never an attractive handpicked ROI."""
    order = [node.get("id") for node in drawing_nodes(ET.fromstring(svg))]
    layers = {layer["id"]: layer for layer in plan["layers"]}
    example = next(iter(masks.values()))
    covered = np.zeros_like(example, dtype=bool)
    visible, exclusions, regions = {}, [], []
    for identifier in reversed(order):
        layer = layers[identifier]
        raw = masks[identifier] >= 128
        if layer["role"] != "underpaint":
            material = raw & ~covered
            visible[identifier] = material
            later = order[order.index(identifier) + 1:]
            shadow_union = np.zeros_like(raw)
            for later_id in later:
                if layers[later_id]["role"] == "occlusion-shadow":
                    shadow_union |= masks[later_id] > 0
            exclusions.append({"id": identifier, "role": layer["role"], "raw_mask_pixels": int(raw.sum()), "visible_mask_pixels": int(material.sum()), "shadow_excluded_pixels": int((raw & shadow_union).sum()), "all_later_layer_excluded_pixels": int((raw & covered).sum()), "method": "all later drawable alpha support in actual SVG order"})
            if material.any():
                regions.append({"id": identifier, "mask_id": identifier, "expectation": "smooth_field" if layer["role"] == "surface" else "opaque_surface"})
        covered |= masks[identifier] > 0
    # Explicit geometry-derived support catches holes or low alpha even when
    # they would disappear from support inferred from the delivered image.
    silhouette = np.logical_or.reduce([value >= 128 for value in masks.values()])
    visible["whole-subject"] = silhouette
    regions.append({"id": "whole-subject", "mask_id": "whole-subject", "expectation": "opaque_surface"})
    return {"schema": "aikon.paint-fields.v1", "long_edge": int(example.shape[0]), "rules": rules, "threshold_provenance": "Frozen r1/source-short calibration; all visible vector material masks", "regions": regions}, visible, exclusions


def render_image(svg, size):
    png = render_svg.render_svg_text(svg.decode("utf-8") if isinstance(svg, bytes) else svg, size)
    image = Image.open(io.BytesIO(png))
    image.load()
    return image
