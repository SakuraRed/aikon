"""Check actual SVG paint against serialized analytic fields on each surface."""
import io,json,sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from fit_natural import eval_field,sha,dump
from svg_fields import surface
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[4]
sys.path.insert(0,str(REPO))
from tools.render_svg import render_svg_text

def run(directory,output=None):
    directory=Path(directory);g=json.loads((directory/'geometry-input/geometry.json').read_text());f=json.loads((directory/'fields.json').read_text());pal={r['id']:r for r in f['palette']};out=[]
    for region in g['regions']:
        field=pal[region['id']]['field'];definition,body=surface(region,field,'validation-'+region['id'])
        svg='<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="1280" viewBox="0 0 1280 1280"><defs>'+definition+'</defs>'+body+'</svg>'
        pixels=np.array(Image.open(io.BytesIO(render_svg_text(svg,1280))))
        mask=np.array(Image.open(directory/'geometry-input'/region['mask_path']))>127
        # Compare opaque interior only for analytic interpolation equivalence;
        # entire visible mask color/tip ranges already reported by fit_natural.
        use=ndimage.binary_erosion(mask,iterations=2)&(pixels[...,3]==255)
        if not use.any():
            out.append({'id':region['id'],'status':'not_assessed','reason':'no fully opaque 2px interior; all-visible ranges still in fields.json'});continue
        y,x=np.nonzero(use);expected=eval_field(field,np.column_stack((x+.5,y+.5)));actual=pixels[use,:3].astype(float);error=abs(actual-expected)
        out.append({'id':region['id'],'pixels':int(use.sum()),'layered':field['kind']=='layered','channel_mae_255':float(error.mean()),'channel_max_255':float(error.max()),'channel_p99_255':float(np.quantile(error,.99)),'status':'pass' if error.max()<2.1 else 'fail'})
    result={'geometry_sha256':sha(directory/'geometry-input/geometry.json'),'fields_sha256':sha(directory/'fields.json'),'renderer':'actual resvg via tools.render_svg','tolerance_rgb_levels':2.1,'scope':'SVG interpolation/export equivalence, not artistic acceptance','results':out,'pass':all(x['status']!='fail' for x in out)}
    dump(Path(output) if output else directory/'actual-render-field-equivalence.json',result);print(json.dumps({'pass':result['pass'],'failed':[r['id'] for r in out if r['status']=='fail'],'not_assessed':[r['id'] for r in out if r['status']=='not_assessed']}))
    if not result['pass']:raise SystemExit(2)

if __name__=='__main__':run(sys.argv[1],sys.argv[2] if len(sys.argv)>2 else None)
