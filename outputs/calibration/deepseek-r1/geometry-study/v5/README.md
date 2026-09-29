# v5 — upstream RGBA re-execution

The working source is now `ref/subjects/deepseek/cetus-desktop/r1-clean-source-1280.png`, SHA-256 `60c234f594ad81319fa74bb4fa8392f10a125127d46bf1d3b47e618b25813da2`. Both RGB and alpha derive from uniform scaling of the authentic 4096 source. No alpha from the old watermarked r1 is inherited. See `reference-contract-v4.json` in the source directory.

This is an actual fresh geometry run, not a metadata replacement. `extract_geometry_v5.py` retains the v4 geometry algorithm and recomputes all masks, parent supports, curves and diagnostic renders from the corrected RGBA source. One execution took 4.0 seconds under a 43-second internal limit and a 48-second external timeout. It creates 43 visible semantic surfaces, 1,240 curve anchors, five opaque backing supports and a material support of 1,160,068 pixels. There are no watermark exclusions, interpolated areas or image edits.

Frozen manifest SHA-256: `8105b2e6d66b4ff7339302b59bd419df883cf033c0b0a663123989d404443769`.

`regeneration-evidence.json` records exact mask differences and path changes versus the superseded v4 output, together with every new mask hash and the executed script hash. The diagnostic PNG was viewed after execution. The coloured regions are geometric diagnostics, not final paint or a visual acceptance claim.

The previous v4 snapshot remains historical evidence and must not be used as the current reference. Its face/eye contour statistics are not silently attributed to v5. No new design round was introduced; the production parent and paint task use these newly generated v5 paths and masks.

The same 2,801 visible-sample boundary pixels require opaque parent composition and final alpha checking; this is not permission for transparent cracks. Whole-image similarity, natural lighting and final user acceptance remain outside this geometry-only task.
