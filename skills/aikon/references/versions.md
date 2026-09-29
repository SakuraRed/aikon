# Project and revision handling

Respect the location and format the user supplies. At a new project with no storage choice, ask once before persisting project artifacts. Offer a structured project folder as the default recommendation, explain its extra files, and remember the actual answer. Do not auto-initialize or push a Git repository.

A practical layout for structured storage is:

```text
<chosen-project>/
  rounds/
    round-001/
      brief.json
      references/          # chosen copies or provenance pointers
      short/
        prompt.zh-CN.md
        revisions/r001/
          scene.json       # optional in direct-SVG workflow
          icon.svg
          revision.json
          preview.png      # actual review evidence, if available
          feedback.md
      full/
        prompt.zh-CN.md
        revisions/r001/    # same files, full profile
```

Alternative layouts and a single SVG workflow are valid user choices. Be clear when those choices do not preserve previous states. Never overwrite an existing user artifact merely because its name matches an example.

The minimum record identifies the round, profile (`short` or `full`), revision, parent, subject and style sources, settled decisions, changed parts, preserved parts, generating method/version, content hashes where possible, and actual validation status. 两版共用已确认主体，但分别存生产提示词与产物。Keep reference observations distinct from user choices and agent defaults. Record the source/permission status before copying third-party images into a shared deliverable.

For current direct SVG, [archive_svg.py](direct-svg-archive.md) receives the already chosen profile root and preserves the SVG, actual prompt and metadata bytes with raw-file hashes. Local gradients and clips are supported; no renderer or drawing model is required for archiving. The older scene helper's `snapshot` recreates its restricted scene v1 SVG and remains available for those existing scenes. Neither helper decides storage policy, copies external references or claims user approval. Add actual visual evidence and human feedback alongside the immutable archive, tied to its hashes.

For a precise revision:

1. Read and hash the base. Name targets and the preserve list from actual feedback.
2. Work in a new candidate or revision. With scene data, change the intended parameter or vector path; preserve other values. With direct SVG, target the corresponding semantic group.
3. Compare source structure and actual before/after renders. A changed fill may affect many pixels but should not change unrelated geometry. A crop change intentionally moves more of the portrait; record that wider scope.
4. Save a new revision referring to its real parent. Keep the prior scene/SVG intact. Returning to a prior version is selecting or deriving from it, not rewriting its history.

When the user already manages artifacts with Git, follow their repository workflow and permissions. File snapshots remain useful without Git. A file save, local commit, remote push, and user acceptance are distinct events.
