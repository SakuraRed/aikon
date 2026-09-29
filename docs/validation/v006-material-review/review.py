"""Offline, bounded diagnosis of the frozen v006 main-hair island only."""
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[key] = '1'


def worker(mode):
    import numpy as np
    from PIL import Image, ImageDraw
    from scipy import ndimage as ndi
    from tools import analyze_paint_fields as paint
    base = ROOT / 'outputs/calibration/deepseek-r1'
    rev = base / 'revisions/v006'
    geom = base / 'paint-study/natural-fields-v6/final-fit/geometry-input'
    source_path = ROOT / 'ref/subjects/deepseek/cetus-desktop/r1-clean-source-1280.png'
    assert hashlib.sha256(source_path.read_bytes()).hexdigest() == '60c234f594ad81319fa74bb4fa8392f10a125127d46bf1d3b47e618b25813da2'
    source = Image.open(source_path).convert('RGBA')
    candidate = Image.open(rev / 'comparison/candidate-render.png').convert('RGBA')
    mask = np.asarray(Image.open(geom / 'masks/hair-front-main.png').convert('L')) > 127
    contract = json.loads((rev / 'quality/paint-contract.json').read_text())
    contract['regions'] = [r for r in contract['regions'] if r['id'] == 'hair-front-main']
    masks = {'hair-front-main': mask}
    report, maps = paint.analyze_image(candidate, contract, masks)
    old = json.loads((rev / 'quality/paint.json').read_text())
    assert report['decoded_rgba_sha256'] == old['decoded_rgba_sha256']
    assert report['regions'][0] == next(r for r in old['regions'] if r['id'] == 'hair-front-main')
    rgb = np.asarray(maps['normalized'])[:, :, :3].astype(float)
    region = maps['regions']['hair-front-main']
    interior = ndi.binary_erosion(region, iterations=3)
    island = maps['islands']
    start = time.monotonic()
    result = {'scope': 'v006 hair-front-main only; diagnostic evidence, no gate override',
              'source_sha256': hashlib.sha256(source_path.read_bytes()).hexdigest(),
              'candidate_svg_sha256': hashlib.sha256((rev/'short.svg').read_bytes()).hexdigest(),
              'analyzer_sha256': hashlib.sha256((ROOT/'tools/analyze_paint_fields.py').read_bytes()).hexdigest(),
              'mask_sha256': hashlib.sha256((geom/'masks/hair-front-main.png').read_bytes()).hexdigest(),
              'rules': report['rules'], 'candidate_decoded_sha256': report['decoded_rgba_sha256'],
              'original_region_exactly_reproduced': True}

    def compact(rep):
        r = rep['regions'][0]
        return {'issues': rep['issues'], 'color_islands': r['color_islands'],
                'texture': r['texture'], 'texture_support_evidence': r['texture_support_evidence']}

    if mode == 'real':
        result['candidate'] = compact(report)
        ref_report, ref_maps = paint.analyze_image(source, contract, masks)
        result['source_with_candidate_mask_NOT_ground_truth'] = compact(ref_report)
        norm_ref = np.asarray(ref_maps['normalized'])[:, :, :3].astype(float)
        dist = ndi.distance_transform_edt(region)
        ring = ndi.binary_dilation(island, iterations=7) & region & ~island
        result['island_pixels'] = {'analysis_bbox_xyxy': [3,623,21,671],
          'source_canvas_bbox_xyxy': [3.75,778.75,26.25,838.75],
          'distance_to_material_boundary_analysis_px': {'min': float(dist[island].min()), 'max': float(dist[island].max()), 'median': float(np.median(dist[island]))},
          'candidate_rgb_median': np.median(rgb[island],axis=0).tolist(),
          'candidate_rgb_min': rgb[island].min(axis=0).tolist(), 'candidate_rgb_max': rgb[island].max(axis=0).tolist(),
          'candidate_minus_source_rgb_median': np.median((rgb-norm_ref)[island],axis=0).tolist(),
          'candidate_source_rgb_rmse': float(np.sqrt(np.mean((rgb-norm_ref)[island]**2))),
          'ring_candidate_minus_source_rgb_median': np.median((rgb-norm_ref)[ring],axis=0).tolist()}
        # Actual rendered support is independent of the cached/source-derived raster mask.
        import xml.etree.ElementTree as ET
        from tools.paint_checks import render_image
        root = ET.fromstring((rev/'short.svg').read_text())
        defs = next(n for n in root if n.tag.endswith('defs'))
        support_path = next(n for n in defs.iter() if n.get('id')=='hair-front-main-material-clip')
        shell = ET.Element(root.tag, dict(root.attrib))
        shell.append(copy.deepcopy(support_path))
        shell[0].set('fill','white')
        support_image = render_image(ET.tostring(shell,encoding='unicode'),1280)
        actual = np.asarray(support_image.resize((1024,1024),Image.Resampling.LANCZOS))[:,:,3]>=254
        actual_dist = ndi.distance_transform_edt(actual)
        result['island_actual_svg_support'] = {'pixels_fully_covered_by_mainhair': int((island & actual).sum()),
          'pixels_outside_mainhair': int((island & ~actual).sum()),
          'min_actual_support_boundary_distance': float(actual_dist[island].min())}
        # Audit final compositing ownership, including all later occluders.
        owner_root=copy.deepcopy(root)
        def owner_walk(node, main=False, definition=False):
            definition=definition or node.tag.endswith('defs')
            main=main or node.get('id')=='hair-front-main'
            if not definition and node.tag.rsplit('}',1)[-1] in ('path','rect','circle','ellipse','polygon','polyline','line'):
                if node.get('fill','black')!='none':node.set('fill','white' if main else 'black')
                if node.get('stroke','none')!='none':node.set('stroke','black')
                for key in ('fill-opacity','stroke-opacity','opacity'):
                    if key in node.attrib:node.set(key,'1')
            for child in node:owner_walk(child,main,definition)
        owner_walk(owner_root)
        ownership=np.asarray(render_image(ET.tostring(owner_root,encoding='unicode'),1280).resize((1024,1024),Image.Resampling.LANCZOS))
        result['island_final_visible_ownership']={'fully_mainhair_pixels':int((island & (ownership[:,:,0]>=254)).sum()),
             'non_mainhair_or_mixed_pixels':int((island & (ownership[:,:,0]<254)).sum())}
        global_residual=paint.polynomial_residual(rgb,interior)
        local_domain=interior.copy();local_domain[:544,:]=False;local_domain[:,48:]=False
        local_residual=paint.polynomial_residual(rgb,local_domain)
        result['trend_domain_diagnostic_NOT_gate_override']={
          'local_domain':'same declared mask intersect native bbox [0,680,60,1280], then same 3px eroded interior; left hair only',
          'domain_pixels':int(local_domain.sum()),
          'island_coverage':int((island&local_domain).sum()),
          'global_quadratic_prediction_rgb_median_at_island':np.median((rgb-global_residual)[island],axis=0).tolist(),
          'global_contrast_median':float(np.median(np.sqrt(np.mean(global_residual[island]**2,axis=1)))),
          'local_quadratic_contrast_median':float(np.median(np.sqrt(np.mean(local_residual[island]**2,axis=1)))),
          'local_quadratic_contrast_max':float(np.max(np.sqrt(np.mean(local_residual[island]**2,axis=1)))),
          'island_full_mottle_support_pixels':int((island&maps['texture_support']['hair-front-main']['mottle']).sum()),
          'purpose':'domain-sensitivity diagnosis, not acceptance; local-fit negative sensitivity not validated'}
        # Show the full context and an enlarged crop; red only on diagnostic panel.
        crop=(0,730,130,880)
        panels=[]
        for name, im in [('SOURCE',source),('CANDIDATE',candidate)]:
            p=Image.new('RGB',(390,490),'#20242d'); p.paste(im.crop(crop).convert('RGB').resize((390,450)),(0,40))
            ImageDraw.Draw(p).text((8,12),name,fill='white'); panels.append(p)
        overlay=np.asarray(candidate).copy()
        native_island=np.asarray(Image.fromarray(island).resize((1280,1280),Image.Resampling.NEAREST))
        native_edge=mask ^ ndi.binary_erosion(mask)
        overlay[native_edge,:3]=[255,225,0]; overlay[native_island,:3]=[255,0,70]
        p=Image.new('RGB',(390,490),'#20242d');p.paste(Image.fromarray(overlay).crop(crop).convert('RGB').resize((390,450)),(0,40))
        ImageDraw.Draw(p).text((8,12),'RED=ISLAND YELLOW=MASK',fill='white');panels.append(p)
        board=Image.new('RGB',(1170,490))
        for i,p in enumerate(panels):board.paste(p,(390*i,0))
        board.save(OUT/'left-hair-crop.png')
        # Boundary-free source-only ROI, chosen by visible hair surface before statistics.
        source_roi={'schema':contract['schema'],'long_edge':1024,'rules':contract['rules'],
          'regions':[{'id':'source-central-bang-independent','bbox':[390/1280,420/1280,625/1280,680/1280],'expectation':'smooth_field'}]}
        independent, _=paint.analyze_image(source,source_roi)
        result['source_independent_material_roi']={'contract':source_roi,'result':compact(independent),'reason':'rectangle within central blue bang; no candidate mask and no source/candidate shared fit'}
    else:
        # Independent fields use image coordinates and documented constants;
        # they never load candidate paint-fields.json or replay declared shading.
        yy,xx=np.mgrid[:1280,:1280]
        base_rgb=np.empty((1280,1280,3),float)
        for c,v in enumerate((64.,86.,156.)):base_rgb[:,:,c]=v+0.015*yy
        cone_a=np.clip(1-np.hypot((xx-60)/570,(yy-730)/510),0,1)
        cone_b=np.clip(1-np.hypot((xx-480)/550,(yy-770)/480),0,1)
        radial=base_rgb+cone_a[:,:,None]*np.array([25,31,42])+cone_b[:,:,None]*np.array([20,27,34])
        # C-infinity Gaussian radial combination is a separate positive control.
        gauss=base_rgb+np.exp(-((xx-400)**2/(2*210**2)+(yy-650)**2/(2*225**2)))[:,:,None]*np.array([35,43,54])
        roi=mask & (xx>=420)&(xx<560)&(yy>=430)&(yy<600)
        disk=mask & ((xx-475)**2+(yy-510)**2<=13**2)
        safe=ndi.binary_erosion(mask,iterations=32)
        rng=np.random.default_rng(20260929)
        cases={'positive-linear':base_rgb,'positive-two-broad-cones':radial,'positive-broad-gaussian':gauss}
        positive_baseline=radial.copy()
        negative=positive_baseline.copy();negative[disk]+=np.array([55,20,-10]);cases['negative-color-island']=negative
        negative=positive_baseline.copy();negative[roi]+=rng.normal(0,5,(roi.sum(),3));cases['negative-grain']=negative
        noise=ndi.gaussian_filter(rng.normal(size=(1280,1280)),6)
        noise=noise/np.std(noise[roi])*5
        negative=positive_baseline.copy();negative[roi]+=noise[roi,None];cases['negative-cloud']=negative
        # Candidate injection retains all original material, not a replaced clean ROI.
        actual_rgb=np.asarray(candidate)[:,:,:3].astype(float)
        negative=actual_rgb.copy();negative[disk]+=np.array([55,20,-10]);cases['actual-candidate-plus-island']=negative
        negative=actual_rgb.copy();negative[safe]+=rng.normal(0,3,(safe.sum(),3));cases['actual-candidate-plus-grain']=negative
        negative=actual_rgb.copy();negative[safe]+=noise[safe,None];cases['actual-candidate-plus-cloud']=negative
        controls=[];panels=[]
        for name, field in cases.items():
            arr=np.asarray(candidate).copy()
            arr[:,:,:3][mask]=np.uint8(np.clip(np.rint(field[mask]),0,255))
            rep,cmaps=paint.analyze_image(Image.fromarray(arr),contract,masks)
            controls.append({'id':name,'decoded_sha256':paint.decoded_hash(Image.fromarray(arr)),**compact(rep)})
            # Same 170 x 200 material patch before/after; raw pixels are not hidden by overlay.
            p=Image.new('RGB',(256,320),'#20242d');p.paste(Image.fromarray(arr).crop((400,420,570,620)).convert('RGB').resize((256,280)),(0,40))
            ImageDraw.Draw(p).text((5,10),name,fill='white');panels.append(p)
        board=Image.new('RGB',(256*3,320*4))
        for i,p in enumerate(panels):board.paste(p,((i%3)*256,320+(i//3)*320))
        # Context makes the left strip positive-control alarm auditable, too.
        context=positive_baseline.copy()
        context_rgba=np.asarray(candidate).copy();context_rgba[:,:,:3][mask]=np.uint8(np.clip(np.rint(context[mask]),0,255))
        for i,(name,im) in enumerate((('SOURCE',source),('CANDIDATE',candidate),('INDEPENDENT TWO CONES',Image.fromarray(context_rgba)))):
            p=Image.new('RGB',(256,320),'#20242d');p.paste(im.crop((0,650,80,850)).convert('RGB').resize((112,280)),(72,40))
            ImageDraw.Draw(p).text((5,10),name,fill='white');board.paste(p,(i*256,0))
        board.save(OUT/'controls-board.png')
        result['definitions']={'linear':'RGB=(64,86,156)+0.015*y',
         'two_cones':'linear + clip(1-hypot((x-60)/570,(y-730)/510),0,1)*(25,31,42) + clip(1-hypot((x-480)/550,(y-770)/480),0,1)*(20,27,34)',
         'gaussian':'linear + exp(-((x-400)^2/(2*210^2)+(y-650)^2/(2*225^2)))*(35,43,54)',
         'injected_color_island':'disk center=(475,510), radius=13 native px; add RGB=(55,20,-10)',
         'grain':'seed=20260929, independent per-channel normal noise, sigma=5 local / 3 actual full safe material',
         'cloud':'same seeded random field, gaussian sigma=6 native px, normalized to RMS=5 over local ROI',
         'local_roi_xyxy':[420,430,560,600], 'candidate_safe_material':'32-iteration erosion of same declared mainhair mask',
         'outside_material':'candidate unchanged in every case', 'frozen_rules_unchanged':True}
        result['cases']=controls
    result['elapsed_seconds']=time.monotonic()-start
    (OUT/(mode+'.json')).write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'mode':mode,'elapsed_seconds':result['elapsed_seconds'],'output':str(OUT/(mode+'.json'))}))


if __name__=='__main__':
    mode=sys.argv[1]
    if '--worker' in sys.argv:
        worker(mode)
    else:
        from tools.run_visual_e2e import run_bounded
        raise SystemExit(run_bounded([sys.executable,'-B',__file__,mode,'--worker'],timeout=40))
