import numpy as np
from PIL import Image
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
a=np.asarray(Image.open(ROOT/'ref/subjects/deepseek/cetus-desktop/r1-clean-source-1280.png')).astype(float)
for y,lo,hi in [(825,850,880),(850,840,890),(875,840,890),(900,825,890),(925,820,880),(950,815,880),(975,800,870),(1000,795,865),(1025,790,860),(1050,795,850),(1075,795,850),(1100,790,845)]:
    d=np.linalg.norm(a[y,lo+1:hi+1,:3]-a[y,lo:hi,:3],axis=1)
    inds=np.argsort(d)[-5:][::-1]
    print(y,[(int(lo+i),round(float(d[i]),2),a[y,lo+i,:3].astype(int).tolist(),a[y,lo+i+1,:3].astype(int).tolist()) for i in inds])
