from pathlib import Path
import hashlib
import json

HERE=Path(__file__).resolve().parent
base=HERE.parent/"material-fit-v4/fit_fields_v4.py"
code=base.read_text(encoding="utf-8")
changes=[
    ('    output.mkdir(parents=True, exist_ok=True)\n',
     '    output.mkdir(parents=True, exist_ok=True)\n    source_label=source.as_posix()\n    source_bytes=source.read_bytes()\n    source_snapshot=output/"source-input.png"\n    source_snapshot.write_bytes(source_bytes)\n    source=source_snapshot\n'),
    ('"source":source.as_posix(),','"source":source_label,"source_snapshot_file":"source-input.png",'),
    ('# Clean-source v4:', '# Clean-source v5:'),
    ('clean-source v4 forbids watermark exclusion','clean-source v5 forbids watermark exclusion'),
]
for old,new in changes:
    if code.count(old)!=1:
        raise ValueError(f"expected one code anchor {old[:80]}")
    code=code.replace(old,new)
target=HERE/"fit_fields_v5.py"
target.write_text(code,encoding="utf-8")
(HERE/"code-provenance.json").write_text(json.dumps({
    "base_file":"../material-fit-v4/fit_fields_v4.py", "base_sha256":hashlib.sha256(base.read_bytes()).hexdigest(),
    "v5_file":"fit_fields_v5.py", "v5_sha256":hashlib.sha256(target.read_bytes()).hexdigest(),
    "fitting_policy":"unchanged from v4; source snapshot added; source and geometry actually rerun"
},indent=2),encoding="utf-8")
print("prepared",target.name,flush=True)
