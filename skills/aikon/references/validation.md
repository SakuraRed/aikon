# Validation and feedback

Keep structural, visual, and human checks separate. Report only the checks actually completed and the input version they apply to.

## Before rendering

Use the helper's `check` when available, or inspect the SVG directly. Require static self-contained vector geometry, a square viewBox, explicit colors, and stable semantic groups. Final art must not be an embedded or remotely referenced bitmap. Active content, event handlers, and externally fetched resources are outside the portable output subset.

Check geometry relevant to the current contract: identical capsule dimensions, expected ratio, shared pose, fully visible eyes, and resolved deviations. Structural checks cannot prove that two marked objects are the only visible eyes or that a dark hair shape does not obscure them.

`aikon.py check` applies to its scene/export subset. For the analytic paint path, use `paint_svg.py`'s compile report followed by an actual renderer; do not assume the older scene checker accepts every gradient/clip used by the paint compiler. A compile report alone has not run pixel or visual checks.

## Paint checks

Apply [paint anti-patterns](paint-antipatterns.md) and the [paint plan](paint-plan.md) before drawing. When pixel tools are available, rasterize every selected layer with its real transform and clipping, then account for draw order to identify visible material. Inspect whole surfaces, not only small easy patches; disclose any excluded boundaries and insufficient samples.

Treat grain, mid-scale mottling, unexpected islands in declared smooth fields, opaque-interior alpha and boundary-connected shadows as separate checks. Keep legal gradient/antialiasing controls and known bad cases. Freeze reference-derived limits before measuring candidates. Do not lower limits just to reject one image or raise them to pass another. A shadow's owner/reason text does not prove its geometry or lighting is correct.

Highlight naturalness remains a visual judgment. A narrow shadow can have enough coverage for an anchor check but too little interior for texture analysis; record that gap. A soft defect below a calibrated threshold is undetected, not accepted. No renderer or numerical dependencies are required for basic SVG authoring; if unavailable, retain these checks as not run.

## Actual visual inspection

Render with an available trusted local browser or SVG renderer and view the result. Record renderer/version when obtainable, canvas size and background. Use the intended output sizes; if unspecified, inspect at 24, 48, and 128 px plus one large view. These are Aikon's default review sizes, not thresholds measured from third-party examples.

每个 round 的 short/full 分别检查。把同一 SVG 放在浅色、深色和棋盘格预览底上，确认底色透出、边缘没有黑底残块；展示底不得嵌入输出。若可将 SVG 渲染到透明 canvas，读取空白区域实际 alpha，记录像素检查与结构检查的区别。确认画面和源码都没有水印、署名或意外文字；用户明确要求的标记另记。

Review four independent questions:

1. **Style:** do the eye pair, round sparse face, direction, close crop and upper-right space read together?
2. **Identity:** are the selected source cues present without importing a style sample's identity?
3. **Clarity:** are the eyes and important silhouette readable at the actual display size, with no accidental tangencies, missing fills or clutter?
4. **Change scope:** did a revision preserve the requested invariants and alter only the intended parts?

Where a check fails, identify the responsible geometry or constraint and make one targeted correction. Recheck affected sizes and neighboring shapes. Do not relax acceptance criteria after seeing a failure without recording a changed user requirement.

## Missing capabilities

If no renderer is available, preserve the SVG and mark `visual_review: not_run`; offer it for user preview. If a renderer exists but images cannot be viewed, a generated PNG is not evidence that it looks correct. A user can supply feedback to continue. Do not install an unrequested drawing service just to hide this limitation.

## Independent forward tests

For substantial skill changes, give an independent evaluator the skill folder, a realistic request, and only the necessary raw references. Keep expected answers and prior failure diagnoses out of that brief. Inspect its actual artifacts, then fix demonstrated problems. Include text-only subjects, role-separated images, darker skin, bald/mechanical subjects, faceless entities, explicit output paths, unanswered choices, and scoped edits as coverage expands.

Several agents on the same model measure behavior variability, not cross-model compatibility. To claim cross-model consistency, run the same source brief and settled decisions in named harness/model versions and compare contract adherence, exported geometry, rendered results, and human judgments separately. Equal scene input can reproduce SVG bytes; different model interpretations need their own evaluation.
