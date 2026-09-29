"""Freeze the existing fitter with explicit clean-source handling for v4 only."""
from pathlib import Path
import hashlib
import json

HERE=Path(__file__).resolve().parent
base=HERE.parent/"fit_fields.py"
code=base.read_text(encoding="utf-8")
replacements=[
    ('    mask[1196:1254, 1082:1256] = True\n',''),
    ('    # Fixed location of visible user-source watermark, not derived from error.\n    # This rectangle deliberately includes the antialiased logo glyph boundary.\n',
     '    # Clean-source v4: null means no exclusion; never restore the old ROI.\n'),
    ('    manifest=json.loads(manifest_bytes.decode("utf-8-sig"))\n',
     '    manifest=json.loads(manifest_bytes.decode("utf-8-sig"))\n    if manifest.get("reference_sha256") != hashlib.sha256(source.read_bytes()).hexdigest():\n        raise ValueError("source/geometry reference hash mismatch")\n    if manifest.get("watermark_uncertainty_mask") is not None:\n        raise ValueError("clean-source v4 forbids watermark exclusion")\n'),
    ('"source":"ref/user-mode/r1.png",', '"source":source.as_posix(),'),
    ('else "default_fixed_rectangle",','else None,'),
    ('output/"watermark-exclusion.png"','output/"exclusion-mask.png"'),
    ('"r1 source (watermark unchanged)"','"verified clean source (no watermark exclusion)"'),
    ('        field,stats,use=fit_field(rgb,mask,exclusion,simplicity_tolerance=tolerance)\n',
     '        if region["id"] == "hair-center-left-crease":\n            # A 173-pixel true thin crease has no 2-pixel-eroded interior.\n            # Model as one solid from the complete visible line; do not invent\n            # a gradient or omit its error from the record.\n            field,stats,use=fit_field(rgb,mask,exclusion,edge_pixels=0,allowed=["solid"],simplicity_tolerance=tolerance)\n            stats["thin_line_exception"] = {"reason":"fixed 2px erosion leaves zero pixels", "model":"solid only", "evaluation":"all visible line pixels", "limitation":"source AA may affect inferred line color"}\n        else:\n            field,stats,use=fit_field(rgb,mask,exclusion,simplicity_tolerance=tolerance)\n'),
]
for old,new in replacements:
    if code.count(old)!=1:
        raise ValueError(f"expected exactly one code anchor: {old[:80]}")
    code=code.replace(old,new)
target=HERE/"fit_fields_v4.py"
target.write_text(code,encoding="utf-8")
(HERE/"code-provenance.json").write_text(json.dumps({
    "base_file":"../fit_fields.py", "base_sha256":hashlib.sha256(base.read_bytes()).hexdigest(),
    "v4_file":"fit_fields_v4.py", "v4_sha256":hashlib.sha256(target.read_bytes()).hexdigest(),
    "changes":["null exclusion is zero pixels", "assert new source hash matches geometry",
               "reject any watermark mask", "record actual source path", "rename zero exclusion evidence",
               "one true thin crease uses all visible pixels and a solid-only model; all errors reported"]
},indent=2),encoding="utf-8")
print("prepared",target.name,flush=True)
