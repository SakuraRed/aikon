"""Bounded low-frequency SVG paint fitting for visible semantic regions.

No reference image is embedded or emitted as reconstructed art. Raster masks are
measurement inputs; final SVG uses geometry-study editable paths.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from scipy.optimize import minimize_scalar, minimize


def _weights(t, count):
    t = np.clip(t, 0, 1) * (count - 1)
    low = np.minimum(t.astype(int), count - 2)
    frac = t - low
    weights = np.zeros((len(t), count), dtype=float)
    weights[np.arange(len(t)), low] = 1 - frac
    weights[np.arange(len(t)), low + 1] = frac
    return weights


def _fit_stops(t, values, count):
    weights = _weights(t, count)
    # A gradient may have knots outside the visible clipped support. Anchor
    # those weakly to the material mean, not the least-norm black default.
    design = np.vstack((weights, .01*np.eye(count)))
    targets = np.vstack((values, np.tile(.01*values.mean(axis=0), (count, 1))))
    colors = np.linalg.lstsq(design, targets, rcond=None)[0]
    colors = np.clip(colors, 0, 255)
    predicted = weights @ colors
    return colors, float(np.sqrt(np.mean((predicted - values) ** 2)))


def _stops(colors):
    return [{"offset": i / (len(colors) - 1),
             "color": "#" + "".join(f"{int(v):02x}" for v in np.rint(c)),
             "rgb": np.round(c, 5).tolist()} for i, c in enumerate(colors)]


def _linear_candidate(xy, values, bounds, count):
    corners = np.array([[bounds[0], bounds[1]], [bounds[0], bounds[3]],
                        [bounds[2], bounds[1]], [bounds[2], bounds[3]]])

    def fit_angle(angle, get_field=False):
        direction = np.array([math.cos(angle), math.sin(angle)])
        extents = corners @ direction
        lo, hi = extents.min(), extents.max()
        colors, error = _fit_stops((xy @ direction - lo) / (hi - lo), values, count)
        if not get_field:
            return error
        start = direction * lo
        end = direction * hi
        return {"kind": "linear", "from": start.tolist(), "to": end.tolist(),
                "x1": float(start[0]), "y1": float(start[1]),
                "x2": float(end[0]), "y2": float(end[1]), "gradientUnits": "userSpaceOnUse",
                "stops": _stops(colors), "sample_rmse": error,
                "parameters": count * 3 + 1}

    angles = np.linspace(0, math.pi, 12, endpoint=False)
    best = min(angles, key=fit_angle)
    result = minimize_scalar(fit_angle, bounds=(best - math.pi / 12, best + math.pi / 12),
                             method="bounded", options={"maxiter": 18, "xatol": .0005})
    return fit_angle(float(result.x), True)


def _radial_candidate(xy, values, bounds, count):
    x0, y0, x1, y1 = bounds
    width, height = x1-x0, y1-y0
    corners = np.array([[x0, y0], [x0, y1], [x1, y0], [x1, y1]])

    def fit_params(params, get_field=False):
        cx, cy = x0 + params[0]*width, y0 + params[1]*height
        aspect = math.exp(params[2])
        radius = np.max(np.sqrt((corners[:, 0]-cx)**2 + ((corners[:, 1]-cy)*aspect)**2))
        radius = max(radius, 1.)
        t = np.sqrt((xy[:, 0]-cx)**2 + ((xy[:, 1]-cy)*aspect)**2)/radius
        colors, error = _fit_stops(t, values, count)
        if not get_field:
            return error
        return {"kind": "radial", "center": [cx, cy], "radii": [radius, radius/aspect],
                "cx": 0., "cy": 0., "r": 1., "fx": 0., "fy": 0.,
                "gradientTransform": f"translate({cx:.5f} {cy:.5f}) scale({radius:.5f} {radius/aspect:.5f})",
                "gradientUnits": "userSpaceOnUse",
                "stops": _stops(colors), "sample_rmse": error,
                "parameters": count*3 + 3}

    guesses = [[x, y, 0] for x in (0., .5, 1.) for y in (0., .5, 1.)]
    best = min(guesses, key=fit_params)
    result = minimize(fit_params, best, method="Nelder-Mead",
                      bounds=((-1., 2.), (-1., 2.), (-.7, .7)),
                      options={"maxiter": 38, "xatol": .003, "fatol": .003})
    return fit_params(result.x, True)


def evaluate_field(field, xy):
    """Evaluate a serialized field at N x 2 global pixel-center coordinates."""
    xy = np.asarray(xy, dtype=float)
    if field["kind"] == "solid":
        return np.broadcast_to(field["rgb"], (len(xy), 3)).copy()
    if field["kind"] == "linear":
        start = np.array(field["from"])
        delta = np.array(field["to"]) - start
        t = ((xy - start) @ delta) / (delta @ delta)
    elif field["kind"] == "radial":
        delta = (xy - np.array(field["center"])) / np.array(field["radii"])
        t = np.sqrt((delta**2).sum(axis=1))
    else:
        raise ValueError("unsupported field kind")
    stops = field["stops"]
    # Use stored RGB floats for diagnostics; svg_paint emits those same values
    # as rgb(percentage) to avoid introducing a separate rounding discrepancy.
    colors = np.array([s["rgb"] for s in stops])
    return _weights(t, len(stops)) @ colors


def fit_field(rgb, visible_mask, excluded_mask=None, *, edge_pixels=2, allowed=None, simplicity_tolerance=.35):
    """Fit one solid/linear/radial field; report every nonexcluded interior pixel.

    Deterministic stratified sample <=3000 estimates parameters. The complete
    interior evaluates them; no residual-driven omission, denoising or masking.
    Simpler candidate retained if its RMSE lies within 0.35 RGB levels of best.
    """
    rgb = np.asarray(rgb)[..., :3]
    mask = np.asarray(visible_mask, dtype=bool)
    if mask.shape != rgb.shape[:2] or not np.any(mask):
        raise ValueError("nonempty same-canvas mask required")
    exclusion = np.zeros_like(mask) if excluded_mask is None else np.asarray(excluded_mask, dtype=bool)
    if exclusion.shape != mask.shape:
        raise ValueError("exclusion shape mismatch")
    interior = ndimage.binary_erosion(mask, iterations=edge_pixels) if edge_pixels else mask.copy()
    use = interior & ~exclusion
    yy, xx = np.nonzero(use)
    if len(xx) < 16:
        raise ValueError("too few interior pixels; explicit different treatment needed")
    xy = np.column_stack((xx+.5, yy+.5))
    values = rgb[use].astype(float)
    sample = np.linspace(0, len(xx)-1, min(3000, len(xx))).astype(int)
    fit_xy, fit_values = xy[sample], values[sample]
    my, mx = np.nonzero(mask)
    bounds = [float(mx.min()), float(my.min()), float(mx.max()+1), float(my.max()+1)]
    mean = fit_values.mean(axis=0)
    candidates = [{"kind": "solid", "rgb": mean.tolist(),
                   "color": "#"+"".join(f"{int(v):02x}" for v in np.rint(mean)),
                   "parameters": 3, "sample_rmse": float(np.sqrt(np.mean((fit_values-mean)**2)))}]
    allowed = allowed or ["solid", "linear", "radial"]
    for count in (2, 3, 5):
        if "linear" in allowed:
            candidates.append(_linear_candidate(fit_xy, fit_values, bounds, count))
        if "radial" in allowed:
            candidates.append(_radial_candidate(fit_xy, fit_values, bounds, count))
    best_error = min(c["sample_rmse"] for c in candidates)
    field = min([c for c in candidates if c["sample_rmse"] <= best_error + simplicity_tolerance],
                key=lambda c: (c["parameters"], c["sample_rmse"]))
    error = evaluate_field(field, xy) - values
    norm = np.sqrt(np.mean(error**2, axis=1))
    stats = {"visible_pixels": int(mask.sum()), "edge_excluded_pixels": int((mask & ~interior).sum()),
             "watermark_excluded_interior_pixels": int((interior & exclusion).sum()),
             "evaluated_pixels": len(xx), "parameter_fit_samples": len(sample),
             "simplicity_tolerance_rgb_levels": simplicity_tolerance,
             "rgb_rmse_255": float(np.sqrt(np.mean(error**2))),
             "rgb_mae_255": float(np.mean(np.abs(error))),
             "pixel_rgb_rmse_p95_255": float(np.quantile(norm, .95)),
             "pixel_rgb_rmse_max_255": float(norm.max()),
             "residual_gt_5_levels_pixels": int((norm>5).sum()),
             "candidate_errors": [{"kind": c["kind"], "stops": len(c.get("stops", [])),
                                    "parameters": c["parameters"], "sample_rmse": c["sample_rmse"]}
                                   for c in candidates]}
    return field, stats, use


def _rgb(color):
    return "rgb(" + ",".join(f"{v/255*100:.5f}%" for v in color) + ")"


def svg_paint(field, identifier):
    """Return (definition, fill). Pure SVG, no filters, images or textures."""
    if field["kind"] == "solid":
        return "", _rgb(field["rgb"])
    stops = "".join(f'<stop offset="{s["offset"]:.5f}" stop-color="{_rgb(s["rgb"])}"/>'
                    for s in field["stops"])
    common = f'id="{identifier}" gradientUnits="userSpaceOnUse" color-interpolation="sRGB"'
    if field["kind"] == "linear":
        a,b=field["from"],field["to"]
        definition = f'<linearGradient {common} x1="{a[0]:.5f}" y1="{a[1]:.5f}" x2="{b[0]:.5f}" y2="{b[1]:.5f}">{stops}</linearGradient>'
    else:
        cx,cy=field["center"]; rx,ry=field["radii"]
        definition = f'<radialGradient {common} cx="0" cy="0" r="1" gradientTransform="translate({cx:.5f} {cy:.5f}) scale({rx:.5f} {ry:.5f})">{stops}</radialGradient>'
    return definition, f"url(#{identifier})"


def _default_exclusion(shape):
    mask = np.zeros(shape, bool)
    # Fixed location of visible user-source watermark, not derived from error.
    # This rectangle deliberately includes the antialiased logo glyph boundary.
    mask[1196:1254, 1082:1256] = True
    return mask


def run(source, manifest_path, output, only=None, fidelity_region_prefix=None):
    started = time.monotonic()
    source = Path(source); manifest_path=Path(manifest_path); output=Path(output)
    output.mkdir(parents=True, exist_ok=True)
    image=Image.open(source).convert("RGBA"); rgb=np.asarray(image)[...,:3]
    manifest_bytes=manifest_path.read_bytes()
    manifest=json.loads(manifest_bytes.decode("utf-8-sig"))
    # Freeze the exact input, including masks, before any fit. Other agents can
    # continue reviewing the source geometry without invalidating this run.
    snapshot=output/"geometry-input"
    snapshot.mkdir(parents=True,exist_ok=True)
    (snapshot/"geometry.json").write_bytes(manifest_bytes)
    mask_paths={r["mask_path"] for r in manifest["regions"]+manifest.get("underpaints",[])}
    if manifest.get("watermark_uncertainty_mask"):
        mask_paths.add(manifest["watermark_uncertainty_mask"])
    for relative in mask_paths:
        destination=snapshot/relative
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(manifest_path.parent/relative,destination)
    if manifest_path.read_bytes()!=manifest_bytes:
        raise RuntimeError("geometry manifest changed during input snapshot")
    manifest_path=snapshot/"geometry.json"
    exclusion_path=manifest_path.parent/manifest["watermark_uncertainty_mask"] if manifest.get("watermark_uncertainty_mask") else None
    exclusion=np.asarray(Image.open(exclusion_path).convert("L"))>127 if exclusion_path else _default_exclusion(rgb.shape[:2])
    Image.fromarray(exclusion.astype("uint8")*255).save(output/"watermark-exclusion.png")
    reconstructed=np.zeros((*rgb.shape[:2],4),np.uint8)
    residual=np.zeros((*rgb.shape[:2],3),np.uint8)
    union=np.zeros(rgb.shape[:2],bool)
    params=[]; definitions=[]; paths=[]
    for region in sorted(manifest["regions"], key=lambda r:r.get("z",0)):
        if only and region["id"] not in only:
            continue
        mask=np.asarray(Image.open(manifest_path.parent/region["mask_path"]).convert("L"))>127
        tolerance=.05 if fidelity_region_prefix and region["id"].startswith(fidelity_region_prefix) else .35
        field,stats,use=fit_field(rgb,mask,exclusion,simplicity_tolerance=tolerance)
        ys,xs=np.nonzero(mask)
        pred=evaluate_field(field,np.column_stack((xs+.5,ys+.5)))
        reconstructed[ys,xs,:3]=np.rint(pred).clip(0,255).astype("uint8")
        reconstructed[ys,xs,3]=255
        yy,xx=np.nonzero(use)
        diff=np.sqrt(np.mean((reconstructed[yy,xx,:3].astype(float)-rgb[yy,xx])**2,axis=1))
        residual[yy,xx]=np.column_stack((np.minimum(diff*14,255),np.minimum(diff*3,100),np.zeros(len(diff)))).astype("uint8")
        union|=use
        params.append({"id":region["id"],"semantic_role":region.get("semantic_role"),
                       "source_mask_sha256":hashlib.sha256((manifest_path.parent/region["mask_path"]).read_bytes()).hexdigest(),
                       "field":field,"stats":stats})
        definition,fill=svg_paint(field,"paint-"+region["id"])
        definitions.append(definition)
        if region.get("d"):
            paths.append(f'<path id="{region["id"]}" d="{region["d"]}" fill-rule="{region.get("fill_rule","nonzero")}" fill="{fill}"/>')
        print(region["id"],field["kind"],round(stats["rgb_rmse_255"],4),flush=True)
    result={"schema":"aikon.r1-analytic-paint-study.v1","source_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
            "source":"ref/user-mode/r1.png","geometry_manifest_sha256":hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            "geometry_manifest_file":"geometry-input/geometry.json",
            "scope":"same-source semantic paint calibration, not independent Skill creation or acceptance",
            "fitting_policy":{"default_simplicity_tolerance":.35,"fidelity_region_prefix":fidelity_region_prefix,
                              "fidelity_simplicity_tolerance":.05 if fidelity_region_prefix else None},
            "exclusions":{"edge_pixels":2,"watermark_mask":str(exclusion_path) if exclusion_path else "default_fixed_rectangle",
                          "watermark_mask_sha256":hashlib.sha256(exclusion_path.read_bytes()).hexdigest() if exclusion_path else None,
                          "watermark_pixels":int(exclusion.sum())},
            "palette":params,"elapsed_seconds":time.monotonic()-started}
    (output/"fields.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    Image.fromarray(reconstructed).save(output/"analytic-material-preview.png")
    Image.fromarray(residual).save(output/"residual-heatmap.png")
    Image.fromarray(union.astype("uint8")*255).save(output/"evaluated-pixels.png")
    if paths:
        (output/"analytic-materials.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 1280"><defs>'+"".join(definitions)+'</defs>'+"".join(paths)+'</svg>',encoding="utf-8")
    board=Image.new("RGB",(1280*3,1340),"#181a20")
    draw=ImageDraw.Draw(board)
    for i,(im,label) in enumerate(((image,"r1 source (watermark unchanged)"),(Image.fromarray(reconstructed),"one analytic field per visible surface"),(Image.fromarray(residual),"interior residual amplified 14x; excluded pixels black"))):
        bg=Image.new("RGBA",(1280,1280),"#101010"); bg.alpha_composite(im.convert("RGBA"))
        board.paste(bg.convert("RGB"),(1280*i,60)); draw.text((1280*i+20,20),label,fill="white")
    board.resize((1920,670),Image.Resampling.LANCZOS).save(output/"comparison.png")
    print("completed",round(time.monotonic()-started,2),flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",required=True);parser.add_argument("--manifest",required=True);parser.add_argument("--output",required=True)
    parser.add_argument("--only",nargs="*")
    parser.add_argument("--fidelity-region-prefix")
    args=parser.parse_args();run(args.source,args.manifest,args.output,args.only,args.fidelity_region_prefix)
