#!/usr/bin/env python3
"""Render a bounded, self-contained vector SVG using a pinned optional backend.

The authoring skill remains standard-library-only. This verification adapter
requires requirements-ci.txt and never fetches fonts, images or other resources.
The calling process must enforce its wall-clock timeout (CI does so explicitly).
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import xml.etree.ElementTree as ET


SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
XML_NS = "http://www.w3.org/XML/1998/namespace"
MAX_SVG_BYTES = 2_000_000
MAX_ELEMENTS = 10_000
MAX_DEPTH = 64
MAX_SIZE = 4096
ALLOWED_TAGS = {
    "svg", "g", "defs", "title", "desc", "metadata", "path", "rect",
    "circle", "ellipse", "line", "polyline", "polygon", "clipPath", "mask",
    "linearGradient", "radialGradient", "stop",
}
ALLOWED_ATTRIBUTES = {
    "id", "version", "viewBox", "width", "height", "preserveAspectRatio",
    "x", "y", "x1", "y1", "x2", "y2", "cx", "cy", "r", "rx", "ry",
    "fx", "fy", "fr", "d", "points", "transform", "fill", "fill-rule",
    "fill-opacity", "stroke", "stroke-width", "stroke-opacity", "stroke-linecap",
    "stroke-linejoin", "stroke-miterlimit", "stroke-dasharray", "stroke-dashoffset",
    "opacity", "clip-path", "clip-rule", "clipPathUnits", "mask", "maskUnits",
    "maskContentUnits", "mask-type", "gradientUnits", "gradientTransform",
    "spreadMethod", "offset", "stop-color", "stop-opacity", "color", "style",
    "href", "display", "visibility", "vector-effect", "shape-rendering", "role",
    "color-interpolation", "overflow",
}
STYLE_PROPERTIES = {
    "fill", "fill-rule", "fill-opacity", "stroke", "stroke-width",
    "stroke-opacity", "stroke-linecap", "stroke-linejoin", "stroke-miterlimit",
    "stroke-dasharray", "stroke-dashoffset", "opacity", "clip-path", "clip-rule",
    "mask", "mask-type", "stop-color", "stop-opacity", "color", "display",
    "visibility", "vector-effect", "shape-rendering", "color-interpolation",
    "overflow",
}
ID_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_.:-]*\Z")
URL_PATTERN = re.compile(r"url\(\s*(['\"]?)(#[A-Za-z_][A-Za-z0-9_.:-]*)\1\s*\)\Z", re.I)


def _local_reference(value, references):
    if not value.startswith("#") or not ID_PATTERN.fullmatch(value[1:]):
        raise ValueError("Only local #id references are allowed")
    references.add(value[1:])


def _paint_value(value, references):
    # Escapes/comments could disguise CSS url() or @import from a string check.
    if any(token in value for token in ("\\", "/*", "*/", "@", "{", "}")):
        raise ValueError("CSS escapes, comments and at-rules are not supported")
    if "url" in value.lower():
        match = URL_PATTERN.fullmatch(value.strip())
        if not match:
            raise ValueError("Paint references must use a single local url(#id)")
        _local_reference(match.group(2), references)


def validate_svg(svg_text):
    """Return parsed safe vector markup; gradients and clips may reference defs.

    This is a deliberately limited icon profile, not a general SVG sanitizer.
    Unknown elements and attributes fail closed. Fonts, images (including data
    URLs), stylesheets, filters, patterns, animation and links are unsupported.
    """
    if not isinstance(svg_text, str) or not svg_text.strip():
        raise ValueError("SVG source must be nonempty UTF-8 text")
    if len(svg_text.encode("utf-8")) > MAX_SVG_BYTES:
        raise ValueError("SVG exceeds the 2 MB validation budget")
    if re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", svg_text, re.I):
        raise ValueError("DTD and entity declarations are forbidden")
    if re.search(r"<\?(?!xml(?:\s|\?>))", svg_text, re.I):
        raise ValueError("Processing instructions are forbidden")
    try:
        root = ET.fromstring(svg_text)
    except ET.ParseError as error:
        raise ValueError("Invalid SVG XML: " + str(error)) from error
    if root.tag != "{" + SVG_NS + "}svg":
        raise ValueError("Root must be svg in the SVG namespace")
    ids = set()
    references = set()
    count = 0
    pending = [(root, 0)]
    while pending:
        element, depth = pending.pop()
        count += 1
        if count > MAX_ELEMENTS or depth > MAX_DEPTH:
            raise ValueError("SVG exceeds the element or nesting budget")
        if not element.tag.startswith("{" + SVG_NS + "}"):
            raise ValueError("Foreign namespaces are forbidden")
        tag = element.tag.split("}", 1)[1]
        if tag not in ALLOWED_TAGS:
            raise ValueError("Unsupported or active SVG element: " + tag)
        for attribute, value in element.attrib.items():
            if attribute.startswith("{"):
                if attribute == "{" + XLINK_NS + "}href":
                    attribute = "href"
                elif attribute == "{" + XML_NS + "}space" and value in {"default", "preserve"}:
                    continue
                else:
                    raise ValueError("Namespaced attribute is not supported: " + attribute)
            if attribute.lower().startswith("on"):
                raise ValueError("Event attributes are forbidden")
            if attribute not in ALLOWED_ATTRIBUTES and not attribute.startswith(("data-", "aria-")):
                raise ValueError("Unsupported SVG attribute: " + attribute)
            if attribute == "id":
                if not ID_PATTERN.fullmatch(value) or value in ids:
                    raise ValueError("SVG ids must be valid and unique")
                ids.add(value)
            elif attribute == "href":
                if tag not in {"linearGradient", "radialGradient"}:
                    raise ValueError("href is only supported for local gradient inheritance")
                _local_reference(value, references)
            elif attribute == "style":
                for declaration in value.split(";"):
                    if not declaration.strip():
                        continue
                    property_name, separator, property_value = declaration.partition(":")
                    if not separator or property_name.strip().lower() not in STYLE_PROPERTIES:
                        raise ValueError("Unsupported inline style property")
                    _paint_value(property_value.strip(), references)
            elif not attribute.startswith(("data-", "aria-")):
                _paint_value(value, references)
        pending.extend((child, depth + 1) for child in element)
    missing = references - ids
    if missing:
        raise ValueError("Unresolved local references: " + ", ".join(sorted(missing)))
    return root


def backend_info():
    try:
        import resvg_py
    except ImportError as error:
        raise RuntimeError("Optional renderer missing; install requirements-ci.txt in an isolated environment") from error
    if resvg_py.__version__ != "0.5.0":
        raise RuntimeError("Verification requires resvg-py==0.5.0; backend version differs")
    return {"binding": "resvg-py", "version": resvg_py.__version__, "resvg": resvg_py.__resvg_version__}


def render_svg_text(svg_text, size=512):
    """Return PNG bytes fitting within size x size, preserving aspect ratio."""
    if isinstance(size, bool) or not isinstance(size, int) or not 1 <= size <= MAX_SIZE:
        raise ValueError("Render size must be an integer between 1 and 4096")
    root = validate_svg(svg_text)
    backend_info()
    import resvg_py

    # Serialize the inspected tree so ignored XML processing nodes cannot reach
    # the backend. No source path, resource directory or font path is supplied.
    markup = ET.tostring(root, encoding="unicode")
    png = resvg_py.svg_to_bytes(
        svg_string=markup, width=size, height=size, background=None,
        skip_system_fonts=True, resources_dir=None, font_files=None,
        font_dirs=None, shape_rendering="geometric_precision",
    )
    if png[:8] != b"\x89PNG\r\n\x1a\n" or png[12:16] != b"IHDR":
        raise RuntimeError("Renderer did not return a PNG")
    width, height = struct.unpack(">II", png[16:24])
    if png[24:26] != b"\x08\x06" or not 1 <= max(width, height) <= size:
        raise RuntimeError("Renderer did not return bounded 8-bit RGBA output")
    return png


def render_svg_file(input_path, output_path, size=512):
    """Render an SVG file and return small reproducibility metadata."""
    input_path, output_path = Path(input_path), Path(output_path)
    if input_path.resolve() == output_path.resolve():
        raise ValueError("Input SVG and output PNG paths must differ")
    with input_path.open("rb") as source:
        raw = source.read(MAX_SVG_BYTES + 1)
    if len(raw) > MAX_SVG_BYTES:
        raise ValueError("SVG exceeds the 2 MB validation budget")
    png = render_svg_text(raw.decode("utf-8-sig"), size=size)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(png)
    width, height = struct.unpack(">II", png[16:24])
    return {
        "backend": backend_info(), "width": width, "height": height,
        "mode": "RGBA", "source_sha256": hashlib.sha256(raw).hexdigest(),
        "png_sha256": hashlib.sha256(png).hexdigest(),
        "background": "unpainted; source alpha preserved",
        "visual_acceptance": "not_evaluated",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--size", type=int, default=512)
    args = parser.parse_args(argv)
    try:
        report = render_svg_file(args.input, args.output, args.size)
    except (ValueError, RuntimeError, OSError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps({"ok": True, **report}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
