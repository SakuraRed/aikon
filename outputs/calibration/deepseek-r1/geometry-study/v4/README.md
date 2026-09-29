# v4 — authentic clean-source geometry

This is a calibration geometry snapshot, not a finished icon or a 99% acceptance claim. The original `cetus-desktop` artwork supersedes the former watermark interpolation. Previous snapshots remain historical failure evidence.

- Reference: `ref/subjects/deepseek/cetus-desktop/r1-clean-calibration-1280.png`.
- Reference SHA-256: `54de4e5b25db9a7520e3a6422552d4a55da0a6a9122bb856c54c4349bf2b7712`.
- Frozen `geometry.json` SHA-256: `459b11e8734a25f8bf285f256dadf9c70d2833c425257aa21154a32cce4963d1`.
- Contract: upstream-only RGB, uniform 4096 → 1280 normalization, user r1 presentation alpha; no local repaint or denoise.
- Watermark exclusion: **none**. Interpolated geometry: **none**. `watermark_uncertainty_mask` is explicitly `null`, not a signal to fall back to an old ROI.

## Actual inspection and changes

The 1280 reference and the two saved high-resolution local crops were viewed. The high-resolution images were cropped only for visual evidence; segmentation operates on the 1280 working reference.

1. The lower-right rear-hair silhouette and all exposed rear-hair regions now come from actual source pixels. No old watermark rectangle is consulted.
2. The pale fin rim is two interpretable folded surfaces. Its inner division starts around `(1051,1056)` and curves toward `(1137,1096)`; a short straight triangular cut would leave much of the darker upper fold in the wrong paint field. `whale-fin-rim-left-fold` includes that curved upper strip, while `whale-side-fin-rim` is the broad pale lower face.
3. Actual hairline creases remain connected to their face/hair junctions. The dark central slit starts above the pale face window; it is not an expanded skin hole.
4. The major side forelock continues into its long lower tip as one material face. Rear light/dark regions follow source-supported large interfaces, not colour quantization or texture islands.

The manifest has 43 visible semantic regions and 1,235 curve anchors, with five opaque parent backing supports. Masks retain original coordinates. `mask_path` is relative to this directory. Every visible path has a role, source method and uncertainty statement. Because masks describe visible paint samples rather than full concealed anatomy, the parent compositor must use the supplied opaque supports and validate actual alpha; 2,801 material-boundary pixels are outside the visible sampling regions after regularization, and must not become transparent cracks.

## Bounded verification

`geometry-validation.json` compares the face and dark-eye contours to independently re-extracted bright/dark connected regions in the clean working source, using the same original coordinates and no registration. The source-derived reconstruction shares its source with this check, so this is calibration evidence, not generalization evidence.

| Contour | Current mask IoU | Rejected round-002 mask IoU | Current symmetric contour P95 |
| --- | ---: | ---: | ---: |
| Visible face support | 0.998548 | 0.668523 | 1 px |
| Left dark capsule eye | 0.996775 | 0.384372 | 1 px |
| Right dark capsule eye | 0.995525 | 0 | 1 px |

These measurements do not certify pose, material gloss, whole-icon similarity or final user acceptance. Internal blue boundaries still include explicit human geometric constraints. The diagnostic colours intentionally distinguish geometry and are not a paint proposal.

One v4 geometry execution took 4.1 seconds, under a 43-second internal limit and a 48-second external timeout. The separate contour verification took about 2 seconds. No service, browser or dependency installation was started. The reference and original files were not modified.
