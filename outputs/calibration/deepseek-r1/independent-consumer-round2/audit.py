from pathlib import Path
import sys,os,threading,json,hashlib,xml.etree.ElementTree as ET,datetime
threading.Timer(45,lambda:os._exit(124)).start()
R=Path(__file__).resolve().parent; repo=R.parents[3]
sys.path.insert(0,str(repo/'tools'))
from render_svg import render_svg_text,backend_info
from PIL import Image
import numpy as np
from scipy.ndimage import binary_erosion
svg=(R/'short.svg').read_text(encoding='utf-8'); root=ET.fromstring(svg)
before=ET.fromstring((R/'archive/revisions/r001/icon.svg').read_text(encoding='utf-8'))
ids=lambda t:{e.get('id'):ET.tostring(e,encoding='unicode') for e in t.iter() if e.get('id') and e.tag.split('}')[-1] not in ['g','defs']}
b=ids(before); a=ids(root); changed=[k for k in a if a[k]!=b.get(k)]
raw=np.asarray(Image.open(repo/'ref/subjects/deepseek/cetus-desktop/r1-clean-source-1280.png').convert('RGBA'))
out=np.asarray(Image.open(R/'preview-1280.png').convert('RGBA'))
# Fixed diagnostic region rule: reference non-background RGB >24, alpha >127;
# output foreground alpha >127. Never presented as human acceptance probability.
rm=(raw[:,:,:3].max(2)>24)&(raw[:,:,3]>127); om=out[:,:,3]>127
union=rm|om
comp=lambda z:z[:,:,:3].astype(float)*(z[:,:,3:4]/255)+15*(1-z[:,:,3:4]/255)
err=np.abs(comp(out)-comp(raw)).mean(2)
inside=binary_erosion(om,iterations=3,border_value=0)
check={'svg_sha256':hashlib.sha256(svg.encode()).hexdigest(),'renderer':backend_info(),
 'canonical_png_matches':{str(n):render_svg_text(svg,n)==(R/f'preview-{n}.png').read_bytes() for n in [1280,128,48,24]},
 'revision_changed_leaf_ids':changed,'unchanged_leaf_ids':len(a)-len(changed),
 'static_archive_check':'r001 and r002 passed documented archive helper',
 'structure':{'paths':sum(e.tag.endswith('}path') for e in root.iter()),'ellipses':sum(e.tag.endswith('}ellipse') for e in root.iter()),'gradients':sum(e.tag.endswith('Gradient') for e in root.iter()),'images':sum(e.tag.endswith('}image') for e in root.iter()),'filters':sum(e.tag.endswith('}filter') for e in root.iter()),'patterns':sum(e.tag.endswith('}pattern') for e in root.iter())},
 'raster_alpha':{'upper_right':int(out[50,1200,3]),'fully_transparent_pixels':int((out[:,:,3]==0).sum()),'nonopaque_pixels_in_3px_eroded_foreground':int((inside&(out[:,:,3]!=255)).sum())},
 'diagnostics_not_acceptance':{'mask_rule':'Reference max RGB >24 and alpha >127; output alpha >127; fixed 15 gray comparison background; no registration/no exclusions','foreground_iou':float((rm&om).sum()/union.sum()),'rgb_mae_over_foreground_union_0_255':float(err[union].mean()),'note':'Source-aided diagnostic only. Does not establish 99 percent, naturalness, whale identity, or human acceptance.'},
 'visual_review':{'r001':'Actually viewed 1280, 640 pair, exact 128/48/24 inspection board','r002':'Actually viewed 1280, 640 pair, exact 128/48/24 on light/dark/neutral backgrounds','status':'reviewed_with_unresolved_differences'},
 'user_acceptance':'unassessed',
 'resource_record':{'audit_pid':os.getpid(),'audit_ppid':os.getppid(),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'owned':True,'hard_timeout_seconds':45,'children_started':0,'persistent_processes_started':0}}
(R/'verification.json').write_text(json.dumps(check,ensure_ascii=False,indent=2),encoding='utf-8')
(R/'review.md').write_text('''# Independent consumer round 2 — result and limits

Only short was produced, as explicitly authorized for this calibration. Final candidate is r002. r001 SVG, code, actual prompt, metadata, previews and reports were preserved before one scoped correction. No third revision was made.

## Scope completed

- Read Aikon SKILL and relevant reference instructions, actual-viewed raw 1280 PNG and original 4096 PNG; supplied raw image remained both subject and style binding.
- Saved actual prompt before any drawing code. Generated real editable SVG from broad semantic cubic Bézier paths and continuous local gradients. No embedded raster, pattern, filter, external resource, palette-quantization tracing, image model or network used.
- Reconstructed observed tilted face window, unequal projected capsule eyes, left sweep/center fringe/side locks, crescent identity crest, white headband and blue side accessory. Black background and any watermark excluded; no mouth/nose/body invented.
- Rendered real 1280/128/48/24 PNGs and actually viewed both revisions at large and icon sizes on several backgrounds. Final SVG itself has alpha and no presentation background.
- Static archive helper passed for r001 and r002, with raw input hashes and parent manifest. Source and PNG canonical rerender comparisons are recorded separately in verification.json.

## Observed unresolved differences

This is a visually reviewed draft, not a 99-percent or human-accepted reconstruction. Hair crown, central lock and long-lock contour/color transitions remain approximate; the narrow center-curl fold differs from raw; several white fabric lobe turns and rear trim have flatter broad treatment; subtle eye rims and inner light distribution remain approximate. Canvas corner curve was independently approximated, not extracted exactly from alpha. These differences remain visible in the raw/candidate comparison and were not excluded from diagnostics.

The prompt used the user-bound whale identity description without external research. It preserves the observed crescent/blue/accessory form but does not independently establish a canonical whale-design interpretation. A single same-model, source-aided consumer run does not establish transfer to other subjects or models. Short/full distinction was deliberately outside this single-short scope.

## Revision evidence

Actual r001 view showed an unsupported dark triangular detour in left-sweep, plus lower face remaining too cream. r002 changes only left-sweep curve and face-field gradient. Existing eyes, main head contours, identity crest, accessories, all other gradients and crop remain byte-identical by leaf ID comparison. This improves those two discrepancies, not the entire accuracy target.

## Reproduce

Run existing .local/ci-venv/Scripts/python.exe on this directory's draw.py. It uses only allowed tools/render_svg.py plus Pillow/numpy and writes within this directory. draw.py and audit.py have hard 45-second watchdogs; finalize.py also has a 45-second watchdog and 15-second subprocess timeouts. finalize.py records the historical one-time archive sequence and is not intended to rerun into existing archive revision IDs. Archived draw.py files preserve the exact historical code; their ROOT requires restoration into this output root to replay. No install/Git/network/browser process was used. No persistent process was started.

Read-only PowerShell file reads and the initial process inventory completed in under one second, but their tool schema did not expose a hard timeout and no separate watchdog wrapped those early reads; the explicit hard-timeout discipline was applied to generator/finalizer/auditor execution. This procedural limitation is disclosed rather than claimed compliant retroactively.
''',encoding='utf-8')
with (R/'read-log.md').open('a',encoding='utf-8') as f:
 f.write('\n23. r002 own preview-1280.png, inspection-board.png, reference-comparison.png — actual view_image after sole correction.\n24. Own archived r001 SVG and final SVG — leaf-ID comparison; own preview PNGs — canonical rerender byte comparison and alpha diagnostics. Raw reference — fixed-background, fixed-threshold diagnostic comparison with no alignment or exclusion.\n25. scipy.ndimage.binary_erosion — installed general numeric library, not repository drawing module.\n')
print(json.dumps(check,ensure_ascii=False,indent=2),flush=True)
os._exit(0)
