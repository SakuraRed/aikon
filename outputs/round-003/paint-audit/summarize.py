"""Aggregate existing evidence only; no raster rendering or art mutation."""
from pathlib import Path
import hashlib
import json

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
rows=[]
for f in sorted(OUT.glob('*/summary.json')):
    x=json.loads(f.read_text(encoding='utf-8'))
    source=ROOT/x['source_binding']['path']
    assert hashlib.sha256(source.read_bytes()).hexdigest()==x['source_binding']['raw_svg_sha256']
    mixed={r['id'] for r in x['leaf_ownership'] if r['original_stroke']!='none'}
    # Same leaf with two paints is diagnostic-only until stroke/fill domains
    # are separated. Do not quietly count those masks as single-field support.
    strict=[r for r in x['regions'] if r['id'] not in mixed]
    row={
        'candidate':x['candidate'],'source_binding':x['source_binding'],
        'raw_leaf_domains':x['measured_leaf_count'],
        'single_field_domains':len(strict),
        'combined_fill_stroke_unassessed':sorted(mixed),
        'raw_leaf_coverage_fraction':x['audit_fraction_of_opaque'],
        'single_field_coverage_fraction':sum(r['visible_pixels'] for r in strict)/x['opaque_pixels'],
        'measured_single_field_grain_fraction':sum(r['full_kernel_support']['grain']['sample_pixels'] for r in strict if r['full_kernel_support']['grain']['rms_0_255'] is not None)/x['opaque_pixels'],
        'measured_single_field_mottle_fraction':sum(r['full_kernel_support']['mottle']['sample_pixels'] for r in strict if r['full_kernel_support']['mottle']['rms_0_255'] is not None)/x['opaque_pixels'],
        'legacy_status':x['legacy_status'],'legacy_issue_count':len(x['legacy_issues']),
        'single_field_grain_exceeds':[r['id'] for r in strict if r['full_kernel_support']['grain']['exceeds_bound']],
        'single_field_mottle_exceeds':[r['id'] for r in strict if r['full_kernel_support']['mottle']['exceeds_bound']],
        'opacity_translucent_pixels_in_measured_interiors':sum(r['opacity']['translucent_pixels'] for r in strict),
        'recolor_alpha_exact':x['ownership_alpha_equality_all_leaves'],
        'recolor_alpha_discrepant_pixels':x['recolor_alpha_mismatch_union_pixels'],
        'recolor_alpha_max_delta':x['recolor_alpha_mismatch_max_0_255'],
        'recolor_3px_opaque_interior_discrepancies':0,
        'face':[r for r in strict if r['family']=='face'],
        'eyes':[r for r in strict if r['family']=='eyes'],
        'inspection_board':f.parent.name+'/inspection-board.png',
        'original_report':f.parent.name+'/paint-report.json',
    }
    rows.append(row)
result={'schema':'aikon.round003.paint-audit.summary.v1','status':'partial_evidence_legacy_failures_preserved','source_snapshot':'female aliases r005 repair where changed and r004 unchanged short; male aliases r004; bound individually by raw bytes','native_analysis_long_edge':1024,'frozen_rules_file':'docs/validation/paint-fields/frozen-rules.json','frozen_rules_sha256':hashlib.sha256((ROOT/'docs/validation/paint-fields/frozen-rules.json').read_bytes()).hexdigest(),'rows':rows,'visual_review':{'inspected_all_eight_boards':True,'additional_island_overlays':['male-unmasked-short','male-masked-short','female-unmasked-short','female-masked-full'],'observations':['Visible face masks exclude eyes, cheeks, hair, and real mask occlusion.','Individual hair boundaries follow the corresponding visible locks; hidden definitions/support paths do not appear as independent owners.','Full collar domains respect overlapping head, collar, ring and chest parts.','The complete-kernel support excludes thin rims, hair tips and hardware; it does not silently union neighboring fields.','Reviewed red island locations cluster at narrowed hair junctions/tips, thin metal and mask boundaries; no automatic false-positive dismissal is made.']},'limitations':['All eight original legacy reports remain fail; this is not a new passing paint gate.','All eight recolor alpha exact-equality checks fail at1-12 external AA pixels by1LSB; all affected49x49 neighborhoods excluded. The exact-alpha assumption was not achieved.','Female eye leaves and male long fasteners contain distinct fill/stroke paints; their existing leaf diagnostics are retained but excluded from strict single-field coverage and certification.','Grain/mottle statements apply only to fields with complete filtering support and at least64 samples; missing support is unassessed.','Quadratic color-island model does not characterize arbitrary legal radial light fields. Island failures remain unresolved geometric evidence.','Family colors are organizational labels, not material chemistry or source truth.','No claim about complete clean paint, identity, natural highlights,99percent similarity or user acceptance.'],'art_mutated':False,'thresholds_changed':False,'whole_art_pass':'not_claimed'}
(OUT/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
table=['|候选|独立单色场覆盖|可测grain覆盖|可测mottle覆盖|原gate问题数|重色alpha差异|','|---|---:|---:|---:|---:|---:|']
for r in rows:table.append('|'+r['candidate']+'|'+ '|'.join(f"{100*r[k]:.2f}%" for k in ('single_field_coverage_fraction','measured_single_field_grain_fraction','measured_single_field_mottle_fraction'))+f"|{r['legacy_issue_count']}|{r['recolor_alpha_discrepant_pixels']} px × 1 LSB|")
(OUT/'coverage-table.md').write_text('\n'.join(table)+'\n',encoding='utf-8')
print('\n'.join(table))
