"""Create the calibration sampling grid; preserve downloaded and user originals.

The high-resolution source supplies every RGBA pixel, including the formerly
watermarked area and its actual presentation alpha. This is uniform sampling,
not an inpainting model. Original user r1 is retained only as provenance.
"""
import hashlib
import json
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
UPSTREAM_SHA = '4da172c683d7981e170fc90d8e7d1bd8b4e7107799cdc12338859c82e6fb44fd'
R1_SHA = '5a16fe96fab6c06548c87250539739cc4d6dac5e1fed6628f65890a76683817e'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    upstream=HERE/'CETUS-ico.original.png'
    r1=ROOT/'ref/user-mode/r1.png'
    if sha(upstream)!=UPSTREAM_SHA or sha(r1)!=R1_SHA:
        raise ValueError('Reference bytes changed')
    source=Image.open(upstream).convert('RGBA')
    reference=Image.open(r1).convert('RGBA')
    if source.size!=(4096,4096) or reference.size!=(1280,1280):
        raise ValueError('Unexpected canvas')
    result=source.resize(reference.size,Image.Resampling.LANCZOS)
    # The downloaded source already has the presentation alpha. Keeping its
    # own RGBA avoids importing old watermark coverage or clipping it twice.
    # Earlier normalization contracts are retained as superseded studies.
    output=HERE/'r1-clean-source-1280.png'
    result.save(output)
    contract={'schema':'aikon.r1-upstream-reference.v4',
              'upstream_sha256':UPSTREAM_SHA,'user_r1_sha256':R1_SHA,
              'working_reference':output.name,'working_reference_sha256':sha(output),
              'upstream_size':[4096,4096],'working_size':[1280,1280],
              'sampling':'Pillow LANCZOS; exact full-canvas uniform 4096 to1280; no registration',
              'alpha':'true upstream alpha uniformly sampled with RGB; no user-r1 alpha inherited',
              'rgb':'upstream only; no inpainting, redraw, local correction or denoising',
              'watermark_exclusion':None,'original_files_changed':False,
              'acceptance':'source selection and normalization only; not Skill quality certification'}
    (HERE/'reference-contract-v4.json').write_text(json.dumps(contract,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(contract))

if __name__=='__main__':main()
