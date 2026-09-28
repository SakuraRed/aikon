#!/usr/bin/env python3
"""Optional, dependency-free scene renderer and local revision helper.

No network, Git operations, raster embedding, or visual-quality assertions.
The path validator checks a finite-number character subset, not full SVG grammar.
"""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
import xml.etree.ElementTree as ET


HELPER_VERSION = "0.1.1"
SCENE_SCHEMA = "aikon.scene.v1"
SVG_NS = "http://www.w3.org/2000/svg"
MAX_BYTES = 2 * 1024 * 1024
MAX_PATH = 65536
NUMBER = r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?"
NUMBER_RE = re.compile(NUMBER, re.ASCII)
POINTS_RE = re.compile(NUMBER + r"(?:(?:[ \t\r\n]*,[ \t\r\n]*|[ \t\r\n]+)" + NUMBER + r")*", re.ASCII)
PATH_RE = re.compile(r"[MmZzLlHhVvCcSsQqTtAa0-9eE+., \t\r\n-]+", re.ASCII)
ID_RE = re.compile(r"[a-z][a-z0-9-]{0,63}", re.ASCII)
COLOR_RE = re.compile(r"#[0-9a-fA-F]{6}", re.ASCII)
REV_RE = re.compile(r"r[0-9]{3,31}", re.ASCII)
ROUND_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", re.ASCII)
PAINT = {"fill", "stroke", "stroke-width", "opacity", "fill-opacity", "stroke-opacity",
         "fill-rule", "stroke-linecap", "stroke-linejoin", "stroke-miterlimit"}
GEOMETRY = {
    "path": ({"d"}, set()),
    "rect": ({"width", "height"}, {"x", "y", "rx", "ry"}),
    "circle": ({"r"}, {"cx", "cy"}),
    "ellipse": ({"rx", "ry"}, {"cx", "cy"}),
    "polygon": ({"points"}, set()),
    "polyline": ({"points"}, set()),
    "line": ({"x1", "y1", "x2", "y2"}, set()),
}
ENUMS = {"fill-rule": {"nonzero", "evenodd"}, "stroke-linecap": {"butt", "round", "square"},
         "stroke-linejoin": {"miter", "round", "bevel"}}


class AikonError(ValueError):
    """Invalid scene, unsupported SVG, or unsafe output request."""


def fields(value, required, optional, label):
    if not isinstance(value, dict):
        raise AikonError(label + " must be an object")
    missing, extra = required - value.keys(), value.keys() - required - optional
    if missing or extra:
        raise AikonError(f"{label}: missing={sorted(missing)}, unknown={sorted(extra)}")


def number(value, label, minimum=None, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AikonError(label + " must be a finite number")
    try:
        valid = math.isfinite(value)
    except OverflowError:
        valid = False
    if not valid or (minimum is not None and value < minimum) or (positive and value <= 0):
        raise AikonError(label + " is outside its finite numeric range")
    return value


def n(value):
    number(value, "derived coordinate")
    if value == 0:
        return "0"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def text_value(value, label, nonempty=False):
    if not isinstance(value, str) or len(value) > 4096 or (nonempty and not value.strip()):
        raise AikonError(label + " must be a string of at most 4096 characters")
    if any(not (c in "\t\n\r" or 0x20 <= ord(c) <= 0xD7FF or
                0xE000 <= ord(c) <= 0xFFFD or 0x10000 <= ord(c) <= 0x10FFFF) for c in value):
        raise AikonError(label + " contains an invalid XML character")
    return value


def color(value, label, allow_none=False):
    if isinstance(value, str) and ((allow_none and value == "none") or COLOR_RE.fullmatch(value)):
        return value.lower()
    raise AikonError(label + " must be #RRGGBB" + (" or none" if allow_none else ""))


def point(value, label):
    if not isinstance(value, list) or len(value) != 2:
        raise AikonError(label + " must contain two coordinates")
    return [number(v, label) for v in value]


def path_data(value):
    if (not isinstance(value, str) or not value.strip() or len(value) > MAX_PATH or
            not PATH_RE.fullmatch(value) or value.lstrip()[0] not in "Mm"):
        raise AikonError("d must be bounded, moveto-first SVG path data without URLs or other text")
    tokens = NUMBER_RE.findall(value)
    if len(tokens) < 2:
        raise AikonError("d needs at least the initial moveto coordinates")
    for token in tokens:
        number(float(token), "path coordinate")
    return value


def points_data(value, tag):
    if not isinstance(value, str) or len(value) > MAX_PATH or not POINTS_RE.fullmatch(value.strip()):
        raise AikonError("points must be coordinate pairs separated by whitespace or single commas")
    values = NUMBER_RE.findall(value)
    if len(values) % 2 or len(values) < (6 if tag == "polygon" else 4):
        raise AikonError(tag + " has too few complete coordinate pairs")
    for token in values:
        number(float(token), "points coordinate")
    return value


def shape_attributes(tag, attrs, from_xml=False):
    if not isinstance(tag, str) or tag not in GEOMETRY:
        raise AikonError("unsupported shape: " + str(tag))
    required, optional = GEOMETRY[tag]
    fields(attrs, required, optional | PAINT, tag + " attributes")
    result = {}
    for key, raw in sorted(attrs.items()):
        if key in {"fill", "stroke"}:
            value = color(raw, key, allow_none=True)
        elif key in ENUMS:
            if not isinstance(raw, str) or raw not in ENUMS[key]:
                raise AikonError("invalid " + key)
            value = raw
        elif key == "d":
            value = path_data(raw)
        elif key == "points":
            value = points_data(raw, tag)
        else:
            if from_xml:
                if not isinstance(raw, str) or not NUMBER_RE.fullmatch(raw):
                    raise AikonError(key + " must be a finite unitless number")
                raw = float(raw)
            minimum = 0 if key in {"rx", "ry", "stroke-width", "opacity", "fill-opacity", "stroke-opacity"} else None
            if key == "stroke-miterlimit":
                minimum = 1
            positive = key in {"width", "height", "r"} or (tag == "ellipse" and key in {"rx", "ry"})
            value = number(raw, key, minimum, positive)
            if key in {"opacity", "fill-opacity", "stroke-opacity"} and value > 1:
                raise AikonError(key + " must be between 0 and 1")
            value = n(value)
        result[key] = value
    return result


def validate_scene(scene):
    fields(scene, {"schema", "title", "background", "head", "eyes", "layers"}, {"style_overrides", "variant"}, "scene")
    if scene["schema"] != SCENE_SCHEMA:
        raise AikonError("unsupported scene schema")
    text_value(scene["title"], "title")
    if scene["background"] is not None:
        color(scene["background"], "background")
    if "variant" in scene:
        variant = scene["variant"]
        fields(variant, {"round_id", "profile"}, set(), "variant")
        if not isinstance(variant["round_id"], str) or not ROUND_RE.fullmatch(variant["round_id"]):
            raise AikonError("round_id must be 1..64 ASCII letters/digits, underscores or hyphens, beginning with a letter/digit")
        if not isinstance(variant["profile"], str) or variant["profile"] not in {"short", "full"}:
            raise AikonError("profile must be short or full")
    override = scene.get("style_overrides", {})
    if "style_overrides" in scene:
        fields(override, {"reason"}, {"angle", "eye_ratio"}, "style_overrides")
        text_value(override["reason"], "override reason", nonempty=True)
        for key in {"angle", "eye_ratio"} & override.keys():
            if not isinstance(override[key], bool):
                raise AikonError("override flags must be booleans")
    fields(scene["head"], {"angle", "pivot"}, set(), "head")
    angle = number(scene["head"]["angle"], "head angle")
    point(scene["head"]["pivot"], "pivot")
    if not override.get("angle") and not 15 <= angle <= 20:
        raise AikonError("angle must be 15..20 unless explicitly overridden")
    eyes = scene["eyes"]
    fields(eyes, {"centers", "width", "height", "fill"}, set(), "eyes")
    width, height = number(eyes["width"], "eye width", positive=True), number(eyes["height"], "eye height", positive=True)
    ratio = number(height / width, "eye ratio")
    if not override.get("eye_ratio") and not 2.5 <= ratio <= 3:
        raise AikonError("eye height/width must be 2.5..3 unless explicitly overridden")
    color(eyes["fill"], "eye fill")
    if not isinstance(eyes["centers"], list) or len(eyes["centers"]) != 2:
        raise AikonError("eyes need exactly two centers")
    left, right = [point(v, "eye center") for v in eyes["centers"]]
    if left[1] != right[1] or left[0] >= right[0]:
        raise AikonError("eye centers need equal y and strictly increasing x")
    layers = scene["layers"]
    if not isinstance(layers, list) or not layers or len(layers) > 256:
        raise AikonError("layers must be a nonempty list of at most 256 layers")
    ids = {"head", "background", "eye-left", "eye-right"}
    for layer in layers:
        fields(layer, {"id"}, {"shapes"}, "layer")
        layer_id = layer["id"]
        if not isinstance(layer_id, str) or not ID_RE.fullmatch(layer_id) or layer_id in ids:
            raise AikonError("layer IDs must be valid, unique, and not reserved")
        ids.add(layer_id)
        shapes = layer.get("shapes", [])
        if not isinstance(shapes, list) or len(shapes) > 2048:
            raise AikonError("shapes must be an array of at most 2048 shapes")
        if layer_id == "eyes" and shapes:
            raise AikonError("eyes layer cannot contain custom shapes")
        if layer_id != "eyes" and "shapes" not in layer:
            raise AikonError("non-eye layers require shapes")
        for shape in shapes:
            fields(shape, {"tag", "attrs"}, set(), "shape")
            shape_attributes(shape["tag"], shape["attrs"])
    if "eyes" not in ids:
        raise AikonError("exactly one eyes layer is required")


def render_scene(scene):
    validate_scene(scene)
    root = ET.Element("svg", {"xmlns": SVG_NS, "viewBox": "0 0 512 512", "width": "512", "height": "512"})
    ET.SubElement(root, "title").text = scene["title"]
    if scene["background"] is not None:
        ET.SubElement(root, "rect", {"id": "background", "width": "512", "height": "512", "fill": color(scene["background"], "background")})
    angle, (px, py) = scene["head"]["angle"], scene["head"]["pivot"]
    head = ET.SubElement(root, "g", {"id": "head", "transform": f"rotate({n(angle)} {n(px)} {n(py)})"})
    for layer in scene["layers"]:
        group = ET.SubElement(head, "g", {"id": layer["id"]})
        if layer["id"] == "eyes":
            eyes = scene["eyes"]
            width, height = eyes["width"], eyes["height"]
            for eye_id, (x, y) in zip(("eye-left", "eye-right"), eyes["centers"]):
                attrs = {"id": eye_id, "x": n(x - width / 2), "y": n(y - height / 2),
                         "width": n(width), "height": n(height), "rx": n(width / 2), "ry": n(width / 2),
                         "fill": color(eyes["fill"], "eye fill")}
                ET.SubElement(group, "rect", dict(sorted(attrs.items())))
        else:
            for shape in layer["shapes"]:
                ET.SubElement(group, shape["tag"], shape_attributes(shape["tag"], shape["attrs"]))
    result = ET.tostring(root, encoding="utf-8", short_empty_elements=True) + b"\n"
    if len(result) > MAX_BYTES:
        raise AikonError("generated SVG exceeds 2 MiB")
    return result


def background_facts(root):
    """Report plain root canvas rectangles, never infer rendered pixel alpha."""
    rectangles = []
    for element in root:
        if element.tag != "{" + SVG_NS + "}rect":
            continue
        x, y = float(element.get("x", "0")), float(element.get("y", "0"))
        width, height = float(element.get("width")), float(element.get("height"))
        # Rounded, transformed, nested, and arbitrary path coverage need rendering.
        if (x > 0 or y > 0 or x + width < 512 or y + height < 512 or
                float(element.get("rx", "0")) or float(element.get("ry", "0"))):
            continue
        fill = element.get("fill", "#000000").lower()
        alpha = float(element.get("opacity", "1")) * float(element.get("fill-opacity", "1"))
        if fill == "none":
            alpha = 0.0
        rectangles.append({"id": element.get("id"), "fill": fill, "declared_fill_alpha": alpha})
    if any(item["declared_fill_alpha"] == 1 for item in rectangles):
        status = "opaque_canvas_rect"
    elif any(item["declared_fill_alpha"] > 0 for item in rectangles):
        status = "translucent_canvas_rect"
    else:
        status = "no_painted_canvas_rect_detected"
    return {"structural_status": status, "canvas_rects": rectangles, "raster_alpha": "unverified"}


def check_svg(data):
    issues = []
    background = {"structural_status": "unverified", "canvas_rects": [], "raster_alpha": "unverified"}
    try:
        if len(data) > MAX_BYTES:
            raise AikonError("SVG exceeds 2 MiB")
        text = data.decode("utf-8-sig") if isinstance(data, bytes) else data
        if re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", text, re.I):
            raise AikonError("DTD and entity declarations are not supported")
        without_decl = re.sub(r"\A\s*<\?xml\s[^?]*\?>", "", text, count=1)
        if "<?" in without_decl:
            raise AikonError("processing instructions are not supported")
        root = ET.fromstring(text)
        if root.tag != "{" + SVG_NS + "}svg":
            raise AikonError("root must be SVG in the SVG namespace")
        if root.get("viewBox") != "0 0 512 512":
            raise AikonError("viewBox must be 0 0 512 512")
        seen = set()
        parents = {child: parent for parent in root.iter() for child in parent}
        for element in root.iter():
            tag = element.tag.removeprefix("{" + SVG_NS + "}")
            attrs = dict(element.attrib)
            element_id = attrs.pop("id", None)
            if element_id is not None:
                if not ID_RE.fullmatch(element_id) or element_id in seen:
                    raise AikonError("invalid or duplicate SVG id")
                seen.add(element_id)
            if tag in GEOMETRY:
                shape_attributes(tag, attrs, from_xml=True)
            elif tag == "svg" and element is root:
                fields(attrs, {"viewBox"}, {"width", "height"}, "svg attributes")
                for key in {"width", "height"} & attrs.keys():
                    if not NUMBER_RE.fullmatch(attrs[key]):
                        raise AikonError("SVG size must be a finite unitless number")
                    number(float(attrs[key]), "SVG " + key, positive=True)
            elif tag == "g":
                head_transform = element_id == "head" and parents.get(element) is root
                fields(attrs, set(), {"transform"} if head_transform else set(), "group attributes")
                if "transform" in attrs:
                    match = re.fullmatch(r"rotate\((" + NUMBER + r") (" + NUMBER + r") (" + NUMBER + r")\)", attrs["transform"], re.ASCII)
                    if not match:
                        raise AikonError("only the head's finite rotate(angle x y) transform is supported")
                    for value in match.groups():
                        number(float(value), "rotation")
            elif tag in {"title", "desc"}:
                fields(attrs, set(), set(), tag + " attributes")
            else:
                raise AikonError("unsupported element or namespace: " + str(element.tag))
            if tag not in {"g", "svg"} and len(element):
                raise AikonError("leaf SVG element contains child elements")
            if tag not in {"title", "desc"} and element.text and element.text.strip():
                raise AikonError("unexpected text outside title/desc")
            if element.tail and element.tail.strip():
                raise AikonError("unexpected trailing SVG text")
        background = background_facts(root)
    except (AikonError, ET.ParseError, UnicodeError, ValueError, OverflowError) as exc:
        issues.append(str(exc))
    return {"schema": "aikon.check.v1", "ok": not issues,
            "checks": {"structural": "failed" if issues else "passed", "visual": "unverified"},
            "background": background, "issues": issues}


def canonical_json(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def read_bytes(path):
    with open(path, "rb") as stream:
        result = stream.read(MAX_BYTES + 1)
    if len(result) > MAX_BYTES:
        raise AikonError("input exceeds 2 MiB")
    return result


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise AikonError("duplicate JSON key: " + key)
        result[key] = value
    return result


def read_scene(path):
    def invalid_constant(value):
        raise AikonError("non-finite JSON constant: " + value)
    return json.loads(read_bytes(path).decode("utf-8-sig"), object_pairs_hook=unique_object,
                      parse_constant=invalid_constant)


def is_link(info):
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def output_path(value):
    raw = Path(value).expanduser()
    if ".." in raw.parts:
        raise AikonError("output paths cannot contain '..'")
    return Path(os.path.abspath(raw))


def safe_directory(path, create=False):
    """Reject existing symlinks and Windows junction/reparse directories."""
    for directory in [*reversed(path.parents), path]:
        try:
            info = directory.lstat()
        except FileNotFoundError:
            if not create:
                raise AikonError("directory not found: " + str(directory))
            try:
                directory.mkdir()
            except FileExistsError:
                pass
            info = directory.lstat()
        if is_link(info) or not stat.S_ISDIR(info.st_mode):
            raise AikonError("output directory is not a plain directory: " + str(directory))


def plain_file(path):
    info = path.lstat()
    if is_link(info) or not stat.S_ISREG(info.st_mode):
        raise AikonError("expected a plain file: " + str(path))


def write_render(path, content, replace=False):
    target = output_path(path)
    safe_directory(target.parent, create=True)
    if os.path.lexists(target):
        plain_file(target)
        if not replace:
            raise AikonError("output exists; use --replace only for an explicitly replaceable draft")
    fd, temporary = tempfile.mkstemp(prefix=".aikon-render-", suffix=".svg", dir=target.parent)
    temporary = Path(temporary)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
        safe_directory(target.parent)
        if replace:
            if os.path.lexists(target):
                plain_file(target)
            os.replace(temporary, target)
        else:
            # Atomic no-clobber publication; source and destination share a filesystem.
            os.link(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def revision_id(value):
    if not isinstance(value, str) or not REV_RE.fullmatch(value):
        raise AikonError("revision must be r followed by at least three digits, at most 32 characters total")
    return value


def sha256(content):
    return hashlib.sha256(content).hexdigest()


def validate_parent(revisions, parent):
    parent_dir = revisions / revision_id(parent)
    safe_directory(parent_dir)
    for name in ("scene.json", "icon.svg", "revision.json"):
        plain_file(parent_dir / name)
    manifest = json.loads(read_bytes(parent_dir / "revision.json").decode("utf-8"))
    if not isinstance(manifest, dict) or manifest.get("schema") != "aikon.revision.v1" or manifest.get("revision") != parent:
        raise AikonError("parent is not a completed Aikon revision")
    for name, key in (("scene.json", "scene_sha256"), ("icon.svg", "svg_sha256")):
        if manifest.get(key) != sha256(read_bytes(parent_dir / name)):
            raise AikonError("parent content does not match its recorded hash")


def cleanup_owned_directory(path, identity):
    """Only remove our three known files from the exact directory we created."""
    try:
        info = path.lstat()
    except FileNotFoundError:
        return
    if is_link(info) or (info.st_dev, info.st_ino) != identity:
        return
    for name in ("scene.json", "icon.svg", "revision.json"):
        (path / name).unlink(missing_ok=True)
    path.rmdir()


def snapshot(scene, root, revision, parent=None, note=""):
    revision_id(revision)
    if parent is not None:
        revision_id(parent)
        if parent == revision:
            raise AikonError("a revision cannot be its own parent")
    text_value(note, "note")
    svg = render_scene(scene)
    result = check_svg(svg)
    if not result["ok"]:
        raise AikonError("generated SVG failed structural checks: " + "; ".join(result["issues"]))
    scene_bytes = canonical_json(scene)
    if len(scene_bytes) > MAX_BYTES:
        raise AikonError("scene exceeds 2 MiB")
    revisions = output_path(root) / "revisions"
    safe_directory(revisions, create=True)
    destination = revisions / revision
    if os.path.lexists(destination):
        raise AikonError("revision already exists")
    if parent is not None:
        validate_parent(revisions, parent)
    variant = scene.get("variant", {})
    manifest = {"schema": "aikon.revision.v1", "revision": revision, "parent": parent, "note": note,
                "helper_version": HELPER_VERSION, "scene_sha256": sha256(scene_bytes),
                "svg_sha256": sha256(svg), "checks": result["checks"], "background": result["background"],
                "round_id": variant.get("round_id"), "profile": variant.get("profile")}
    contents = {"scene.json": scene_bytes, "icon.svg": svg, "revision.json": canonical_json(manifest)}
    staging = Path(tempfile.mkdtemp(prefix=".aikon-staging-", dir=revisions))
    staging_info = staging.stat()
    staging_identity = (staging_info.st_dev, staging_info.st_ino)
    destination_identity = None
    try:
        for name, content in contents.items():
            (staging / name).write_bytes(content)
        safe_directory(revisions)
        destination.mkdir()  # Exclusive reservation: even an existing empty directory fails.
        info = destination.stat()
        destination_identity = (info.st_dev, info.st_ino)
        for name in contents:  # revision.json is the final completion marker.
            os.replace(staging / name, destination / name)
    except BaseException:
        if destination_identity is not None:
            cleanup_owned_directory(destination, destination_identity)
        raise
    finally:
        cleanup_owned_directory(staging, staging_identity)
    return destination


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    render = commands.add_parser("render", help="export deterministic SVG; does not visually validate")
    render.add_argument("--scene", required=True)
    render.add_argument("--output", required=True)
    render.add_argument("--replace", action="store_true")
    check = commands.add_parser("check", help="check the restricted static SVG structure")
    check.add_argument("--svg", required=True)
    save = commands.add_parser("snapshot", help="create a new local immutable revision")
    save.add_argument("--scene", required=True)
    save.add_argument("--root", required=True)
    save.add_argument("--revision", required=True)
    save.add_argument("--parent")
    save.add_argument("--note", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "check":
            result = check_svg(read_bytes(args.svg))
            print(json.dumps(result, ensure_ascii=False, sort_keys=True))
            return 0 if result["ok"] else 1
        scene = read_scene(args.scene)
        if args.command == "render":
            svg = render_scene(scene)
            write_render(args.output, svg, args.replace)
            print(json.dumps({"output": str(args.output), "checks": {"structural": "unverified", "visual": "unverified"}}))
        else:
            destination = snapshot(scene, args.root, args.revision, args.parent, args.note)
            print(json.dumps({"revision_path": str(destination), "checks": {"structural": "passed", "visual": "unverified"}}))
        return 0
    except (AikonError, OSError, ValueError, UnicodeError, OverflowError) as exc:
        result = {"ok": False, "issues": [str(exc)], "checks": {"structural": "failed", "visual": "unverified"}}
        print(json.dumps(result, ensure_ascii=False, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
