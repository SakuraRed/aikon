# Existing SVG: static checks and revision archive

Use `scripts/archive_svg.py` when the artwork already exists as directly authored SVG, including the current local gradients and clipping. It needs Python 3.9+ and its standard library only. It does not call a renderer, drawing model, network service, Git, or another skill. It never redraws, sorts, normalizes, flattens, or serializes the input SVG.

Use the storage location and revision strategy the user already chose, following [version handling](versions.md). A path in the examples is not permission to choose that path for a user. Preserve a displayed or reviewed base **before** running a generator that might overwrite it. Save the actual new prompt before drawing; archiving a prompt later does not prove it was saved before generation.

## Commands

Run from the skill directory, replacing the paths with actual chosen inputs and the chosen profile directory:

```text
python scripts/archive_svg.py check --svg candidate.svg
python scripts/archive_svg.py snapshot --svg candidate.svg --prompt prompt.zh-CN.md --metadata metadata.json --root <chosen-profile-directory> --revision r001
python scripts/archive_svg.py snapshot --svg revised.svg --prompt revision-prompt.zh-CN.md --metadata revision-metadata.json --root <same-chosen-profile-directory> --revision r002 --parent r001
```

`check` writes JSON and returns 0 for the supported structure, 1 for failure. `snapshot` validates all inputs before writing and creates:

```text
<chosen-profile-directory>/revisions/r001/
  icon.svg
  prompt.md
  metadata.json
  revision.json
```

The first three files preserve their input bytes exactly, including IDs, attribute order, comments, UTF-8 BOM and line endings. The generated `revision.json` records their raw-byte SHA-256 hashes and sizes, round/profile, revision/parent, UTC archive time, helper version and actual check status. Hashes detect changed content; they do not authenticate an author, establish rights or prevent edits outside the helper.

Revision IDs are `r` plus 3–31 digits. Existing revision paths, including empty directories, are refused. There is no replace option. The helper creates only the explicitly chosen root and revision directories when needed, rejects `..`, symlinks and Windows reparse points in the output directory chain, and exclusively creates files. It does not change the source files or automatically select a next ID. Parent revisions must be completed archives made by this tool, belong to the same round/profile, and still match their recorded content hashes. The new manifest also hashes the parent manifest. An old scene-v1 revision can remain alongside these archives, but is not accepted as a direct-SVG `--parent`; preserve the actual old SVG as a first direct archive and describe that provenance.

Handled validation/write failures remove only files and empty directories created by this invocation. `revision.json` is written last as the completion marker. Sudden power loss, a forced process kill or a filesystem failure during cleanup can leave an incomplete directory. If both descriptor identity queries fail after creating a file, ownership cannot be verified for deletion; it is also retained. Inspect and preserve/recover incomplete directories explicitly rather than retrying with overwrite. This is an append-only helper convention, not filesystem write protection, a transactional database or protection against a hostile concurrent local writer.

## Metadata supplied by the caller

Each input file is limited to 2 MiB and must use UTF-8 (BOM allowed). The prompt must contain actual text. Metadata uses the following schema; replace illustrative values with facts rather than adopting them as choices:

```json
{
  "schema": "aikon.direct-svg.metadata.v1",
  "round_id": "round-001",
  "profile": "short",
  "subject": "Example subject",
  "sources": [
    {
      "role": "both",
      "location": "references/user-supplied-reference.png",
      "rights_status": "User-supplied; redistribution permission unknown",
      "purpose": "Subject identity and surface treatment",
      "visual_selection_reason": "Caller observed the silhouette and broad highlight"
    }
  ],
  "decisions": [
    {
      "id": "background",
      "value": "transparent",
      "origin": "agent_default"
    }
  ],
  "unresolved_questions": [],
  "changes": {
    "summary": "First saved candidate",
    "targets": ["hair", "eyes"],
    "preserved": []
  },
  "provenance": {
    "method": "direct SVG authoring",
    "tool": null,
    "version": null,
    "model": null
  }
}
```

Required top-level fields are `schema`, `round_id`, `profile`, `sources`, `decisions`, `changes`, and `provenance`. Optional fields are `subject`, `notes` and `unresolved_questions`. Unknown fields, duplicate JSON keys and non-finite numbers fail rather than silently disappearing. `round_id` uses 1–64 ASCII letters/digits/underscores/hyphens, beginning with a letter/digit; `profile` is `short` or `full`. The caller creates both profiles where the workflow requires them; this tool archives one real file at a time and does not infer profile distinction from labels.

- Each source requires `role` (`subject`, `style` or `both`), `location`, and `rights_status`. Optional fields are `sha256`, `acquired_at`, `purpose` and `visual_selection_reason`. Locations are inert provenance pointers; the helper neither opens URLs nor copies references. Record acquisition time and observed selection reason when available. Do not assert ownership or permission without evidence.
- Each decision requires a unique `id`, its JSON `value`, and `origin` (`user`, `reference_observation` or `agent_default`); optional `evidence` is a text pointer. Unanswered questions belong in `unresolved_questions`; do not invent an answer. Empty source/decision lists are permitted when they accurately describe the input.
- `changes` requires a nonempty `summary` and arrays `targets` and `preserved`, naming the actual requested changes and invariants. On a revision, read the selected base and record the real feedback; the helper does not compare images or certify preserved geometry.
- `provenance` requires `method`, `tool` and `version`; unknown tool/version remain `null`. Optional `model` may also be `null`; optional `script_sha256` identifies a known generation script. SHA fields use 64 lowercase hexadecimal characters. These are caller statements, not verified generation history.

The metadata is validated without rewriting it. Caller-supplied status/approval fields are not part of this schema. The archive always records `user_acceptance: "unassessed"`, `visual_review: "not_run"`, and unverified visual/raster-alpha checks. A previous or later real human decision should be kept in separate feedback/evidence tied to these hashes; the archive tool never manufactures that decision.

## Supported static subset

The root is a namespace-qualified SVG with a positive square `viewBox`. Supported elements are `svg`, `defs`, `g`, `path`, `rect`, `circle`, `ellipse`, `line`, `polygon`, `polyline`, `linearGradient`, `radialGradient`, `stop`, `clipPath`, `title`, `desc`, and plain-text `metadata`. IDs are preserved and must be unique. Inert `data-*` attributes are permitted; custom namespace elements and nested metadata vocabularies are outside this subset.

Supported presentation attributes include explicit hex colors (3/4/6/8 digits), comma-separated `rgb()`/`rgba()` with finite channels (0–255 or consistently 0–100%, alpha 0–1 or 0–100%), `black`, `white`, `transparent`, `none` where applicable, fill/stroke opacity, stroke width/caps/joins/miterlimit, fill/clip rules and local clipping. Geometry lengths accept finite unitless numbers or percentages; CSS length units, other named colors and other CSS color grammars are outside this version. Coordinates, path numeric tokens, viewBox values, opacity/offset ranges and basic required shape attributes are checked. Paths must begin with moveto and use supported commands/finite numbers; **this is not a full SVG path grammar or geometric correctness check**. Zero-size shapes and renderer-dependent clipping can still be visually empty.

Transforms support finite `matrix`, `translate`, `scale`, `rotate`, `skewX` and `skewY` parameters, including lists of transforms. Local linear/radial gradients support coordinate attributes, units, spread method, transforms, `sRGB`/`linearRGB` color interpolation and local `href`/`xlink:href` inheritance. Omitted stop offsets retain SVG's default of zero. `fill`/`stroke` URL targets must be gradients; `clip-path` targets must be `clipPath`. Every reference must resolve locally to the appropriate element type. Gradient and clip cycles, including references from within a clip's descendants, fail. Limits are 10,000 elements, 64 nesting levels, and 65,536 characters per path.

The subset rejects bitmap/image elements, scripts, event attributes, CSS/style, foreign content, animation, filters, patterns, masks, `<use>`, external resource references, DTD/entity declarations and processing instructions other than the UTF-8 XML declaration. Legitimate SVG outside the documented subset may fail; do not simplify the user's artwork solely to satisfy this helper. Use another appropriate check or record that this check was not applicable.

## What a passing archive means

It establishes that the preserved bytes passed this static-subset check and were saved without an existing revision being overwritten. It does not establish visual quality, source fidelity, transparent rendered pixels, no watermark drawn as paths, natural highlights, a meaningful short/full difference, user acceptance or consistency across models/harnesses. Continue the real render–inspect–feedback cycle in [validation](validation.md), recording the available renderer and evidence separately.
