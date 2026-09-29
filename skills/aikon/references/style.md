# Visual contract — bot portrait

当前用户选择为 [natural-gloss-v2](natural-gloss-v2.md)。r1及新full参考中的连续渐变、头发受光和暗色眼缘光泽是目标的一部分；下文保持capsule语法，旧纯色眼默认已被显式覆盖。

默认是更强的超近景（extreme close-up）：头部与脸填满主要区域，从左下裁切，眼睛完整且靠近视觉中心偏下。精简版与完整版的具体差异见 [profiles](profiles.md)。用户强模式参考的观感优先；只转移风格，不转移其中的主体身份、黑底或水印。

## Identity versus treatment

Take identity from the target subject: its surface/skin color, hair or covering color, main outline, and at most a few high-value features. Record which features matter before drawing. A bald subject stays bald; a mechanical subject keeps the appropriate surface material/color. A style example contributes composition and shape treatment, not its subject's palette or accessories.

For a faceless entity, choose a round head interpretation and translate recognizable motifs into covering, color blocks or simple attachments. State the intended transformation; do not present inferred features as facts about the source.

## Geometry

Use a square `viewBox` with a **transparent background**. The helper uses a 512-unit square; other coordinate scales are valid when equivalent. 右上保留的 negative space 是透明空白，不能用黑色矩形或内嵌棋盘格冒充。背景只有用户明确要求才添加。

The default short head enters from the lower left and is large enough for the left and bottom boundaries to cut through its silhouette. The chin reaches or exceeds the lower edge. Retain connected transparent space in the upper right. Keep unmasked eyes fully within the visible canvas unless an explicit reference contract says otherwise. Avoid treating the full head's bounding box as proof of facial crop; inspect the face itself. 避免把双眼放得过高而留下大块无内容的下半脸；必要时共同调整脸部尺度、眼位与裁切，并保持头部坐标一致。

For an unmasked face, retain two dark capsules. The source default uses equal dimensions and a shared local eye line; the current contract may explicitly preserve a reference's projected differences. Its default length/width ratio is 2.5–3; a strong reference can set a shorter capsule. Preserve the observed face, eye, fringe and chin relationship: rotating a front-facing face only supplies roll, not upward pitch. A subtle dark gradient and thin integrated rim may follow the current reference; no pupil, iris, separate white catchlight dot or eyelid. A selected occluding mask retains its real position and records the exception to eye visibility.

可见脸域应宽而柔和，颊与下颌可以具有来源支持的局部转折；它不必须是圆、椭圆或跨主体共用路径。先依据发际线、鬓发及下颌确定可见区域，再安排眼对；不画嘴或鼻。Expression comes from proportion and pose. The capsule itself is the whole eye; gentle material gloss must not create another eye structure. Use small subdued cheek ovals and clear facial space around them. Glasses and other identity features must leave the two eye silhouettes readable.

## Color and shape economy

完整版保留主体肤色或表面色；精简版按源 profile 使用奶油色脸与柔和粉彩，同时保留关键发色和 silhouette。不要悄悄把两版设成同一个配色规则。主体是概念/物件时说明 profile 如何解释其表面。Separate adjacent forms with fill contrast; a heavy black outline is not the default. Hair or coverings consist of large deliberate curves, with one restrained shadow family and only a few broad highlight shapes if needed.

Keep identifying hardware at silhouette scale. Fine screws, wiring, dense panels, fine strands, and tiny decorative marks usually compete with the face at icon sizes. Check at the target size before preserving them.

让自然发束具有不规则、顺着发流的弧线，避免把短发简化成等间距机械尖齿。面具/眼罩是否保留由实际分支决定，不能为了露眼擅自搬成额饰。物件拟人化的腹纹、接缝或浅色弧带也可能被看成嘴，必须以实际观感检查无口脸，不能仅凭图层命名排除这一问题。

The short portrait omits hands and body. The current full profile intentionally includes more evidenced neck, collar and clothing within the same canvas; its framing follows the user's full references, rather than the short close crop. Keep background texture, words, watermarks, flares and particles outside the default artwork; retain identity hardware when actually required.

## Conflict resolution

Apply the settled reference and branch decisions first. Keep visible capsules readable and the simplified face intact, but do not move a selected identity mask to satisfy an older eye-visibility default. Preserve the actual shape and connections of the few key identity cues. Ask only about a consequential conflict that the user has not already resolved; an explicit user choice is itself the applicable override.

## Measured versus chosen

The included examples are original design studies, not measurements of a reference website. Exact eye spacing, crop amount, face outline, palette, and control points are design choices. Record them in the current scene for repeatable export. A valid geometry contract reduces drawing variance; it does not guarantee all models infer the same identity cues.
