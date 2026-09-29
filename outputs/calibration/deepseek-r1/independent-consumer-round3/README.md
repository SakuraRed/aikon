# DeepSeek r1 supervised independent repair, round3

Final candidate: **r003**, a separately authorized frame-alpha-only repair following r002. It is an actual repair of independent-consumer-round2, not a new blind test or accepted artwork. All writes are confined to this folder. No master v001-v007 path/paint/source was read.

**Latest local candidate: r004**, in its own `r004/` folder pending parent comparison. Root deliverables still point to r003 so the reviewed base is not silently replaced. r004 is recommended specifically for the upper-right fringe seam improvement documented below.

## Delivered

- `short.svg` and `preview-1280.png`, `preview-128.png`, `preview-48.png`, `preview-24.png`: final r003 copies.
- `reference-comparison.png`: unwarped raw reference left, r003 right, common #0f0f0f presentation background.
- `inspection-board.png`: 128/48/24 outputs on light/dark/gray presentation backgrounds.
- `actualprompt.md`, `revision-prompt.md`, `read-log.md`: actual pre-generation instructions and reads.
- `draw.py`, `revise.py`: source; each revision preserves its corresponding original source snapshot, prompt, SVG, previews and measurements.
- `r001/measured-boundary-overlay.png`: finite fitted semantic curves over original raw image, including hidden control curves for audit; this is not a final SVG layer.

## What changed and why

The baseline's broad material color and some object boundaries were approximations. r001 measured visible ownership of its named SVG parts, sampled raw-reference interiors with erosion and semantic color checks, then fitted finite continuous fields. 21 existing semantic parts received bounded control-point corrections against nearby high-contrast raw reference locations. Endpoints and object topology were initially preserved. No raster patch, color-quantized fragment or texture was exported.

The face uses a measured vertical warm base plus one elliptical white illumination field. Hair, fabric and accessories use bounded continuous linear fields; integrated dark eyes keep their original geometry and small rim rather than gaining pupils or catchlights. There are 43 directly addressable drawing parts, including the one new face illumination layer. Some small folds are solid where the observed color variation is negligible.

Actual r001 viewing exposed a lower-lock hook caused by retaining a bad intermediate endpoint, and a narrow dark gap between adjacent fringe parts. r002 uses a shared fringe boundary and fits the lower lock's observed blue-versus-rear contour in two finite cubics. Raw sampled boundary points and fit residuals are saved in `r002/measurements.json`. The two mean horizontal fit residuals, 6.62 px and 4.37 px, show this contour remains approximate; they are not an edge-gate pass.

## Diagnostic evidence and limits

Same local diagnostic for baseline and final: original 1280 canvas, #0f0f0f compositing background, source maxRGB > 30 and alpha > 200, no exclusions or registration. This diagnostic differs from the parent's frozen v5 comparator and must not replace it.

| Own diagnostic | Round2 baseline | r001 | r002 |
|---|---:|---:|---:|
| RGB MAE | 6.24854 | 3.23409 | 3.18311 |
| RGB RMSE | 17.64303 | 14.52122 | 14.39665 |

Final local MAE is about 49.1% lower than baseline. Rendered colors and broad forms are visibly closer. Remaining discrepancies include crown/fringe junctions, lower face/right-hair boundary, rear white cloth overlaps, exact thin eye rim gloss, and the long-lock tip. One-dimensional material fits cannot reproduce every two-dimensional source field. Raw source noise is intentionally not reproduced. No assertion is made that this meets 99%, passes the frozen edge gate, or is user-accepted.

Generic static SVG validation and real rendering succeeded at all four sizes. Actual 1280 side-by-side and the three small-size/light-background inspections were completed. No installed dependencies, network calls or resident processes were introduced. Frozen comparator and quality-gate results are owned by the parent review and remain separate.

## Additional authorized r003: frame alpha only

Parent's frozen v5 evaluation of r002 found MAE 3.2925, RMSE 14.9379, silhouette IoU 0.992414, mean boundary distance 2.3198 px and maximum 15.264 px. These are parent-provided results, not remeasured by this agent.

`frame-diagnose.py` separated source rounded-frame alpha from internal material/object geometry. The old hand-authored crop was systematically more square than the raw source: 13,155 frame-threshold XOR pixels and 12.81 px maximum distance. 5,706 actual-subject pixels lay in the frame-alpha difference band, most in the lower-left corner. That band held 17.5% of whole-canvas absolute RGB error; this is an error-location statistic, not an assertion that every error there was caused by the crop.

Following the saved `r003-prompt.md`, `frame-repair.py` measured 1,112 half-alpha boundary crossings on all four raw-source corners, fitted a common radius of 299.550936 px, and exported four smooth quarter-circle cubics. Average raw horizontal fit residual was 0.062 px, maximum 0.171 px. Only `canvas-crop` path `d` changed. Removing that one attribute value makes the before/after SVG byte strings identical; the source asserts this before rendering. No subject path, paint, coordinates, scoring range, or image alignment changed.

| Raw-source/frame diagnostic | r002 | r003 |
|---|---:|---:|
| Frame binary XOR pixels | 13,155 | 63 |
| Frame boundary maximum distance, px | 12.806 | 1.000 |
| Frame alpha MAE, 0–255 | 2.04087 | 0.01940 |
| Whole-canvas RGB MAE | 2.90291 | 2.40091 |
| Whole-canvas RGB RMSE | 16.39849 | 12.92231 |
| Alpha mass outside fully transparent source frame | 3,406.36 | 0.00 |
| Source-opaque subject RGB MAE | 3.17848 | 3.17848 |
| Source-opaque subject pixels not fully covered | 3,781 | 3,781 |

The unchanged opaque-subject error and missing-coverage count are expected: this local revision removes frame overflow and does not repair the remaining internal or subject-silhouette errors. Full results, source boundary samples and changed-pixel map are in `r003/`; r002 remains preserved. All four sizes rendered successfully. The actual r003 reference pair, small-size background board and changed-pixel map were viewed. The parent's unchanged frozen comparator remains the final gate.

## Additional authorized r004: upper-right fringe paint continuity

Actual raw-source/r003 inspection and cross-boundary sampling distinguished a legitimate broad hair-material division from an artificial dark needle. Around y490–520, a roughly 1–3 px exposed strip of `hair-crown-parent` showed through the center-fringe/right-main-lock joint. Around y350–390, the right-main-lock's distinct field created a premature triangular cap. The source itself has a broad side-to-side color difference at y400–550; that division must not be indiscriminately erased.

`seam-repair.py` added two local material support layers using exact copies of existing geometry: one continues the right-main-lock field through the exposed narrow crown strip; the other smoothly tapers shared crown material into the main lock over y340–440. Original ID attributes, path data, paint definitions, crop, eye/face positions and child nodes were asserted identical. 1280 alpha bytes remain exactly identical. Only 8,850 rendered pixels changed, within x650–831/y343–531. No bow or crest edits were made.

| Local diagnostic | r003 | r004 |
|---|---:|---:|
| Inspection ROI MAE, x610–809/y320–609 | 3.11165 | 2.99657 |
| Target ROI MAE, x650–749/y340–539 | 3.03388 | 2.74218 |
| Whole-canvas RGB MAE | 2.40091 | 2.39673 |
| Whole-canvas RGB RMSE | 12.92231 | 12.92138 |

The actual `r004/local-source-r003-r004.png` was inspected: source left, r003 center, r004 right. The artificial dark needle disappears and the small upper cap is reduced. Full reference comparison and small-size board were also viewed. Side sampling records retain regressions: at y370–390 the source's broad boundary position differs from the preserved geometry and some cross-boundary differences increase. This limited paint repair does not solve that geometric placement. Recommendation is r004 for the measured local improvement, subject to parent frozen comparison/visual audit; no further local revision was generated.
