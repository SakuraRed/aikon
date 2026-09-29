#!/usr/bin/env python3
"""Compose an immutable SVG revision from semantic curves and analytic paint.

This exporter uses Python's standard library only. It neither loads a bitmap nor
fits a picture. The source-assisted calibration inputs are recorded separately.
"""
import argparse
import hashlib
import json
from pathlib import Path
from xml.sax.saxutils import escape


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rgb(values):
    if len(values) != 3 or not all(0 <= v <= 255 for v in values):
        raise ValueError("Expected three bounded sRGB channels")
    return "rgb(" + ",".join(f"{v / 255 * 100:.5f}%" for v in values) + ")"


def paint(field, identifier):
    if field["kind"] == "solid":
        return "", rgb(field["rgb"])
    stops = field["stops"]
    if not 2 <= len(stops) <= 5:
        raise ValueError("Analytic fields require two to five stops")
    tags = "".join(f'<stop offset="{s["offset"]:.5f}" stop-color="{rgb(s["rgb"])}"/>' for s in stops)
    common = f'id="{identifier}" gradientUnits="userSpaceOnUse" color-interpolation="sRGB"'
    if field["kind"] == "linear":
        a, b = field["from"], field["to"]
        definition = f'<linearGradient {common} x1="{a[0]:.5f}" y1="{a[1]:.5f}" x2="{b[0]:.5f}" y2="{b[1]:.5f}">{tags}</linearGradient>'
    elif field["kind"] == "radial":
        cx, cy = field["center"]
        rx, ry = field["radii"]
        if min(rx, ry) <= 0:
            raise ValueError("Positive gradient radii required")
        definition = f'<radialGradient {common} cx="0" cy="0" r="1" gradientTransform="translate({cx:.5f} {cy:.5f}) scale({rx:.5f} {ry:.5f})">{tags}</radialGradient>'
    else:
        raise ValueError("Unsupported field")
    return definition, f"url(#{identifier})"


def path(region, fill, extra="", identifier=None):
    identifier = identifier or region["id"]
    return f'<path id="{escape(identifier)}" d="{escape(region["d"])}" fill-rule="{region.get("fill_rule", "evenodd")}" fill="{fill}" {extra}/>'


def assemble(geometry_path, fields_path, prompt_path, output):
    geometry = json.loads(geometry_path.read_text(encoding="utf-8-sig"))
    fields = json.loads(fields_path.read_text(encoding="utf-8-sig"))
    if fields["geometry_manifest_sha256"] != digest(geometry_path):
        raise ValueError("Paint fitted to a different geometry manifest")
    if geometry["reference_sha256"] != fields["source_sha256"]:
        raise ValueError("Different source references")
    if geometry["canvas"] != {"width": 1280, "height": 1280}:
        raise ValueError("This calibration uses the unchanged 1280 canvas")
    if output.exists() and any(output.iterdir()):
        raise ValueError("Revision directory must be new; no overwrite")
    output.mkdir(parents=True, exist_ok=True)
    palettes = {item["id"]: item["field"] for item in fields["palette"]}
    regions = sorted(geometry["regions"], key=lambda region: region["z"])
    parents = {item["id"]: item for item in geometry["underpaints"]}
    definitions, fills = [], {}
    for identifier, field in palettes.items():
        definition, fill = paint(field, "paint-" + identifier)
        definitions.append(definition)
        fills[identifier] = fill
    definitions.append('<clipPath id="clip-face">' + path(parents["face-underpaint"], "white", identifier="face-support-clip") + '</clipPath>')
    body = ['<g id="material-foundations">']
    backing = [("subject-underpaint", "hair-front-main"), ("face-underpaint", "face"),
               ("frill-underpaint", next(key for key in fills if key.startswith("frill-fold"))),
               ("blue-underpaint", "hair-front-main"), ("bow-underpaint", "bow-left")]
    for parent_id, paint_id in backing:
        body.append(path(parents[parent_id], fills[paint_id]))
    body.append('</g><g id="visible-material-surfaces">')
    for region in regions:
        identifier = region["id"]
        if identifier.startswith("eye-"):
            # A narrow source-observed warm outer rim, not a white specular spot.
            # Three concentric low-amplitude strokes approximate its finite falloff.
            body.append(f'<g id="{identifier}-rim" clip-path="url(#clip-face)">')
            for width, opacity in ((10, .10), (8, .35), (6, .80), (4, .90)):
                body.append(path(region, "none", f'stroke="#fffefc" stroke-width="{width}" stroke-opacity="{opacity}" stroke-linejoin="round"', identifier=f'{identifier}-warm-rim-{width}'))
            body.append('</g>')
            body.append(path(region, fills[identifier]))
            definitions.append(f'<clipPath id="clip-{identifier}">' + path(region, "white", identifier=identifier + '-clip-path') + '</clipPath>')
            # Clip a centered stroke to the original contour, so it cannot expand
            # the eye silhouette or silently turn the capsule into an ellipse.
            body.append(path(region, "none", f'stroke="#1b203b" stroke-width="4.0" stroke-opacity="0.50" clip-path="url(#clip-{identifier})"', identifier=identifier + '-inner-transition'))
            body.append(path(region, "none", f'stroke="#0f122b" stroke-width="2.0" clip-path="url(#clip-{identifier})"', identifier=identifier + '-inner-rim'))
        else:
            body.append(path(region, fills[identifier]))
    body.append('</g>')
    svg = '<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="1280" viewBox="0 0 1280 1280">\n<title>DeepSeek r1 semantic short calibration</title>\n<desc>Source-assisted editable vector study. Transparent canvas. Not user accepted.</desc>\n<defs>' + ''.join(definitions) + '</defs>\n' + '\n'.join(body) + '\n</svg>\n'
    (output / "short.svg").write_text(svg, encoding="utf-8")
    for source, name in ((geometry_path, "geometry.json"), (fields_path, "paint-fields.json"), (prompt_path, "short.prompt.zh-CN.md"), (Path(__file__), "assemble.py")):
        (output / name).write_bytes(source.read_bytes())
    manifest = {"schema": "aikon.r1-calibration-revision.v1", "reference_sha256": geometry["reference_sha256"],
                "geometry_sha256": digest(geometry_path), "paint_fields_sha256": digest(fields_path),
                "prompt_sha256": digest(prompt_path), "exporter_sha256": digest(Path(__file__)),
                "svg_sha256": digest(output / "short.svg"), "status": "draft",
                "scope": "source-assisted single short calibration; not independent skill generalization",
                "eye_rim": "finite warm outer band and clipped dark inner band; source-observed, manually calibrated",
                "human_acceptance": None, "similarity_99_percent": "not_assessed"}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "svg_sha256": manifest["svg_sha256"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geometry", type=Path, required=True)
    parser.add_argument("--fields", type=Path, required=True)
    parser.add_argument("--prompt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assemble(args.geometry, args.fields, args.prompt, args.output)
