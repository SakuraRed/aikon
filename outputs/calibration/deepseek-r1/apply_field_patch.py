"""Apply one source- and geometry-bound paint patch without modifying history."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
base=HERE/'paint-study/material-fit-v5/fields.json'
patch_path=HERE/'paint-study/right-face-crease-patch-v1/patch.json'
document=json.loads(base.read_text(encoding='utf-8'))
patch=json.loads(patch_path.read_text(encoding='utf-8'))
if document['source_sha256']!=patch['source_sha256'] or document['geometry_manifest_sha256']!=patch['geometry_manifest_sha256']:
    raise ValueError('Patch input binding mismatch')
matches=[p for p in document['palette'] if p['id']==patch['id']]
if len(matches)!=1:raise ValueError('Unique material required')
material=matches[0]
material['previous_stats']=material.pop('stats')
material['field']=patch['field']
material['stats']=patch['new_errors']
material['stats_note']='Full visible mask and fixed old interior reported separately; see patch evidence'
document['patch']={'path':patch_path.relative_to(HERE).as_posix(),'sha256':hashlib.sha256(patch_path.read_bytes()).hexdigest(),'base_sha256':hashlib.sha256(base.read_bytes()).hexdigest()}
output=HERE/'paint-study/right-face-crease-patch-v1/patched-fields.json'
if output.exists():raise ValueError('No overwrite')
output.write_text(json.dumps(document,indent=2)+'\n',encoding='utf-8')
print(output)
