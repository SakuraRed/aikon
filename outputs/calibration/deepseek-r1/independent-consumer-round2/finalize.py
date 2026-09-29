from pathlib import Path
import sys,os,json,hashlib,subprocess,threading,shutil,datetime
threading.Timer(45,lambda:os._exit(124)).start()
R=Path(__file__).resolve().parent; repo=R.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=repo/'ref/subjects/deepseek/cetus-desktop/r1-clean-source-1280.png'
metadata={
 'schema':'aikon.direct-svg.metadata.v1','round_id':'deepseek-r1-independent-consumer-round2','profile':'short','subject':'DeepSeek, user-bound CETUS reference',
 'sources':[{'role':'both','location':'ref/subjects/deepseek/cetus-desktop/r1-clean-source-1280.png','rights_status':'User-supplied local research reference; redistribution rights unknown','sha256':sha(source),'acquired_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'purpose':'Independent reference reconstruction','visual_selection_reason':'User explicitly bound the raw image as identity and visual target'},{'role':'both','location':'ref/subjects/deepseek/cetus-desktop/CETUS-ico.original.png','rights_status':'User-supplied local research reference; redistribution rights unknown','sha256':sha(repo/'ref/subjects/deepseek/cetus-desktop/CETUS-ico.original.png'),'purpose':'High-resolution visual inspection'}],
 'decisions':[{'id':'profile','value':'short only; overrides default paired output for this calibration','origin':'user'},{'id':'background','value':'transparent','origin':'user'},{'id':'watermark','value':'none','origin':'user'},{'id':'target','value':'Reconstruct reference as closely as possible; 99 percent is requested target, not achieved claim','origin':'user'},{'id':'method','value':'Editable semantic cubic Bezier paths and continuous local gradients','origin':'agent_default'},{'id':'projection','value':'Preserve unequal projected capsule eyes and visible face/fringe relationship','origin':'reference_observation'}],
 'unresolved_questions':['No independently validated quantitative 99 percent similarity criterion','Precise whale-identity semantics are user-bound; external identity research excluded by brief'],
 'changes':{'summary':'Initial independent direct-SVG reconstruction','targets':['face','eyes','hair','identity crest','headband','accessory','paint'],'preserved':['reference canvas framing','two visible capsule eyes','transparent background']},
 'provenance':{'method':'Direct SVG from manual semantic contour observation and limited raw-pixel sampling','tool':'draw.py','version':'r001','model':None,'script_sha256':sha(R/'draw.py')},
 'notes':'Source-aided independent-consumer calibration; no existing answer SVG or prior coordinates read. Not user accepted.'}
(R/'metadata-r001.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
helper=repo/'skills/aikon/scripts/archive_svg.py'
def call(args):
 p=subprocess.run([sys.executable,str(helper),*map(str,args)],capture_output=True,text=True,encoding='utf-8',timeout=15)
 if p.returncode: raise RuntimeError(p.stdout+p.stderr)
 return p.stdout
out=call(['snapshot','--svg',R/'short.svg','--prompt',R/'actualprompt.md','--metadata',R/'metadata-r001.json','--root',R/'archive','--revision','r001'])
(R/'archive-check-r001.json').write_text(out,encoding='utf-8')
for name in ['draw.py','preview-1280.png','preview-128.png','preview-48.png','preview-24.png','inspection-board.png','reference-comparison.png','render-report.json']:
 shutil.copyfile(R/name,R/'archive/revisions/r001'/name)
(R/'revision-prompt.md').write_text('''# Actual revision prompt — r002 (single permitted correction)
Base: archived r001 exact SVG/source/PNG bytes.
Evidence: actual 1280 rendering shows an unsupported angular dark wedge above left-to-center fringe around x306..354/y358..403; actual side-by-side shows face bottom is too cream and insufficiently pink compared with raw.
Targets: remove that angular detour in left-sweep curve only; compress face radial field vertical scale from 720 to 500 while preserving light center and slightly pink far color. Keep all eye shapes, placements, major covering contours, crest, accessories, layer count, transparency and canvas unchanged.
Additional observed issue kept unresolved: center-curl inner narrow fold and cloth rim differ from raw, eye gloss is approximate. No further iterative generation permitted this run.
''',encoding='utf-8')
s=(R/'draw.py').read_text(encoding='utf-8')
s=s.replace('C 430 290 372 321 306 358 L 354 403','C 430 290 391 343 354 403')
s=s.replace("radial('face-field',405,885,720,720,[(0,'#fffffe'),(.25,'#fffaf5'),(.65,'#fff0e5'),(1,'#f8e6e5')])","radial('face-field',405,885,740,500,[(0,'#fffffe'),(.2,'#fffdf9'),(.6,'#fff0e5'),(1,'#f7e6e6')])")
(R/'draw.py').write_text(s,encoding='utf-8')
subprocess.run([sys.executable,str(R/'draw.py')],check=True,timeout=15)
metadata['changes']={'summary':'One evidence-based revision: remove unsupported left-fringe triangular detour and adjust face radial field vertical reach','targets':['left-sweep','face-field'],'preserved':['all other paths and gradients','all eyes','identity crest','accessories','crop']}
metadata['provenance']['version']='r002';metadata['provenance']['script_sha256']=sha(R/'draw.py')
(R/'metadata-r002.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
out=call(['snapshot','--svg',R/'short.svg','--prompt',R/'revision-prompt.md','--metadata',R/'metadata-r002.json','--root',R/'archive','--revision','r002','--parent','r001'])
(R/'archive-check-r002.json').write_text(out,encoding='utf-8')
for name in ['draw.py','preview-1280.png','preview-128.png','preview-48.png','preview-24.png','inspection-board.png','reference-comparison.png','render-report.json']:
 shutil.copyfile(R/name,R/'archive/revisions/r002'/name)
with (R/'read-log.md').open('a',encoding='utf-8') as f:
 f.write('''\n14. references/calibration.md — complete reread, including reference-reconstruction versus style-transfer rules.
15. references/prompts/source-short.zh-CN.md — complete read; user reconstruction/alpha/short-only overrides recorded.
16. tools/render_svg.py — complete read, imported only this allowed rendering module.
17. references/natural-gloss-v2.md, paint-antipatterns.md, validation.md — complete reread after initial truncation.
18. raw r1 PNG — Pillow limited pixel samples and alpha observation; no color quantization or automated fragmented tracing.
19. Own generated reference-comparison.png, inspection-board.png, preview-1280.png — actual view_image; evidence for single revision.
20. skills/aikon/scripts/archive_svg.py — executed documented CLI for r001/r002 static check and immutable snapshots; source not read, internal imports limited to skill implementation.
21. Own draw.py and outputs — read for preservation, one scoped edit, rerender and archival.
22. Optional compose_materials helper schema was received in a message from its author; no file read, import, call, geometry or material output received.
No assets/examples geometry or PNG was viewed: strong same-subject reconstruction takes precedence; README only read. No other repository module, prior output, fixture, calibration report, Git state or network accessed.\n''')
print('r001 preserved; r002 generated and statically archived',flush=True)
os._exit(0)
