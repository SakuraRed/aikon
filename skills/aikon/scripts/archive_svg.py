#!/usr/bin/env python3
"""Archive existing editable SVG bytes; never render, redraw, or approve art.

Python 3.9+ standard library. This checks a deliberately limited static subset,
not arbitrary SVG, full path grammar, or a sandbox for hostile rendering.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import sys
import xml.etree.ElementTree as ET


VERSION = "0.1.0"
SVG_NS = "http://www.w3.org/2000/svg"
XLINK_HREF = "{http://www.w3.org/1999/xlink}href"
MAX_BYTES = 2 * 1024 * 1024
NUMBER = r"[+-]?(?:[0-9]+\.?[0-9]*|\.[0-9]+)(?:[eE][+-]?[0-9]+)?"
NUMBER_RE = re.compile(NUMBER)
ID_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_.:-]{0,127}")
REV_RE = re.compile(r"r[0-9]{3,31}")
ROUND_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}")
HASH_RE = re.compile(r"[0-9a-f]{64}")
URL_RE = re.compile(r"url\(\s*(['\"]?)#([A-Za-z_][A-Za-z0-9_.:-]{0,127})\1\s*\)")
PATH_TOKEN_RE = re.compile(NUMBER + r"|[MmZzLlHhVvCcSsQqTtAa]")
GRADIENTS = {"linearGradient", "radialGradient"}
SHAPES = {"path", "rect", "circle", "ellipse", "line", "polygon", "polyline"}
TEXT_TAGS = {"title", "desc", "metadata"}
PRESENTATION = {"fill", "stroke", "opacity", "fill-opacity", "stroke-opacity",
                "stroke-width", "stroke-linecap", "stroke-linejoin", "stroke-miterlimit",
                "fill-rule", "clip-rule", "clip-path", "color-interpolation"}
ATTRS = {
    "svg": {"viewBox", "width", "height", "preserveAspectRatio", "version", "role",
            "aria-label", "aria-labelledby", "aria-describedby"} | PRESENTATION,
    "defs": set(), "g": {"transform"} | PRESENTATION,
    "clipPath": {"clipPathUnits", "transform"} | PRESENTATION,
    "linearGradient": {"x1", "y1", "x2", "y2", "gradientUnits", "gradientTransform",
                       "spreadMethod", "href", XLINK_HREF, "color-interpolation"},
    "radialGradient": {"cx", "cy", "r", "fx", "fy", "fr", "gradientUnits",
                       "gradientTransform", "spreadMethod", "href", XLINK_HREF, "color-interpolation"},
    "stop": {"offset", "stop-color", "stop-opacity", "color-interpolation"},
    "path": {"d", "transform"} | PRESENTATION,
    "rect": {"x", "y", "width", "height", "rx", "ry", "transform"} | PRESENTATION,
    "circle": {"cx", "cy", "r", "transform"} | PRESENTATION,
    "ellipse": {"cx", "cy", "rx", "ry", "transform"} | PRESENTATION,
    "line": {"x1", "y1", "x2", "y2", "transform"} | PRESENTATION,
    "polygon": {"points", "transform"} | PRESENTATION,
    "polyline": {"points", "transform"} | PRESENTATION,
    "title": set(), "desc": set(), "metadata": set(),
}
ENUMS = {
    "gradientUnits": {"userSpaceOnUse", "objectBoundingBox"},
    "clipPathUnits": {"userSpaceOnUse", "objectBoundingBox"},
    "spreadMethod": {"pad", "reflect", "repeat"},
    "color-interpolation": {"sRGB", "linearRGB"},
    "fill-rule": {"nonzero", "evenodd"}, "clip-rule": {"nonzero", "evenodd"},
    "stroke-linecap": {"butt", "round", "square"},
    "stroke-linejoin": {"miter", "round", "bevel"},
}
LENGTHS = {"x", "y", "x1", "y1", "x2", "y2", "cx", "cy", "r", "rx", "ry",
           "fx", "fy", "fr", "width", "height", "stroke-width"}
FILES = ("icon.svg", "prompt.md", "metadata.json", "revision.json")


class ArchiveError(ValueError):
    """An unsupported input or an unsafe archive request."""


def finite(value, label):
    if not NUMBER_RE.fullmatch(value.strip()):
        raise ArchiveError(label + " must be a finite SVG number")
    result = float(value)
    if not math.isfinite(result):
        raise ArchiveError(label + " must be finite")
    return result


def numbers(value, label):
    """Read a finite numeric list, without accepting unparsed trailing text."""
    pieces = re.split(r"[\s,]+", value.strip())
    if not value.strip() or any(not part for part in pieces):
        raise ArchiveError(label + " requires a numeric list")
    return [finite(part, label) for part in pieces]


def transform(value):
    counts = {"matrix": {6}, "translate": {1, 2}, "scale": {1, 2},
              "rotate": {1, 3}, "skewX": {1}, "skewY": {1}}
    end = 0
    found = False
    for match in re.finditer(r"([A-Za-z]+)\s*\(([^()]*)\)", value):
        if value[end:match.start()].strip(" \t\r\n,"):
            raise ArchiveError("unsupported transform syntax")
        kind, body = match.groups()
        if kind not in counts or len(numbers(body, "transform")) not in counts[kind]:
            raise ArchiveError("unsupported transform or parameter count")
        end, found = match.end(), True
    if not found or value[end:].strip(" \t\r\n,"):
        raise ArchiveError("unsupported transform syntax")


def path_data(value):
    if len(value) > 65536 or not value.lstrip().startswith(("M", "m")):
        raise ArchiveError("path must be moveto-first and at most 65536 characters")
    end, tokens = 0, []
    for match in PATH_TOKEN_RE.finditer(value):
        if value[end:match.start()].strip(" \t\r\n,"):
            raise ArchiveError("unsupported path token")
        token = match.group()
        if len(token) != 1 or token not in "MmZzLlHhVvCcSsQqTtAa":
            finite(token, "path coordinate")
        tokens.append(token)
        end = match.end()
    if value[end:].strip(" \t\r\n,") or len(tokens) < 3:
        raise ArchiveError("incomplete path data")
    finite(tokens[1], "initial moveto x")
    finite(tokens[2], "initial moveto y")


def color(value, allow_none=True):
    keywords = {"black", "white", "transparent"} | ({"none"} if allow_none else set())
    if value in keywords or re.fullmatch(r"#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})", value):
        return
    match = re.fullmatch(r"(rgb|rgba)\(([^()]*)\)", value)
    if match:
        channels = [part.strip() for part in match.group(2).split(",")]
        if len(channels) != (4 if match.group(1) == "rgba" else 3):
            raise ArchiveError("rgb/rgba requires three color channels and optional alpha")
        if len({part.endswith("%") for part in channels[:3]}) != 1:
            raise ArchiveError("rgb channels must consistently use numbers or percentages")
        for index, channel in enumerate(channels):
            percent = channel.endswith("%")
            number = finite(channel[:-1] if percent else channel, "color channel")
            limit = 100 if percent else (1 if index == 3 else 255)
            if not 0 <= number <= limit:
                raise ArchiveError("color channel is outside its numeric range")
        return
    raise ArchiveError("paint must use an explicit supported color or local gradient")


def local_reference(value):
    match = URL_RE.fullmatch(value.strip())
    if not match:
        raise ArchiveError("only local url(#id) references are supported")
    return match.group(2)


def tag_name(element):
    prefix = "{" + SVG_NS + "}"
    if not element.tag.startswith(prefix):
        raise ArchiveError("all elements must use the SVG namespace")
    return element.tag[len(prefix):]


def no_cycles(graph):
    """Include containment edges: a clip child can refer back to its own clip."""
    states = {}
    for start in graph:
        if states.get(start) == 2:
            continue
        stack = [(start, False)]
        while stack:
            node, leaving = stack.pop()
            if leaving:
                states[node] = 2
            elif states.get(node) == 1:
                raise ArchiveError("cyclic gradient or clip dependency")
            elif states.get(node) != 2:
                states[node] = 1
                stack.append((node, True))
                stack.extend((child, False) for child in graph[node])


def validate_svg(data):
    if not isinstance(data, bytes) or len(data) > MAX_BYTES:
        raise ArchiveError("SVG must be bytes of at most 2 MiB")
    text = data.decode("utf-8-sig")
    if re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", text, re.I):
        raise ArchiveError("DTD and entity declarations are not supported")
    without_decl = re.sub(r"\A<\?xml\s[^?]*\?>", "", text, count=1)
    if "<?" in without_decl:
        raise ArchiveError("processing instructions are not supported")
    declaration = text[:len(text) - len(without_decl)]
    encoding = re.search(r"encoding\s*=\s*['\"]([^'\"]+)['\"]", declaration)
    if encoding and encoding.group(1).lower() not in {"utf-8", "utf8"}:
        raise ArchiveError("only UTF-8 XML is supported")
    root = ET.fromstring(text)
    if tag_name(root) != "svg":
        raise ArchiveError("root must be svg")
    ids, references, graph, tags = {}, [], {}, {}
    pending = [(root, None, 1)]
    while pending:
        element, parent, depth = pending.pop()
        if depth > 64 or len(tags) >= 10000:
            raise ArchiveError("SVG exceeds 64 levels or 10000 elements")
        tag = tag_name(element)
        if tag not in ATTRS or (tag == "svg" and element is not root):
            raise ArchiveError("unsupported SVG element: " + tag)
        tags[element] = tag
        graph[element] = list(element)
        if parent is not None:
            parent_tag = tag_name(parent)
            allowed = ({"stop"} if parent_tag in GRADIENTS else
                       SHAPES | {"g", "title", "desc"} if parent_tag == "clipPath" else
                       SHAPES | GRADIENTS | TEXT_TAGS | {"g", "defs", "clipPath"}
                       if parent_tag in {"svg", "g", "defs"} else set())
            if tag not in allowed:
                raise ArchiveError("unsupported element placement: " + tag + " in " + parent_tag)
        if tag not in TEXT_TAGS and element.text and element.text.strip():
            raise ArchiveError("only title/desc/plain-text metadata can contain text")
        if element.tail and element.tail.strip():
            raise ArchiveError("unexpected trailing SVG text")
        for name, value in element.attrib.items():
            if name == "id":
                if not ID_RE.fullmatch(value) or value in ids:
                    raise ArchiveError("invalid or duplicate SVG id")
                ids[value] = element
                continue
            if re.fullmatch(r"data-[a-z][a-z0-9-]*", name):
                continue  # Inert caller metadata; never interpreted as instructions.
            if name not in ATTRS[tag]:
                raise ArchiveError("unsupported attribute on " + tag + ": " + name)
            if name in {"fill", "stroke"}:
                if value.strip().startswith("url("):
                    references.append((element, local_reference(value), GRADIENTS))
                else:
                    color(value)
            elif name == "stop-color":
                color(value, allow_none=False)
            elif name == "clip-path":
                if value != "none":
                    references.append((element, local_reference(value), {"clipPath"}))
            elif name in {"href", XLINK_HREF}:
                if not value.startswith("#") or not ID_RE.fullmatch(value[1:]):
                    raise ArchiveError("gradient href must reference a local gradient")
                references.append((element, value[1:], GRADIENTS))
            elif name in ENUMS:
                if value not in ENUMS[name]:
                    raise ArchiveError("unsupported " + name)
            elif name in {"transform", "gradientTransform"}:
                transform(value)
            elif name in LENGTHS:
                number = finite(value[:-1] if value.endswith("%") else value, name)
                if name in {"r", "rx", "ry", "fr", "width", "height", "stroke-width"} and number < 0:
                    raise ArchiveError(name + " cannot be negative")
            elif name in {"opacity", "fill-opacity", "stroke-opacity", "stop-opacity", "offset"}:
                number = finite(value[:-1] if value.endswith("%") else value, name)
                if not 0 <= number <= (100 if value.endswith("%") else 1):
                    raise ArchiveError(name + " is outside 0..1 / 0..100%")
            elif name == "stroke-miterlimit":
                if finite(value, name) < 1:
                    raise ArchiveError("stroke-miterlimit must be at least 1")
            elif name == "d":
                path_data(value)
            elif name == "points":
                coords = numbers(value, "points")
                if len(coords) % 2 or len(coords) < (6 if tag == "polygon" else 4):
                    raise ArchiveError("points requires complete coordinate pairs")
            elif name == "viewBox":
                coords = numbers(value, name)
                if len(coords) != 4 or coords[2] <= 0 or coords[2] != coords[3]:
                    raise ArchiveError("viewBox must have four numbers and a positive square size")
            elif name == "preserveAspectRatio":
                if not re.fullmatch(r"(?:none|x(?:Min|Mid|Max)Y(?:Min|Mid|Max)(?:\s+(?:meet|slice))?)", value):
                    raise ArchiveError("unsupported preserveAspectRatio")
            elif name == "version" and value not in {"1.0", "1.1", "2.0"}:
                raise ArchiveError("unsupported SVG version")
            elif name == "role" and value != "img":
                raise ArchiveError("only role=img is supported")
            elif name in {"aria-labelledby", "aria-describedby"}:
                references.extend((element, key, TEXT_TAGS) for key in value.split())
        required = {"svg": {"viewBox"}, "path": {"d"}, "rect": {"width", "height"},
                    "circle": {"r"}, "ellipse": {"rx", "ry"},
                    "polygon": {"points"}, "polyline": {"points"}}.get(tag, set())
        if required - element.attrib.keys():
            raise ArchiveError("missing required attributes on " + tag)
        if "href" in element.attrib and XLINK_HREF in element.attrib:
            raise ArchiveError("use only one gradient href spelling")
        pending.extend((child, element, depth + 1) for child in reversed(element))
    for element, target_id, kinds in references:
        target = ids.get(target_id)
        if target is None or tags[target] not in kinds:
            raise ArchiveError("missing or wrong-type local reference: " + target_id)
        graph[element].append(target)
    no_cycles(graph)


def check_svg(data):
    issues = []
    try:
        validate_svg(data)
    except (ArchiveError, ET.ParseError, UnicodeError, ValueError, OverflowError) as exc:
        issues.append(str(exc))
    return {"schema": "aikon.direct-svg.check.v1", "ok": not issues,
            "checks": {"structural": "failed" if issues else "passed",
                       "visual": "unverified", "raster_alpha": "unverified"},
            "user_acceptance": "unassessed", "issues": issues}


def read_bytes(path):
    with open(path, "rb") as stream:
        data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ArchiveError("each input must be at most 2 MiB")
    return data


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ArchiveError("duplicate JSON key: " + key)
        result[key] = value
    return result


def parse_json(data):
    def invalid_constant(value):
        raise ArchiveError("non-finite JSON constant: " + value)
    return json.loads(data.decode("utf-8-sig"), object_pairs_hook=unique_object,
                      parse_float=lambda value: finite(value, "JSON number"),
                      parse_constant=invalid_constant)


def fields(value, required, optional, label):
    if not isinstance(value, dict) or required - value.keys() or value.keys() - required - optional:
        raise ArchiveError(label + " has missing/unsupported fields")


def nonempty(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ArchiveError(label + " must be a nonempty string")


def string_list(value, label):
    if not isinstance(value, list):
        raise ArchiveError(label + " must be an array")
    for item in value:
        nonempty(item, label)


def validate_metadata(meta):
    fields(meta, {"schema", "round_id", "profile", "sources", "decisions", "changes", "provenance"},
           {"subject", "notes", "unresolved_questions"}, "metadata")
    if meta["schema"] != "aikon.direct-svg.metadata.v1":
        raise ArchiveError("unsupported metadata schema")
    if not isinstance(meta["round_id"], str) or not ROUND_RE.fullmatch(meta["round_id"]):
        raise ArchiveError("round_id must be a portable 1..64 character identifier")
    if meta["profile"] not in ("short", "full"):
        raise ArchiveError("profile must be short or full")
    for name in ("subject", "notes"):
        if name in meta:
            nonempty(meta[name], name)
    if "unresolved_questions" in meta:
        string_list(meta["unresolved_questions"], "unresolved_questions")
    if not isinstance(meta["sources"], list) or not isinstance(meta["decisions"], list):
        raise ArchiveError("sources and decisions must be arrays")
    for source in meta["sources"]:
        fields(source, {"role", "location", "rights_status"},
               {"sha256", "acquired_at", "purpose", "visual_selection_reason"}, "source")
        if source["role"] not in ("subject", "style", "both"):
            raise ArchiveError("source role must be subject, style or both")
        for key, value in source.items():
            nonempty(value, "source " + key)
        if "sha256" in source and not HASH_RE.fullmatch(source["sha256"]):
            raise ArchiveError("source sha256 must be lowercase SHA-256")
    decision_ids = set()
    for decision in meta["decisions"]:
        fields(decision, {"id", "value", "origin"}, {"evidence"}, "decision")
        nonempty(decision["id"], "decision id")
        if decision["id"] in decision_ids:
            raise ArchiveError("decision IDs must be unique")
        decision_ids.add(decision["id"])
        if decision["origin"] not in ("user", "reference_observation", "agent_default"):
            raise ArchiveError("unknown decision origin")
        if "evidence" in decision:
            nonempty(decision["evidence"], "decision evidence")
    changes = meta["changes"]
    fields(changes, {"summary", "targets", "preserved"}, set(), "changes")
    nonempty(changes["summary"], "change summary")
    string_list(changes["targets"], "change targets")
    string_list(changes["preserved"], "preserved parts")
    provenance = meta["provenance"]
    fields(provenance, {"method", "tool", "version"}, {"model", "script_sha256"}, "provenance")
    nonempty(provenance["method"], "provenance method")
    for name in ("tool", "version", "model"):
        if name in provenance and provenance[name] is not None:
            nonempty(provenance[name], "provenance " + name)
    if "script_sha256" in provenance:
        value = provenance["script_sha256"]
        if not isinstance(value, str) or not HASH_RE.fullmatch(value):
            raise ArchiveError("script_sha256 must be lowercase SHA-256")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def is_link(info):
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def directory(path, created=None):
    for item in [*reversed(path.parents), path]:
        try:
            info = item.lstat()
        except FileNotFoundError:
            if created is None:
                raise ArchiveError("directory does not exist: " + str(item))
            item.mkdir()  # Do not take ownership of a concurrently created directory.
            info = item.lstat()
            created.append((item, (info.st_dev, info.st_ino)))
        if is_link(info) or not stat.S_ISDIR(info.st_mode):
            raise ArchiveError("archive paths must use plain directories: " + str(item))


def output_root(value):
    if isinstance(value, str) and not value.strip():
        raise ArchiveError("archive root must be an explicitly chosen nonempty path")
    raw = Path(value).expanduser()
    if ".." in raw.parts:
        raise ArchiveError("archive root cannot contain '..'")
    return Path(os.path.abspath(raw))


def revision_id(value):
    if not isinstance(value, str) or not REV_RE.fullmatch(value):
        raise ArchiveError("revision must be r followed by 3..31 digits")
    return value


def parent_record(revisions, parent, meta):
    path = revisions / revision_id(parent)
    directory(path)
    for name in FILES:
        info = (path / name).lstat()
        if is_link(info) or not stat.S_ISREG(info.st_mode):
            raise ArchiveError("parent contains a non-regular archive file")
    data = read_bytes(path / "revision.json")
    manifest = parse_json(data)
    if (not isinstance(manifest, dict) or manifest.get("schema") != "aikon.direct-svg.revision.v1"
            or manifest.get("revision") != parent):
        raise ArchiveError("parent is not a completed direct-SVG revision")
    if any(manifest.get(key) != meta[key] for key in ("round_id", "profile")):
        raise ArchiveError("parent must belong to the same round and profile")
    records = manifest.get("files")
    if not isinstance(records, dict):
        raise ArchiveError("parent has no content hashes")
    for name in FILES[:-1]:
        content = read_bytes(path / name)
        if records.get(name) != {"sha256": sha256(content), "bytes": len(content)}:
            raise ArchiveError("parent content does not match its recorded hash: " + name)
    return sha256(data)


def remove_owned_empty_directories(created):
    for path, identity in reversed(created):
        try:
            info = path.lstat()
            if not is_link(info) and (info.st_dev, info.st_ino) == identity:
                path.rmdir()
        except OSError:
            pass  # Never remove other writers' files, links or nonempty directories.


def snapshot(svg_path, prompt_path, metadata_path, root, revision, parent=None):
    revision_id(revision)
    if parent is not None and revision_id(parent) == revision:
        raise ArchiveError("a revision cannot be its own parent")
    svg, prompt, metadata = [read_bytes(path) for path in (svg_path, prompt_path, metadata_path)]
    result = check_svg(svg)
    if not result["ok"]:
        raise ArchiveError("SVG structure failed: " + "; ".join(result["issues"]))
    nonempty(prompt.decode("utf-8-sig"), "prompt")
    meta = parse_json(metadata)
    validate_metadata(meta)
    revisions = output_root(root) / "revisions"
    destination = revisions / revision
    if os.path.lexists(destination):
        raise ArchiveError("revision already exists; choose a new revision ID")
    parent_hash = parent_record(revisions, parent, meta) if parent is not None else None
    contents = {"icon.svg": svg, "prompt.md": prompt, "metadata.json": metadata}
    manifest = {"schema": "aikon.direct-svg.revision.v1", "archive_version": VERSION,
                "revision": revision, "parent": parent, "parent_manifest_sha256": parent_hash,
                "round_id": meta["round_id"], "profile": meta["profile"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "files": {name: {"sha256": sha256(data), "bytes": len(data)} for name, data in contents.items()},
                "checks": result["checks"], "visual_review": "not_run", "user_acceptance": "unassessed"}
    contents["revision.json"] = json_bytes(manifest)  # Last file is the completion marker.
    created, written = [], []
    try:
        directory(revisions, created)
        destination.mkdir()  # Exclusive even when an existing directory is empty.
        info = destination.lstat()
        identity = (info.st_dev, info.st_ino)
        created.append((destination, identity))
        for name, content in contents.items():
            path = destination / name
            with path.open("xb") as stream:
                try:
                    info = os.fstat(stream.fileno())
                except OSError:
                    # Identify the same open descriptor for rollback, never an
                    # arbitrary replacement found by a path-based fallback.
                    info = os.stat(stream.fileno())
                    written.append((path, (info.st_dev, info.st_ino)))
                    raise
                written.append((path, (info.st_dev, info.st_ino)))
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
    except BaseException:
        for path, identity in reversed(written):
            try:
                info = path.lstat()
                if not is_link(info) and (info.st_dev, info.st_ino) == identity:
                    path.unlink()
            except OSError:
                pass
        remove_owned_empty_directories(created)
        raise
    return destination


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check", help="check the supported static SVG subset")
    check.add_argument("--svg", required=True)
    save = commands.add_parser("snapshot", help="archive existing SVG, prompt and metadata without overwriting")
    for name in ("svg", "prompt", "metadata", "root", "revision"):
        save.add_argument("--" + name, required=True)
    save.add_argument("--parent")
    args = parser.parse_args(argv)
    try:
        if args.command == "check":
            result = check_svg(read_bytes(args.svg))
        else:
            path = snapshot(args.svg, args.prompt, args.metadata, args.root, args.revision, args.parent)
            result = {"ok": True, "revision_path": str(path), "checks": {"structural": "passed",
                      "visual": "unverified", "raster_alpha": "unverified"}, "user_acceptance": "unassessed"}
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0 if result["ok"] else 1
    except (ArchiveError, OSError, ValueError, UnicodeError, OverflowError, RecursionError) as exc:
        print(json.dumps({"ok": False, "issues": [str(exc)], "visual_review": "not_run",
                          "user_acceptance": "unassessed"}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
