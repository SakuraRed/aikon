# r1 semantic geometry study

**Latest: [v5](v5/README.md)** recomputes v4's algorithm from the authenticated `cetus-desktop` source's own RGBA. It has no watermark exclusion, inherited user-r1 alpha or interpolated geometry. v4's mixed-alpha working source was superseded; it remains failure/provenance history. The original-source stop below describes the earlier v1–v3 handoff, which remains preserved as historical evidence.

Status: **private calibration evidence, not accepted production art**. Work stopped immediately when the user identified `cetus-desktop` as the source. The root agent is retrieving the original; these approximate reconstructions must not override a better authentic source.

The original `ref/user-mode/r1.png` remains unchanged. No shared Skill, CI, previous output or Git state was changed by this bounded geometry task. The script only writes below this directory. The initial execution brief was saved before reconstruction in `brief.zh-CN.md`.

## Snapshots

| Snapshot | Manifest | Geometry scope | Status |
| --- | --- | --- | --- |
| v1 | `geometry.json` | 40 visible semantic surfaces plus 5 opaque parent supports | Recorded failure: warm skin predicate lost nearly white face rims; hand-constrained rear surfaces mixed materials |
| v2 | `v2/geometry.json` | 39 surfaces, 1,160 visible curve anchors | Corrected full bright face support and bow contamination; rear interfaces still imperfect |
| v3 | `v3/geometry.json` | 43 surfaces, 1,183 visible curve anchors | Frozen at source-retrieval handoff, not final painted or accepted |

Frozen v3 manifest SHA-256: `16a7009bc94748390ce0bb99bb5da0cc682c36d8fe9b4a20ee147eba5c19949c`.

Each manifest uses `aikon.semantic-geometry.v1`, original 1280 × 1280 coordinates and per-region `id`, `semantic_role`, `z`, `mask_path`, `d`, `fill_rule`, source method and uncertainty. PNG masks are binary analytical regions, not embedded artwork. Diagnostic SVG/PNG colours deliberately distinguish semantic regions and are not paint proposals.

`underpaints` supply opaque whole-subject, face, frill, blue-material and bow backing shapes. Visible sample masks remain separate so eye/blush colours do not contaminate face-field fitting. The blue backing initially contained hundreds of isolated AA specks; these were removed as components smaller than 26 pixels, with exact changes recorded in `support_cleanup`. Large real gaps remain. Parent supports avoid using visible regions as mutually isolated alpha tiles.

## What was learned

- The right structure is a separately modelled whale head fin, with its own pale folded rim and bow, not generic rear hair.
- The eye shapes are source-derived closed contours; they were never fitted back into ellipses. The face/eye/hairline/chin projection stays in original coordinates. No unique real 3D pitch is inferred.
- A warm-colour predicate such as `R > B + 4` wrongly removes nearly white face and eye rims. A connected bright-face surface fixes the false forelock notches without erasing legitimate glow.
- The slit beginning around `(381,597)` is a tapered dark hair crease, not a white face opening. The white face window starts around y=674. See `fringe-notch-source-crop.png`.
- The side forelock's long lower tip is one continuous surface. Splitting it into an invented back-light patch created spurious geometry. v3 follows its broad observed light/dark interface with three interpretable rear surfaces, rather than a many-colour quantization.
- The fin's pale rim includes an actual folded left lobe; treating all of it as one paint field flattens the source. v3 separates that fold from the broad pale face.

## Evidence limits

`v2/geometry-validation.json` and `v2/core-geometry-comparison.png` compare visible core contours at fixed original coordinates. Against material-segmented r1, v2 face-support IoU is 0.998516; left/right dark eye IoU 0.996375 / 0.995895. Their symmetric contour 95th percentile is 1 pixel. The rejected round-002 short output gives 0.668547 / 0.384394 / 0 for the corresponding fixed-coordinate overlaps. These only prove substantially better positioning/shape reconstruction than that rejected image. They **do not** establish whole-art similarity, natural lighting, a 99% acceptance standard or cross-agent generalization.

The reference masks and current contours both derive from r1, so this is calibration, not an independent generalization test. Internal hair interfaces are partly hand constrained; no trustworthy pixel-gold segmentation is claimed for them. Whole-figure silhouette agreement cannot replace identity or visual review.

`watermark-uncertainty.png` fixes the visibly occluded lower-right area. Its underlying geometry was locally interpolated only for diagnostics and is explicitly uncertain. The source was not edited, the watermark letters never belong to final geometry, and interpolated pixels must not be called original-source pixels. The new authentic-source lead takes priority over this interpolation.

## Reproduction and stopping state

The scripts use the already installed NumPy, SciPy, Pillow and resvg packages; no dependencies were installed. Runs used an external subprocess timeout of 48 seconds and an internal processing budget of 43 seconds; actual geometry runs took about 3–4 seconds. No background service was started.

`extract_geometry.py`, `extract_geometry_v2.py`, `extract_geometry_v3.py` reconstruct their respective snapshot directories. `validate_geometry.py` writes only the v2 comparison evidence. The production parent performs final SVG composition and review separately.

That stop was lifted after the root confirmed the authentic clean source. Only the independent v4 snapshot was subsequently added; v1–v3 were not changed.
