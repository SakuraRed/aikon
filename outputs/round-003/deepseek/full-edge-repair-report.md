# Full frozen-edge targeted repair — partial, not passed

Two bounded repair attempts were actually generated and checked. After actual parent review, root `full.svg` now aliases r006 as the **current draft**, SHA-256 `ff3197cd7d083ff4e8a697bf5e3437bf4af7600259ce3276ba638928c1dc950d`. Its local color-edge gate still fails; this is not a passing or user-accepted replacement. r004/r005 remain preserved. Short and all gate code/rules remain unchanged.

## Actual results

| Frozen 256px SVG edge check | r004 baseline | r005 | r006 |
|---|---:|---:|---:|
| Interior alpha bad pixels | 4 | 3 | 0 |
| Maximum interior deficit, 0–255 | 43.5625 | 16.0000 | 0.0000 |
| Largest local bad-color cluster | 19 | 7 | 10 |
| Frozen gate status | fail | fail | fail |

The local cluster limit stays 3 original bad pixels at the existing >32/255 error cutoff; no masks, thresholds, size, renderer or comparator changed. r005 clears the existing interior-alpha gate because it allows at most 3 bad pixels; this is not a claim of zero deficit. r006 actually reaches zero interior-alpha deficit in this check.

## What was changed

r005 groups the original major hair materials under one original-geometry owner clip, adds an 8-raw-unit stroke using each part's existing gradient as bounded opaque material support, and applies analogous face support. All original path d values and gradient definitions remain unchanged; the extra strokes are implementation support clipped by the owner, not an instruction to flatten the colors. A navy shoulder-neck support sits under existing head and clothing. This reduces repeated edge coverage across the hair/face seam and lowers the largest cluster from 19 to 7.

r006 shares the original face-plus-hair union as a head owner, lets face support cover the interior beneath the hair, and narrows the shoulder support. This removes all measured interior-alpha deficits, but the largest remaining color cluster increases from 7 to 10 and shifts to the hair crown against the white headband. The current nested head/hair clips likely repeat antialiasing at the external crown boundary; this is a source-structure diagnosis supported by the crop, not an independently proven complete renderer root cause. A future repair should specifically reconcile those owner boundaries rather than further dilate every material.

## Exact remaining locations

Coordinates below are the unmodified gate's 256px grid, half-open boxes. Multiply by 5 to locate the same area in the 1280 artwork; no registration was performed.

- r005: 7 pixels at `[121,147,122,154]`, right face/side-lock boundary; 5 pixels at `[2,107,3,118]`, left face/hair edge.
- r006: 10 pixels at `[128,69,138,88]`, right crown/white headband boundary; 8 pixels at `[82,38,98,45]`, upper crown/headband; 5 pixels at `[10,36,21,40]`, upper-left crown/headband.

All gate-generated reports, native/supersampled references, masks and local crop boards are in each revision's `edge/`. Baseline root evidence was read, not overwritten.

## Eye geometry and actual inspection

For r005 and r006, existing `review_gloss_pairs._eye_markup` generated both isolated and actual-visible 1024px depth mattes. Unmodified `analyze_capsule_geometry.analyze_pair` returned `no_rule_failure` for both eyes under both modes. Visible coverage contains 100% of the isolated primary-eye coverage. Visible mattes include the integrated `eye-*-rim` layer and therefore have extra edge mass; the nonzero absolute mask differences are recorded, not described as exact equality.

Actually viewed baseline gate local/worst-edge crops and overview; r005 full1280 and its local residual crop; r006 full1280, local residual crop, 128/48/24 on light/dark/gray and a three-revision comparison. At normal viewing size, identity and clothing remain readable; these observations do not override the failed edge result. No white eye points, new clothing or background fill were added.

## Reproduction and hashes

- r005 generator: `full-edge-fix.py`; SVG: `full-revisions/r005/full.svg`; SHA-256 `741eb90c1b1c4823d75ea7ba9bffc0e2d7c36b182ef81159e148a12ae19e36e7`.
- r006 generator: `full-edge-fix2.py`; SVG: `full-revisions/r006/full.svg`; SHA-256 `ff3197cd7d083ff4e8a697bf5e3437bf4af7600259ce3276ba638928c1dc950d`.
- Gate command: existing Python `tools/analyze_edge_quality.py --svg <candidate> --size 256 --output <revision>/edge`; existing 45-second bounded worker behavior retained.
- Isolated/visible eye and small-view evidence: `full-edge-qa.py`, each revision's `capsule/report.json`, mattes and `inspection-board.png`.

Every candidate has the actual pre-generation prompt, exact source snapshot, SVG, and 1280/128/48/24 PNGs. The parent explicitly chose r006 after viewing it because its measured interior alpha deficit is zero and its largest local cluster is lower than r004 overall. `promote-full-r006.py` only copies aliases and updates matching previews/records; it does not generate r007 or alter artwork bytes. No third repair, heavy test suite, network, Git mutation, source-data alteration or persistent process was used. This task ends with an unresolved local color-edge gate and preserved evidence.
