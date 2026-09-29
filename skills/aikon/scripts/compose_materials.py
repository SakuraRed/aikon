#!/usr/bin/env python3
"""Compile explicit analytic materials onto existing SVG shapes; stdlib only.

No reference fitting, rendering, networking, storage policy or visual approval.
The static SVG subset is owned by archive_svg.validate_svg, not this compiler.
"""

import argparse
import json
import math
import os
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

import archive_svg as archive


VERSION = "0.1.0"
NS = archive.SVG_NS
ET.register_namespace("", NS)
GEOMETRY = {"d", "x", "y", "x1", "y1", "x2", "y2", "width", "height",
            "rx", "ry", "r", "cx", "cy", "points", "transform", "fill-rule", "clip-rule"}


class MaterialError(ValueError):
    """The explicit material contract was not satisfied."""


def fields(value, required, optional, label):
    if not isinstance(value, dict) or required - value.keys() or value.keys() - required - optional:
        raise MaterialError(label + " has missing/unsupported fields")


def text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise MaterialError(label + " must be a nonempty string")


def number(value):
    try:
        valid = type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        valid = False
    if not valid:
        raise MaterialError("coordinates and paint parameters must be finite numbers")
    return value


def vector(value, length):
    if not isinstance(value, list) or len(value) != length:
        raise MaterialError("expected an array of " + str(length) + " finite numbers")
    return [number(item) for item in value]


def unit(value):
    if not 0 <= number(value) <= 1:
        raise MaterialError("opacity and offsets must be in 0..1")
    return value


def color(value):
    if not isinstance(value, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        raise MaterialError("material colors must be explicit #RRGGBB")


def simple(field, opaque):
    if not isinstance(field, dict):
        raise MaterialError("field must be an object")
    kind = field.get("kind")
    if kind == "solid":
        fields(field, {"kind", "color"}, {"opacity"}, "solid field")
        color(field["color"])
        if unit(field.get("opacity", 1)) != 1 and opaque:
            raise MaterialError("direct material and base must be opaque")
        return
    if kind == "linear":
        fields(field, {"kind", "from", "to", "stops"}, set(), "linear field")
        if vector(field["from"], 2) == vector(field["to"], 2):
            raise MaterialError("linear field requires a nonzero direction")
    elif kind == "radial":
        fields(field, {"kind", "center", "radii", "stops"}, set(), "radial field")
        vector(field["center"], 2)
        if min(vector(field["radii"], 2)) <= 0:
            raise MaterialError("radial radii must be positive")
    else:
        raise MaterialError("simple fields support only solid, linear and radial")
    stops = field["stops"]
    if not isinstance(stops, list) or not 2 <= len(stops) <= 5:
        raise MaterialError("gradient requires 2..5 stops")
    offsets = []
    for stop in stops:
        fields(stop, {"offset", "color"}, {"opacity"}, "stop")
        offsets.append(unit(stop["offset"]))
        color(stop["color"])
        if unit(stop.get("opacity", 1)) != 1 and opaque:
            raise MaterialError("direct material and base stops must be opaque")
    if offsets[0] != 0 or offsets[-1] != 1 or any(a >= b for a, b in zip(offsets, offsets[1:])):
        raise MaterialError("stop offsets must increase strictly from 0 to 1")


def parents_of(root):
    return {child: parent for parent in root.iter() for child in parent}


def inherited(element, name, parents, default):
    while element is not None:
        if name in element.attrib:
            return element.get(name)
        element = parents.get(element)
    return default


def transforms(element, parents):
    result = []
    while element is not None:
        if "transform" in element.attrib:
            result.append(element.get("transform"))
        element = parents.get(element)
    return result


def opaque_ancestors(element, parents):
    element = parents.get(element)
    while element is not None:
        value = element.get("opacity", "1")
        if archive.finite(value[:-1] if value.endswith("%") else value, "opacity") != (100 if value.endswith("%") else 1):
            raise MaterialError("target ancestors must have opacity=1; do not make the subject translucent")
        element = parents.get(element)


def validate_plan(plan, geometry, ids, parents, definitions):
    fields(plan, {"schema", "geometry_sha256", "profile", "materials"}, {"notes"}, "plan")
    if plan["schema"] != "aikon.material-plan.v1" or plan["geometry_sha256"] != archive.sha256(geometry):
        raise MaterialError("material plan does not match this geometry/schema")
    if plan["profile"] not in ("short", "full"):
        raise MaterialError("profile must be short or full")
    if "notes" in plan:
        text(plan["notes"], "notes")
    materials = plan["materials"]
    if not isinstance(materials, list) or not 1 <= len(materials) <= 256:
        raise MaterialError("materials must contain 1..256 explicit targets")
    selected = set()
    for item in materials:
        fields(item, {"target", "role", "reason", "field"}, {"owner", "support", "glaze_reasons"}, "material")
        key = item["target"]
        if (not isinstance(key, str) or key in selected or key not in ids
                or archive.tag_name(ids[key]) not in archive.SHAPES or ids[key] in definitions):
            raise MaterialError("target must be a unique existing rendered shape ID")
        selected.add(key)
        target = ids[key]
        if (archive.tag_name(target) == "line" or
                (inherited(target, "fill", parents, "black") == "none" and
                 inherited(target, "stroke", parents, "none") != "none")):
            raise MaterialError("material targets must be filled surfaces, not line/stroke-only artwork")
        text(item["role"], "role")
        text(item["reason"], "material reason")
        opaque_ancestors(target, parents)
        field = item["field"]
        if isinstance(field, dict) and field.get("kind") == "layered":
            fields(field, {"kind", "base", "glazes"}, set(), "layered field")
            simple(field["base"], opaque=True)
            glazes = field["glazes"]
            if not isinstance(glazes, list) or not 1 <= len(glazes) <= 2:
                raise MaterialError("layered field requires one or two broad glazes")
            reasons = item.get("glaze_reasons")
            if not isinstance(reasons, list) or len(reasons) != len(glazes):
                raise MaterialError("each glaze requires a caller-declared semantic reason")
            for glaze, reason in zip(glazes, reasons):
                simple(glaze, opaque=False)
                text(reason, "glaze reason")
            support = vector(item.get("support"), 4)
            if min(support[2:]) <= 0:
                raise MaterialError("support width and height must be positive")
            # Do not overflow when a renderer evaluates the declared rectangle.
            number(support[0] + support[2]); number(support[1] + support[3])
            fill_rule = inherited(target, "fill-rule", parents, "nonzero")
            if target.get("clip-rule", fill_rule) != fill_rule:
                raise MaterialError("layered target clip-rule conflicts with its filled silhouette")
        else:
            simple(field, opaque=True)
            if "support" in item or "glaze_reasons" in item:
                raise MaterialError("support/glaze_reasons only apply to layered fields")
        if "owner" in item:
            owner = item["owner"]
            if (not isinstance(owner, str) or owner not in ids or owner == key
                    or archive.tag_name(ids[owner]) not in archive.SHAPES or ids[owner] in definitions):
                raise MaterialError("owner must be a different existing rendered shape ID")
            if transforms(target, parents) != transforms(ids[owner], parents):
                raise MaterialError("owner and target must share the same complete transform chain")
            if inherited(ids[owner], "clip-path", parents, "none") != "none":
                raise MaterialError("owner must have an unclipped silhouette; author an explicit support shape")
    return materials


def geometry_records(original, root, attributes):
    parents = parents_of(root)
    order = [element for element in root.iter() if element in attributes]
    if order != original:
        raise MaterialError("original geometry order changed")
    return [{"tag": archive.tag_name(element), "id": element.get("id"),
             "geometry": {key: element.get(key) for key in attributes[element]},
             "transforms": transforms(element, parents),
             "fill_rule": inherited(element, "fill-rule", parents, "nonzero")}
            for element in original]


def emit_field(field, defs, fresh):
    if field["kind"] == "solid":
        return {"fill": field["color"], "fill-opacity": str(field.get("opacity", 1))}
    identifier = fresh("field")
    common = {"id": identifier, "gradientUnits": "userSpaceOnUse", "color-interpolation": "sRGB"}
    if field["kind"] == "linear":
        common.update(dict(zip(("x1", "y1", "x2", "y2"), map(str, field["from"] + field["to"]))))
        gradient = ET.SubElement(defs, "{" + NS + "}linearGradient", common)
    else:
        cx, cy = field["center"]; rx, ry = field["radii"]
        common.update({"cx": "0", "cy": "0", "r": "1",
                       "gradientTransform": f"translate({cx} {cy}) scale({rx} {ry})"})
        gradient = ET.SubElement(defs, "{" + NS + "}radialGradient", common)
    for stop in field["stops"]:
        ET.SubElement(gradient, "{" + NS + "}stop", {"offset": str(stop["offset"]),
                      "stop-color": stop["color"], "stop-opacity": str(stop.get("opacity", 1))})
    return {"fill": "url(#" + identifier + ")", "fill-opacity": "1"}


def compile_materials(geometry, plan):
    """Return (SVG bytes, report dict). Input bytes and plan are never mutated."""
    archive.validate_svg(geometry)
    root = ET.fromstring(geometry)
    ids = {element.get("id"): element for element in root.iter() if element.get("id")}
    parents = parents_of(root)
    definitions = {child for element in root.iter() if archive.tag_name(element) in {"defs", "clipPath"}
                   for child in element.iter()}
    materials = validate_plan(plan, geometry, ids, parents, definitions)
    original = [element for element in root.iter() if archive.tag_name(element) in archive.SHAPES]
    attributes = {element: set(element.attrib) & GEOMETRY for element in original}
    before = geometry_records(original, root, attributes)
    counter = 0

    def fresh(kind):
        nonlocal counter
        while True:
            counter += 1
            identifier = "aikon-material-" + kind + "-" + str(counter)
            if identifier not in ids:
                ids[identifier] = None
                return identifier

    # Snapshot owner outlines before any selected target is repainted or moved.
    owner_outlines = {}
    for item in materials:
        if "owner" in item:
            owner = ids[item["owner"]]
            attrs = {key: value for key, value in owner.attrib.items() if key in GEOMETRY}
            attrs["clip-rule"] = inherited(owner, "fill-rule", parents, "nonzero")
            owner_outlines[item["target"]] = (owner.tag, attrs)
    defs = ET.Element("{" + NS + "}defs")
    root.insert(0, defs)
    layer_reports = []
    for item in materials:
        target = ids[item["target"]]
        parent = parents[target]
        field = item["field"]
        layered = field["kind"] == "layered"
        wrapper = None
        if layered or "owner" in item:
            wrapper = ET.Element("{" + NS + "}g", {"id": fresh("surface")})
            position = list(parent).index(target)
            parent.remove(target)
            parent.insert(position, wrapper)
            # Keep tail placement outside the newly introduced wrapper.
            wrapper.tail, target.tail = target.tail, None
        if "owner" in item:
            owner_clip = fresh("owner")
            clip = ET.SubElement(defs, "{" + NS + "}clipPath", {"id": owner_clip, "clipPathUnits": "userSpaceOnUse"})
            tag, attrs = owner_outlines[item["target"]]
            ET.SubElement(clip, tag, attrs)
            wrapper.set("clip-path", "url(#" + owner_clip + ")")
        if not layered:
            target.attrib.update(emit_field(field, defs, fresh))
            target.set("opacity", "1"); target.set("stroke", "none")
            if wrapper is not None:
                wrapper.append(target)
        else:
            # The original editable shape IS the shared clip. Rectangles carry
            # analytic paint; the subject edge is never painted repeatedly.
            local_defs = ET.SubElement(wrapper, "{" + NS + "}defs")
            surface_clip = fresh("clip")
            clip = ET.SubElement(local_defs, "{" + NS + "}clipPath", {"id": surface_clip, "clipPathUnits": "userSpaceOnUse"})
            target.set("clip-rule", inherited(target, "fill-rule", parents, "nonzero"))
            target.set("fill", "#ffffff"); target.set("fill-opacity", "1")
            target.set("opacity", "1"); target.set("stroke", "none")
            clip.append(target)
            painted = ET.SubElement(wrapper, "{" + NS + "}g", {"clip-path": "url(#" + surface_clip + ")"})
            rectangle = dict(zip(("x", "y", "width", "height"), map(str, item["support"])))
            if target.get("transform"):
                rectangle["transform"] = target.get("transform")
            for index, layer in enumerate([field["base"], *field["glazes"]]):
                attrs = {**rectangle, **emit_field(layer, defs, fresh), "stroke": "none", "opacity": "1",
                         "data-material-layer": "base" if index == 0 else "glaze"}
                ET.SubElement(painted, "{" + NS + "}rect", attrs)
        layer_reports.append({"target": item["target"], "role": item["role"], "reason": item["reason"],
                              "owner": item.get("owner"), "field": field["kind"],
                              "support": item.get("support"), "glaze_reasons": item.get("glaze_reasons", [])})
    if before != geometry_records(original, root, attributes):
        raise MaterialError("painting changed original geometry or its transform chain")
    data = ET.tostring(root, encoding="utf-8", xml_declaration=True) + b"\n"
    archive.validate_svg(data)
    report = {"schema": "aikon.material-compile.v1", "compiler_version": VERSION, "profile": plan["profile"],
              "geometry_source_sha256": archive.sha256(geometry),
              "material_plan_sha256": archive.sha256(archive.json_bytes(plan)), "svg_sha256": archive.sha256(data),
              "original_geometry_sha256": archive.sha256(archive.json_bytes(before)),
              "original_shape_count": len(original), "materials": layer_reports,
              "checks": {"static_svg": "passed", "original_geometry_preserved": True,
                         "opaque_material_construction": "passed", "support_coverage": "unverified",
                         "raster_alpha": "unverified", "visual": "unverified"},
              "user_acceptance": "unassessed"}
    return data, report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("geometry", "plan", "output", "report"):
        parser.add_argument("--" + name, required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        outputs = (args.output.resolve(), args.report.resolve())
        inputs = (args.geometry.resolve(), args.plan.resolve())
        if len(set(outputs)) != 2 or any(path in inputs for path in outputs):
            raise MaterialError("inputs, SVG output and report must have separate paths")
        if any(path.exists() or path.is_symlink() for path in outputs):
            raise MaterialError("refusing to overwrite existing artifacts")
        data, report = compile_materials(archive.read_bytes(args.geometry), archive.parse_json(archive.read_bytes(args.plan)))
        # Parents must already exist. Directory/revision policy belongs to caller.
        created = []
        try:
            for path, content in ((args.output, data), (args.report, archive.json_bytes(report))):
                with path.open("xb") as stream:
                    try:
                        info = os.fstat(stream.fileno())
                    except OSError:
                        try:
                            # Query the same open descriptor, never a possibly
                            # replaced path, to establish rollback ownership.
                            info = os.stat(stream.fileno())
                        except OSError as fallback_error:
                            raise MaterialError("descriptor identity unavailable; created output left untouched: "
                                                + str(path)) from fallback_error
                        created.append((path, (info.st_dev, info.st_ino)))
                        raise  # Abort and roll back after the failed first query.
                    created.append((path, (info.st_dev, info.st_ino)))
                    stream.write(content)
        except BaseException:
            for path, identity in reversed(created):
                try:
                    info = path.lstat()
                    if not archive.is_link(info) and (info.st_dev, info.st_ino) == identity:
                        path.unlink()
                except OSError:
                    pass
            raise
        print(json.dumps({"ok": True, "output": str(args.output), "report": str(args.report),
                          "svg_sha256": report["svg_sha256"], "visual": "unverified"}))
        return 0
    except (MaterialError, archive.ArchiveError, OSError, ET.ParseError, UnicodeError,
            ValueError, OverflowError, RecursionError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
