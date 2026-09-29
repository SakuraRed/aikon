"""Source-only foreground proxy for a known uniform backdrop.

Unlike pixelwise color thresholding, an enclosed dark eye cannot become a hole
in the silhouette. This is not a general-purpose matte extractor: source alpha
still controls coverage, and foreground indistinguishable from the connected
backdrop remains ambiguous. Never infer artistic acceptance from this mask.
"""
import numpy as np
from scipy import ndimage as ndi


def exterior_foreground(rgba, background=(15, 15, 15), tolerance=8, alpha_threshold=128):
    pixels=np.asarray(rgba)
    if pixels.ndim!=3 or pixels.shape[2]!=4 or pixels.dtype!=np.uint8:
        raise ValueError('Expected native uint8 RGBA')
    if min(pixels.shape[:2])<2:
        raise ValueError('Canvas must have at least two pixels per dimension')
    if len(background)!=3 or any(isinstance(v,bool) or not isinstance(v,int) or not 0<=v<=255 for v in background):
        raise ValueError('Background requires three integer channels')
    if isinstance(tolerance,bool) or not isinstance(tolerance,int) or not 0<=tolerance<=255:
        raise ValueError('Invalid backdrop tolerance')
    if isinstance(alpha_threshold,bool) or not isinstance(alpha_threshold,int) or not 1<=alpha_threshold<=255:
        raise ValueError('Invalid coverage threshold')
    opaque=pixels[:,:,3]>=alpha_threshold
    near=np.max(np.abs(pixels[:,:,:3].astype(np.int16)-np.array(background)),axis=2)<=tolerance
    allowed=(~opaque)|near
    seeds=np.zeros_like(allowed)
    seeds[0,:]=allowed[0,:];seeds[-1,:]=allowed[-1,:]
    seeds[:,0]=allowed[:,0];seeds[:,-1]=allowed[:,-1]
    exterior=ndi.binary_propagation(seeds,structure=np.ones((3,3),dtype=bool),mask=allowed)
    return opaque & ~exterior, exterior
