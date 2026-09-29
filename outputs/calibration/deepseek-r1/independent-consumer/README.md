# Independent short consumer experiment

Final candidate: `short.svg` (v2); visual status is **reviewed, not accepted**. `v1/` and `v2/` preserve both real SVGs and renders. This bounded run used one initial drawing and one local revision.

## Inputs and assistance

The only image used during authoring was `ref/subjects/deepseek/cetus-desktop/r1-clean-calibration-1280.png`, actually viewed before source construction. After drawing, the root agent superseded it with `ref/subjects/deepseek/cetus-desktop/r1-clean-source-1280.png`, whose RGBA comes entirely from uniform scaling of the original 4096 image. I actually viewed the replacement. The root reported unchanged subject RGB and removal of an erroneous old alpha/watermark residue. No old alpha, black display background, watermark or pixel samples were transferred into the SVG. All paths and colors were independently estimated visually. The original 4096 file and original user r1 were supplied but not opened by this consumer.

`read-log.json` lists skill/rule files actually read. No other calibration SVG, geometry manifest, paint field, fixture drawing code or other agent artifact was opened. Process inventory incidentally exposed other task filenames and command lines; their content and parameters were not used. No external drawing service, tracing library, quantization trace, geometry detector, pixel fitting, evaluator or alternate model was used. This measures a single agent's skill consumption under an unusually specific brief, not arbitrary-model or cross-model validation.

The actual prompt was saved before each source edit. The prompt is in English in this experiment; it is not a claim that the skill's Chinese production-prompt convention was followed. Historical prompts remain unchanged after input replacement.

## Construction and reproduction

The artwork contains 37 semantic paths, 11 analytic gradients and two cheek ellipses. Eyes are cubic capsule paths, with separately addressable narrow material rims and opaque inner surfaces. No eye is an ellipse. SVG has no background fill, embedded bitmap, remote resource, filter, pattern, pixel tile, script or watermark. Groups separate rear hair, whale fin, headdress, face, bow, front hair, eyes and cheeks.

Run the delivered `generate_v1.py` and `generate_v2.py` in this directory with the repository's existing verification Python. Each command must have an external hard timeout of at most 45 seconds. `generate_v2.py` imports the immutable v1 SVG string from the root-level generator and applies four explicit replacements. The archived `v1/source.py` and `v2/revision-source.py` are snapshots, not separate entry points. No bitmap is read by either generator. Rendering uses the allowed common `tools/render_svg.py` and its pinned `resvg-py 0.5.0` backend; no dependency was installed.

The first attempted prompt-writing shell snippet failed with a quoting SyntaxError before writing anything. The actual prompt was then successfully saved by apply_patch before the SVG source. The first process inventory attempt also failed due to PowerShell interpolation; a later one succeeded. These failures did not create alternate artwork.

## Material reasoning

| Material / region | Field and structural anchor |
| --- | --- |
| Front blue hair | Broad top-dark to bottom-light linear fields; main fringe, left sweep and outer side mass have editable boundaries. |
| Rear hair / whale side fin | Darker blue fields behind the side fringe and bow; pale underside follows the fin's actual lower boundary. |
| Face | One broad warm radial field on an opaque semantic face path; the two peach wedges sit under actual fringe occlusions. |
| White headdress | Pale cloth gradient on scalloped shapes over lavender folded cloth. No white shape is treated as a hair highlight. |
| Blue bow | Broad blue field, one darker lower fold and two small knot folds attached to the knot. |
| Eyes | Dark-blue continuous field with a narrow integrated rim; no independent white dot or pupil. |
| Cheeks | Solid pale pink ovals. |

## Actual visual review and remaining defects

I viewed the v1 1280 and 128 PNGs. Main positions and subject cues were recognizable, but the eye rims were too conspicuous and the center-fringe right shadow was too heavy. The saved v2 prompt limited changes to eye inner fill/rim tone and that one shadow path. Other paths and fields remained unchanged.

I then viewed v2 at 1280 and its review sheet containing light/dark compositions at 512 plus actual 128/48/24 sizes. Eyes and headline silhouette remain readable at the small sizes; frill, bow and side fin simplify naturally. No grain, sparkles, bitmap blocks or dark background rectangle are visible. The transparent upper-right pixel is RGBA (0,0,0,0).

Unresolved: v2 leaves a thin light sliver beside the revised central-fringe right shadow around the lower diagonal hair/face boundary. The straight-sided capsule interpretation is slightly more geometric than the reference's subtly convex sides. The lower-left jaw, lower rear hair crop, bow/fin curvature, white-fold boundaries and broad face/hair illumination remain manual approximations. The fin's pale underside is simpler than the source. These differences matter for very high fidelity. No similarity percentage, aesthetic pass, human acceptance or exact match is claimed. The one-revision budget is exhausted, so these issues are recorded rather than hidden by further edits.

Structural report and renderer hashes are saved, but no complete owner-mask or interior-alpha audit was performed. Fractional alpha counts include silhouette antialiasing and are not a proof of clean material interiors. PNG metadata/structural validation does not establish visual acceptance.

Hash note: generator stdout and the v2 historical prompt identify the in-memory LF-normalized SVG string; Windows text writes use CRLF on disk. The renderer's `source_sha256` and `hash-manifest.json` are the authoritative actual file-byte hashes. The final file hash is `0e182ecda410867351aa6b88e2449a3f2927c06704150263fcf95d91aa76ebc9`.

## Files

- `short.svg`: latest candidate, identical to `v2/short.svg`.
- `preview-1280.png`, `preview-128.png`, `preview-48.png`, `preview-24.png`: actual transparent renders.
- `review-sheet.png`, `preview-light.png`, `preview-dark.png`: review compositions only; their backgrounds are not embedded in SVG.
- `prompt-v1.txt`, `prompt-v2.txt`: actual prompts saved before execution.
- `generate_v1.py`, `generate_v2.py`: deterministic authoring source.
- `read-log.json`, `structural-checks.json`, `process-inventory.json`, `final-process-audit.json`, `hash-manifest.json`: evidence and handoff.

No server, browser or background process was started for this run. All drawing/rendering commands completed as bounded one-shot subprocesses. Existing unrelated processes were not terminated. Nothing outside this assigned output directory was intentionally modified.
