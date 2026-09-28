# Visual contract — bot portrait v0.1

默认是更强的超近景（extreme close-up）：头部与脸填满主要区域，从左下裁切，眼睛完整且靠近视觉中心偏下。精简版与完整版的具体差异见 [profiles](profiles.md)。用户强模式参考的观感优先；只转移风格，不转移其中的主体身份、黑底或水印。

## Identity versus treatment

Take identity from the target subject: its surface/skin color, hair or covering color, main outline, and at most a few high-value features. Record which features matter before drawing. A bald subject stays bald; a mechanical subject keeps the appropriate surface material/color. A style example contributes composition and shape treatment, not its subject's palette or accessories.

For a faceless entity, choose a round head interpretation and translate recognizable motifs into covering, color blocks or simple attachments. State the intended transformation; do not present inferred features as facts about the source.

## Geometry

Use a square `viewBox` with a **transparent background**. The helper uses a 512-unit square; other coordinate scales are valid when equivalent. 右上保留的 negative space 是透明空白，不能用黑色矩形或内嵌棋盘格冒充。背景只有用户明确要求才添加。

The head enters from the lower left and is large enough for the left and bottom boundaries to cut through its silhouette. The chin reaches or exceeds the lower edge. Retain connected transparent space in the upper right. Keep both eyes fully within the visible canvas. Avoid treating the full head's bounding box as proof of facial crop; inspect the face itself. 避免把双眼放得过高而留下大块无内容的下半脸；必要时共同调整脸部尺度、眼位与裁切，并保持头部坐标一致。

Place exactly two solid dark vertical capsules in the head's local coordinates. They share width, height, fill, and orientation; their centers sit on one horizontal line. The default length/width ratio is 2.5–3. Rotate the entire head group, including both eyes and attachments, clockwise by 15–20 degrees. In SVG's downward y-axis, positive rotation has this visual direction; the screen-left eye should be higher. Check the rendered result when transforms are composed.

可见脸域应宽而柔和，颊与下颌可以具有来源支持的局部转折；它不必须是圆、椭圆或跨主体共用路径。先依据发际线、鬓发及下颌确定可见区域，再安排眼对；不画嘴或鼻。Expression comes from proportion and pose. The capsule itself is the whole eye: keep its interior solid. Use small subdued cheek ovals and clear facial space around them. Glasses and other identity features must leave the two eye silhouettes readable.

## Color and shape economy

完整版保留主体肤色或表面色；精简版按源 profile 使用奶油色脸与柔和粉彩，同时保留关键发色和 silhouette。不要悄悄把两版设成同一个配色规则。主体是概念/物件时说明 profile 如何解释其表面。Separate adjacent forms with fill contrast; a heavy black outline is not the default. Hair or coverings consist of large deliberate curves, with one restrained shadow family and only a few broad highlight shapes if needed.

Keep identifying hardware at silhouette scale. Fine screws, wiring, dense panels, fine strands, and tiny decorative marks usually compete with the face at icon sizes. Check at the target size before preserving them.

让自然发束具有不规则、顺着发流的弧线，避免把短发简化成等间距机械尖齿。为露出双眼而调整的眼罩等附件，应读作独立身份配件，而非新增眉毛。物件拟人化的腹纹、接缝或浅色弧带也可能被看成嘴，必须以实际观感检查无口脸，不能仅凭图层命名排除这一问题。

The portrait contains no hands or body. A small collar fragment may remain only when it carries a chosen identity cue without weakening the close crop. Keep background texture, badges, words, logos, watermarks, flares, and particles outside the default artwork.

## Conflict resolution

Keep the eye pair readable and the simplified face intact. Adjust the position or contour of hair and attachments before letting them obscure the eyes. Preserve identity through a few selected cues rather than adding every source detail. If preserving a user-locked feature makes the default composition impossible, show that conflict and ask which constraint may change.

## Measured versus chosen

The included examples are original design studies, not measurements of a reference website. Exact eye spacing, crop amount, face outline, palette, and control points are design choices. Record them in the current scene for repeatable export. A valid geometry contract reduces drawing variance; it does not guarantee all models infer the same identity cues.
