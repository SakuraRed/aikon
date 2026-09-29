import audit
import numpy as np
from scipy import ndimage as ndi
from PIL import Image

p=audit.ROOT/'outputs/round-003/endministrator-male/unmasked/short.svg'
root=audit.validate_svg(p.read_text(encoding='utf-8'))
original=np.array(audit.image(p.read_text(encoding='utf-8')))
label=np.array(audit.render_ownership(root,'hair-back'))
a=original[:,:,3];b=label[:,:,3];delta=b.astype(int)-a.astype(int);bad=delta!=0
y,x=np.nonzero(bad)
inside=ndi.binary_erosion(a==255,iterations=3,border_value=1)
r={'bad_pixels':int(bad.sum()),'signed_delta_values_counts':{str(k):int(n) for k,n in zip(*np.unique(delta[bad],return_counts=True))},'bbox':list(map(int,[x.min(),y.min(),x.max()+1,y.max()+1])) if len(x) else None,'source_fully_opaque_bad':int((bad&(a==255)).sum()),'source_3px_opaque_interior_bad':int((bad&inside).sum()),'original_alpha_values_at_bad':{str(k):int(n) for k,n in zip(*np.unique(a[bad],return_counts=True))},'meaning':'Diagnostic only; raw equality failed and no unchanged-alpha claim is made.'}
audit.write(audit.OUT/'alpha-recolor-diagnosis.json',r)
Image.fromarray((bad*255).astype('uint8')).save(audit.OUT/'alpha-recolor-mismatch.png')
Image.fromarray(a).save(audit.OUT/'original-alpha.png');Image.fromarray(b).save(audit.OUT/'recolored-alpha.png')
print(r)
