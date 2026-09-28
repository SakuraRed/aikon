#!/usr/bin/env python3
"""Compile explicit, analytic paint onto existing vector geometry; stdlib only.

This restricts a drawing method, not aesthetic judgment. It never derives paint
islands from raster pixels and never claims that a declared shadow is natural.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

VERSION = "0.2.0"
NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)
SHAPES = {"path", "rect", "circle", "ellipse", "polygon", "polyline", "line"}
ALLOWED = SHAPES | {"svg", "g", "defs", "clipPath", "linearGradient", "radialGradient", "stop", "title", "desc"}
ROLES = {"surface", "underpaint", "eye", "blush", "occlusion-shadow"}
COLOR = re.compile(r"#[0-9a-fA-F]{6}\Z")
ID = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,95}\Z")
GEOMETRY_ATTRS = {"d", "x", "y", "width", "height", "rx", "ry", "r", "cx", "cy", "points", "transform", "fill-rule", "clip-rule"}


class PaintError(ValueError):
    pass


def local(element):
    if not isinstance(element.tag, str) or not element.tag.startswith("{" + NS + "}"):
        raise PaintError("Expected SVG namespace")
    return element.tag.split("}", 1)[1]


def fields(obj, required, optional, label):
    if not isinstance(obj, dict) or required - obj.keys() or obj.keys() - required - optional:
        raise PaintError("Invalid fields in " + label)


def number(value):
    try:
        finite = not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)
    except OverflowError:
        finite = False
    if not finite:
        raise PaintError("Paint coordinates must be finite numbers")
    return value


def point(value):
    if not isinstance(value, list) or len(value) != 2:
        raise PaintError("Expected two paint coordinates")
    return [number(x) for x in value]


def color(value):
    if not isinstance(value, str) or not COLOR.fullmatch(value):
        raise PaintError("Paint colors must be opaque #RRGGBB")
    return value.lower()


def luma(value):
    channels = [int(value[i:i + 2], 16) for i in (1, 3, 5)]
    return sum(a * b for a, b in zip(channels, (.2126, .7152, .0722)))


def parse_geometry(data):
    if len(data) > 4 * 1024 * 1024 or b"<!" in data or b"<?" in re.sub(br"^\s*<\?xml[^?]*\?>", b"", data):
        raise PaintError("Unsupported SVG declaration or size")
    root = ET.fromstring(data)
    if local(root) != "svg":
        raise PaintError("Expected an SVG root")
    ids = {}
    elements = list(root.iter())
    if len(elements) > 10000:
        raise PaintError("Geometry exceeds the element budget")
    for e in elements:
        if local(e) not in ALLOWED:
            raise PaintError("Unsupported vector element: " + local(e))
        for key, value in e.attrib.items():
            if key.lower().startswith("on") or key in {"style", "filter", "mask"}:
                raise PaintError("Active, styled, filtered or masked geometry is not supported")
            lowered = value.lower()
            if "href" in key.lower() or any(scheme in lowered for scheme in ("data:", "http:", "https:", "file:", "javascript:")):
                raise PaintError("External or embedded content is not supported")
            for target in re.findall(r"url\(([^)]*)\)", value, re.I):
                if not re.fullmatch(r"#[A-Za-z][A-Za-z0-9_-]*", target):
                    raise PaintError("Only local vector references are supported")
        key = e.get("id")
        if key:
            if not ID.fullmatch(key) or key in ids:
                raise PaintError("Invalid or duplicate ID")
            ids[key] = e
    return root, ids


def validate_plan(plan, digest, ids):
    fields(plan, {"schema", "geometry_sha256", "profile", "layers"}, {"notes", "reference_bindings"}, "plan")
    if plan["schema"] != "aikon.paint-plan.v1" or plan["geometry_sha256"] != digest:
        raise PaintError("Paint plan does not match this geometry")
    if plan["profile"] not in {"short", "full"}:
        raise PaintError("Unknown profile")
    if not isinstance(plan["layers"], list) or not 1 <= len(plan["layers"]) <= 64:
        raise PaintError("Expected 1..64 explicitly selected paint layers")
    selected = {}
    for layer in plan["layers"]:
        fields(layer, {"id", "role", "paint"}, {"owner", "anchor", "reason"}, "paint layer")
        key, role = layer["id"], layer["role"]
        if not isinstance(key, str) or key in selected or key not in ids or local(ids[key]) not in SHAPES:
            raise PaintError("Paint target must be a unique existing vector shape")
        if not isinstance(role, str) or role not in ROLES:
            raise PaintError("Unsupported paint role; arbitrary highlight patches are not a default primitive")
        paint = layer["paint"]
        if not isinstance(paint, dict):
            raise PaintError("Paint must be an object")
        if paint.get("type") == "solid":
            fields(paint, {"type", "color"}, set(), "solid paint")
            color(paint["color"])
        elif paint.get("type") == "linear":
            fields(paint, {"type", "from", "to", "colors"}, set(), "linear paint")
            if role != "surface" or point(paint["from"]) == point(paint["to"]):
                raise PaintError("A directional field belongs to a surface and needs a nonzero direction")
            if not isinstance(paint["colors"], list) or len(paint["colors"]) != 2:
                raise PaintError("Use exactly two opaque gradient endpoints")
            ends = [color(c) for c in paint["colors"]]
            if abs(luma(ends[0]) - luma(ends[1])) > 24:
                raise PaintError("Surface field exceeds the conservative 24/255 luma budget")
            if max(abs(int(ends[0][i:i+2],16)-int(ends[1][i:i+2],16)) for i in (1,3,5)) > 40:
                raise PaintError("Surface field crosses a color family")
        else:
            raise PaintError("Only solid or smooth two-stop linear paint is supported")
        if role == "occlusion-shadow":
            if paint["type"] != "solid" or layer.get("anchor") != "receiver-boundary" or not isinstance(layer.get("reason"), str) or not layer["reason"].strip():
                raise PaintError("Shadow needs an opaque tone, a boundary anchor and an explicit cause")
        elif role == "blush":
            if paint["type"] != "solid" or not layer.get("owner"):
                raise PaintError("Blush must be opaque and clipped to its face receiver")
        elif any(k in layer for k in ("owner", "anchor", "reason")):
            raise PaintError("Unexpected ownership metadata")
        selected[key] = layer
    for layer in selected.values():
        if layer["role"] in {"blush", "occlusion-shadow"}:
            if not isinstance(layer.get("owner"), str):
                raise PaintError("Paint owner must be an ID")
            owner = selected.get(layer.get("owner"))
            if not owner or owner["role"] != "surface":
                raise PaintError("Paint owner must be a selected surface")
            if layer["role"] == "occlusion-shadow":
                owner_colors = owner["paint"].get("colors", [owner["paint"].get("color")])
                difference = min(luma(c) for c in owner_colors) - luma(layer["paint"]["color"])
                if not 0 <= difference <= 24:
                    raise PaintError("Occlusion tone must be darker than its receiver, within 24/255 luma")
    return selected


def geometry_signature(root, keys):
    ids = {e.get("id"): e for e in root.iter() if e.get("id")}
    records = {}
    parents = {child: parent for parent in root.iter() for child in parent}
    for key in sorted(keys):
        e = ids[key]
        chain = []
        current = e
        while current is not None:
            if current.get("transform"):
                chain.append(current.get("transform"))
            current = parents.get(current)
        records[key] = {"tag": local(e), "geometry": {k:v for k,v in e.attrib.items() if k in GEOMETRY_ATTRS}, "transform_chain": chain}
    return hashlib.sha256(json.dumps(records,sort_keys=True,separators=(",", ":")).encode()).hexdigest()


def compile_paint(geometry, plan):
    root, ids = parse_geometry(geometry)
    digest = hashlib.sha256(geometry).hexdigest()
    selected = validate_plan(plan, digest, ids)
    # Drawing targets inside defs are not paint surfaces.
    in_defs = {id(e) for d in root.iter() if local(d) == "defs" for e in d.iter()}
    if any(id(ids[k]) in in_defs for k in selected):
        raise PaintError("A drawing layer cannot target definitions")
    before = geometry_signature(root, selected)
    layout_keys=[key for key,layer in selected.items() if layer["role"]!="occlusion-shadow"]
    layout_before=geometry_signature(root,layout_keys)
    removed = []
    def prune(e, definitions=False):
        definitions = definitions or local(e) == "defs"
        for child in list(e):
            kind = local(child)
            if kind in {"linearGradient", "radialGradient"} or (not definitions and kind in SHAPES and child.get("id") not in selected):
                removed.append(child.get("id", kind));e.remove(child)
            else:
                prune(child, definitions)
        for key in ("opacity", "fill-opacity", "stroke-opacity", "stroke", "stroke-width"):
            e.attrib.pop(key, None)
        if not definitions and local(e) == "g":
            e.attrib.pop("fill", None)
    prune(root)
    defs = root.find("{"+NS+"}defs")
    if defs is None:
        defs = ET.Element("{"+NS+"}defs");root.insert(0,defs)
    current = {e.get("id"):e for e in root.iter() if e.get("id")}
    owners = {}
    gradients = []
    for key, layer in selected.items():
        e = current[key];paint = layer["paint"]
        if paint["type"] == "solid":
            e.set("fill",color(paint["color"]))
        else:
            gid = "paint-field-"+key
            if gid in current:raise PaintError("Generated paint ID collision")
            x1,y1=paint["from"];x2,y2=paint["to"]
            gradient=ET.SubElement(defs,"{"+NS+"}linearGradient",{"id":gid,"gradientUnits":"userSpaceOnUse","x1":str(x1),"y1":str(y1),"x2":str(x2),"y2":str(y2)})
            for offset,c in zip(("0","1"),paint["colors"]):ET.SubElement(gradient,"{"+NS+"}stop",{"offset":offset,"stop-color":color(c)})
            e.set("fill","url(#"+gid+")");gradients.append(gid)
        if "owner" in layer:
            owner=layer["owner"]
            if owner not in owners:
                clip_id="paint-receiver-"+owner
                if clip_id in current:raise PaintError("Generated receiver ID collision")
                clip=ET.SubElement(defs,"{"+NS+"}clipPath",{"id":clip_id,"clipPathUnits":"userSpaceOnUse"})
                outline=copy.deepcopy(current[owner]);outline.attrib.pop("id",None);outline.set("fill","#ffffff")
                clip.append(outline);owners[owner]=clip_id
            # All supported sources in this contract express receiver and overlay
            # in a common user space; reject differing ancestor transforms.
            parents={c:p for p in root.iter() for c in p}
            def transforms(node):
                chain=[];node=parents.get(node)
                while node is not None:
                    if node.get("transform"):chain.append(node.get("transform"))
                    node=parents.get(node)
                return chain
            if transforms(e)!=transforms(current[owner]):raise PaintError("Receiver and overlay need a common coordinate space")
            parent=parents[e]
            wrapper_id="paint-ownership-"+key
            if wrapper_id in current:raise PaintError("Generated ownership ID collision")
            wrapper=ET.Element("{"+NS+"}g",{"id":wrapper_id,"clip-path":"url(#"+owners[owner]+")"})
            position=list(parent).index(e);parent.remove(e);wrapper.append(e);parent.insert(position,wrapper)
    after=geometry_signature(root,selected)
    if before!=after:raise PaintError("Painting changed selected geometry")
    data=ET.tostring(root,encoding="utf-8",xml_declaration=True)+b"\n"
    plan_digest=hashlib.sha256(json.dumps(plan,ensure_ascii=False,sort_keys=True,separators=(",", ":")).encode()).hexdigest()
    if layout_before!=geometry_signature(root,layout_keys):raise PaintError("Painting changed layout geometry")
    report={"schema":"aikon.paint-compile.v1","compiler_version":VERSION,"profile":plan["profile"],"paint_plan_sha256":plan_digest,"geometry_source_sha256":digest,"geometry_signature":after,"layout_geometry_signature":layout_before,"selected_geometry_unchanged":True,"retained_layers":list(selected),"discarded_prior_paint":removed,"gradient_count":len(gradients),"shadow_anchors":[{"id":v["id"],"owner":v["owner"],"anchor":v["anchor"],"reason":v["reason"]} for v in selected.values() if v["role"]=="occlusion-shadow"],"svg_sha256":hashlib.sha256(data).hexdigest(),"checks":{"static_paint_contract":"passed","boundary_anchor_pixels":"not_run","visual":"not_run","user_acceptance":"not_claimed"}}
    return data,report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--geometry",required=True,type=Path);p.add_argument("--plan",required=True,type=Path);p.add_argument("--output",required=True,type=Path);p.add_argument("--report",type=Path)
    args=p.parse_args()
    try:
        data,report=compile_paint(args.geometry.read_bytes(),json.loads(args.plan.read_text(encoding="utf-8")))
        if args.report and args.output.resolve()==args.report.resolve():raise PaintError("SVG and report need different paths")
        if args.output.exists() or (args.report and args.report.exists()):raise PaintError("Refusing to overwrite existing artifacts")
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with args.output.open("xb") as f:f.write(data)
        if args.report:
            args.report.parent.mkdir(parents=True,exist_ok=True)
            with args.report.open("x",encoding="utf-8",newline="\n") as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
        print(json.dumps(report,ensure_ascii=True))
    except (PaintError,OSError,ValueError,ET.ParseError) as e:
        print(json.dumps({"ok":False,"error":str(e)},ensure_ascii=True),file=sys.stderr);return 1
    return 0


if __name__=="__main__":raise SystemExit(main())
