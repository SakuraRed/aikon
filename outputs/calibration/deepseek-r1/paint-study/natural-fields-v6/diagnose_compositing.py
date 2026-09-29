"""Inspect actual component RGBA at fixed worst residual coordinates."""
import io,json,sys
from pathlib import Path
import numpy as np
from PIL import Image
from fit_natural import eval_field,alpha,dump
from svg_fields import paint
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[4];sys.path.insert(0,str(REPO))
from tools.render_svg import render_svg_text

def layer(field,name):
    defs,fill,unused=paint(field,name)
    svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 1280"><defs>'+defs+'</defs><rect width="1280" height="1280" fill="'+fill+'"/></svg>'
    return np.array(Image.open(io.BytesIO(render_svg_text(svg,1280))))

def main():
    directory=HERE/'final-fit';doc=json.loads((directory/'fields.json').read_text());out=[]
    for rid,coords in [('hair-right-fringe',[(954,770),(800,700),(900,1000)]),('hair-front-main',[(420,650),(320,490),(520,780)])]:
        f=next(p['field'] for p in doc['palette'] if p['id']==rid);layers=[layer(f['base'],'base')]+[layer(g,'glaze'+str(i)) for i,g in enumerate(f['glazes'])]
        rows=[]
        for x,y in coords:
            xy=np.array([[x+.5,y+.5]]);base_ideal=eval_field(f['base'],xy)[0];row={'xy':[x+.5,y+.5],'base_ideal_rgb':base_ideal.tolist(),'base_actual_rgba':layers[0][y,x].tolist(),'glazes':[]}
            ideal=base_ideal.copy();actual_component_rgb=layers[0][y,x,:3].astype(float)
            for g,im in zip(f['glazes'],layers[1:]):
                a=float(alpha(g,xy)[0]);rgba=im[y,x];actual_a=rgba[3]/255.;pigment=np.array(g['stops'][0]['rgb'])
                ideal=ideal*(1-a)+pigment*a;actual_component_rgb=actual_component_rgb*(1-actual_a)+rgba[:3]*actual_a
                row['glazes'].append({'ideal_alpha':a,'actual_alpha':actual_a,'ideal_pigment_rgb':pigment.tolist(),'actual_unpremultiplied_rgba':rgba.tolist(),'premultiplied_rgb_ideal':(pigment*a).tolist(),'premultiplied_rgb_actual':(rgba[:3]*actual_a).tolist()})
            row.update(analytic_final_rgb=ideal.tolist(),composed_actual_component_rgba_prediction=actual_component_rgb.tolist());rows.append(row)
        out.append({'id':rid,'points':rows})
    dump(directory/'premultiplied-quantization-diagnosis.json',{'scope':'fixed sample diagnostic; does not alter renderer, model, or validation thresholds','results':out})

if __name__=='__main__':main()
