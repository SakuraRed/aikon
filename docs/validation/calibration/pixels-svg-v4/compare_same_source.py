"""Same-source approximation loss only. No perceptual/art acceptance score."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def worker(args):
    os.environ.setdefault('OMP_NUM_THREADS', '1')
    os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
    import numpy as np
    from PIL import Image
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    a_path, b_path = Path(args.png).resolve(), Path(args.svg_render).resolve()
    a_img, b_img = Image.open(a_path).convert('RGBA'), Image.open(b_path).convert('RGBA')
    if a_img.size != b_img.size:
        raise ValueError('Same-source loss requires identical native canvas sizes; no implicit registration or resizing.')
    a = np.asarray(a_img, dtype=np.float32) / 255
    b = np.asarray(b_img, dtype=np.float32) / 255
    aa, ba = a[:, :, 3], b[:, :, 3]
    am, bm = aa >= (128/255), ba >= (128/255)
    union, intersection = am | bm, am & bm
    ap, bp = a[:, :, :3] * aa[:, :, None], b[:, :, :3] * ba[:, :, None]
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    difference = np.abs(ap-bp)*255
    result = {
        'schema': 'aikon.same-source-approximation.v1', 'art_score': None, 'gold': False, 'user_accepted': False,
        'source_png': str(a_path), 'svg_render_png': str(b_path),
        'source_png_sha256': hashlib.sha256(a_path.read_bytes()).hexdigest(),
        'svg_render_sha256': hashlib.sha256(b_path.read_bytes()).hexdigest(),
        'native_size': list(a_img.size), 'resizing': 'none', 'registration': 'none',
        'alpha_threshold_0_255': 128,
        'binary_alpha_iou': float(intersection.sum()/max(1,union.sum())),
        'binary_alpha_intersection_pixels': int(intersection.sum()), 'binary_alpha_union_pixels': int(union.sum()),
        'source_only_alpha_pixels': int((am & ~bm).sum()), 'svg_only_alpha_pixels': int((bm & ~am).sum()),
        'soft_alpha_iou': float(np.minimum(aa,ba).sum()/max(1e-12,float(np.maximum(aa,ba).sum()))),
        'alpha_mae_0_255': float(np.mean(np.abs(aa-ba))*255),
        'premultiplied_rgb_mae_0_255_all_canvas': float(difference.mean()),
        'premultiplied_rgb_mae_0_255_alpha_union': float(difference[union].mean()),
        'color_math': 'sRGB-encoded channel values; P=RGB*(alpha/255). No linear-light or perceptual conversion.',
        'composites': {},
        'interpretation': 'The SVG intentionally simplifies and redraws colors. These are same-source approximation losses, not art quality, style conformance, IP fidelity, or user acceptance.'
    }
    alpha_map = np.zeros((*am.shape,3), dtype=np.uint8)
    alpha_map[:] = [25,25,25]
    alpha_map[intersection] = [205,205,205]
    alpha_map[am & ~bm] = [240,40,140]
    alpha_map[bm & ~am] = [0,210,230]
    Image.fromarray(alpha_map).save(output/'same-source-alpha-map.png')
    result['alpha_map_legend'] = {'gray':'both foreground', 'pink':'PNG only', 'cyan':'SVG render only', 'dark':'both below alpha threshold'}
    fig, axes = plt.subplots(2,3,figsize=(12,8))
    for index,(name,channel) in enumerate([('white',255),('dark',32)]):
        background=np.full(3,channel/255,dtype=np.float32)
        ac=ap+(1-aa[:,:,None])*background
        bc=bp+(1-ba[:,:,None])*background
        error=np.abs(ac-bc)*255
        result['composites'][name]={'background_rgb_0_255':[channel]*3,
                                   'formula':'C=P+(1-alpha)*background',
                                   'rgb_mae_0_255_all_canvas':float(error.mean()),
                                   'rgb_mae_0_255_alpha_union':float(error[union].mean()),
                                   'per_channel_rgb_mae_0_255':error.mean(axis=(0,1)).tolist()}
        axes[index,0].imshow(np.clip(ac,0,1))
        axes[index,1].imshow(np.clip(bc,0,1))
        plot=axes[index,2].imshow(error.mean(axis=2),cmap='magma',vmin=0,vmax=64)
        fig.colorbar(plot,ax=axes[index,2],fraction=.046,pad=.02)
        for j in range(3): axes[index,j].set_axis_off()
        axes[index,0].set_title('Diagnostic PNG — '+name)
        axes[index,1].set_title('Actual SVG render v4 — '+name)
        axes[index,2].set_title('Mean absolute RGB delta (0–255)')
    fig.suptitle('Same-source approximation: colors intentionally simplified; not an art score\nHeatmaps fixed at 0–64 for display (larger errors clipped only in the visualization)',fontsize=11)
    fig.tight_layout()
    fig.savefig(output/'same-source-rgb-comparison.png',dpi=150)
    plt.close(fig)
    (output/'same-source-loss.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k in ['native_size','binary_alpha_iou','soft_alpha_iou','alpha_mae_0_255','premultiplied_rgb_mae_0_255_all_canvas','composites']},ensure_ascii=False),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--png',required=True)
    parser.add_argument('--svg-render',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--_worker',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args._worker:
        worker(args)
        return 0
    command=[sys.executable,'-B','-X','utf8',str(Path(__file__).resolve()),*sys.argv[1:],'--_worker']
    started=time.monotonic()
    p=subprocess.Popen(command)
    record={'pid':p.pid,'parent_pid':os.getpid(),'cwd':os.getcwd(),'command':command,'hard_timeout_s':60,
            'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    print(json.dumps(record,ensure_ascii=False),flush=True)
    try:
        code=p.wait(timeout=60)
    except subprocess.TimeoutExpired:
        if os.name=='nt': subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,timeout=10)
        else: p.kill()
        p.wait(timeout=10)
        code=124
    record.update(exit_code=code,elapsed_s=time.monotonic()-started)
    output=Path(args.output).resolve()
    output.mkdir(parents=True,exist_ok=True)
    (output/'same-source-process.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return code


if __name__=='__main__': raise SystemExit(main())
