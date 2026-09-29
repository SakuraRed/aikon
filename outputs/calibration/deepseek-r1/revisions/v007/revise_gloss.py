"""Freeze a paint-only SVG patch, including its exact code and inputs."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main(output):
    base=HERE/'revisions/v006/short.svg'
    prompt=HERE/'revision-007.prompt.zh-CN.md'
    plan_path=HERE/'paint-study/gloss-detail-v7/trial-correction.json'
    code=HERE/'paint-study/gloss-detail-v7/gloss_paint.py'
    if output.exists() and any(output.iterdir()):raise ValueError('No overwrite')
    if sha(base)!='0e662b8789d71a5baf6e3f1ee4c27af3033a5e75c72ae63d99e7a40691a3c297':
        raise ValueError('Unexpected base revision')
    spec=importlib.util.spec_from_file_location('gloss_paint',code)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    svg,_=module.apply_gloss(base.read_text(encoding='utf-8'),json.loads(plan_path.read_text(encoding='utf-8')))
    output.mkdir(parents=True,exist_ok=True)
    (output/'short.svg').write_bytes(svg.encode('utf-8'))
    for source,name in ((base,'base.svg'),(prompt,'short.prompt.zh-CN.md'),(plan_path,'gloss-plan.json'),(code,'gloss_paint.py'),(Path(__file__),'revise_gloss.py'),(HERE/'revisions/v006/geometry.json','geometry.json'),(HERE/'revisions/v006/paint-fields.json','paint-fields.json')):
        (output/name).write_bytes(source.read_bytes())
    manifest={'schema':'aikon.r1-gloss-revision.v1','parent':'v006','base_svg_sha256':sha(base),
              'svg_sha256':sha(output/'short.svg'),'prompt_sha256':sha(prompt),'patch_sha256':sha(code),'plan_sha256':sha(plan_path),
              'scope':'source-assisted paint-only calibration; not independent Skill generation',
              'status':'draft','user_acceptance':None,'similarity_99_percent':'not_assessed'}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(manifest))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);main(p.parse_args().output)
