"""Preserve the handed-off trial and corrected final geometry separately."""
import hashlib
import json
import shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]
prior=BASE/'paint-study/natural-fields-v6/main-fit/geometry-input'
assert prior.exists(),prior
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert digest(prior/'geometry.json')=='7772af7a8301b53d2bb024b0929e306ec43c38d5bcd81004bee4f4052b61f43b'
assert digest(HERE/'geometry.json')=='8c251ff7add8cefd0737b4e2d0586b8e961b17de33e83051d4b0b364a5bbfebd'
for dest in [HERE/'attempt-01',HERE/'final']:
    if dest.exists():raise ValueError('Snapshot is immutable; refusing overwrite')
shutil.copytree(prior,HERE/'attempt-01')
(HERE/'final').mkdir()
for p in HERE.iterdir():
    if p.is_file() and p.name!='freeze_snapshots.py':shutil.copyfile(p,HERE/'final'/p.name)
shutil.copytree(HERE/'masks',HERE/'final/masks')
index={'attempt_01':{'geometry':'attempt-01/geometry.json','sha256':digest(HERE/'attempt-01/geometry.json'),'status':'superseded; binary-mask retrace shortened tapered tips','preserved_from':'paint-study/natural-fields-v6/main-fit/geometry-input'},'final':{'geometry':'final/geometry.json','sha256':digest(HERE/'final/geometry.json'),'status':'geometry frozen for paint refit and parent review','change_from_attempt_01':'Two thin fold paths retain their direct finite cubics; underfold left contour explicitly follows face occlusion below y980.'},'not_claimed':'art acceptance, 99 percent similarity, independent skill generalization'}
(HERE/'snapshot-index.json').write_text(json.dumps(index,indent=2)+'\n')
print(json.dumps(index))
