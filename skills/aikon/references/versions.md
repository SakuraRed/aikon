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

For the helper, `snapshot` receives the already chosen project root; it creates an immutable revision with scene, SVG, and a minimal manifest. It does not decide storage policy, collect the entire brief, copy reference images, or claim user approval. Add workflow decisions and visual evidence alongside its files without changing the archived scene/SVG. See [the CLI contract](scene-format.md).

For a precise revision:

1. Read and hash the base. Name targets and the preserve list from actual feedback.
2. Work in a new candidate or revision. With scene data, change the intended parameter or vector path; preserve other values. With direct SVG, target the corresponding semantic group.
3. Compare source structure and actual before/after renders. A changed fill may affect many pixels but should not change unrelated geometry. A crop change intentionally moves more of the portrait; record that wider scope.
4. Save a new revision referring to its real parent. Keep the prior scene/SVG intact. Returning to a prior version is selecting or deriving from it, not rewriting its history.

When the user already manages artifacts with Git, follow their repository workflow and permissions. File snapshots remain useful without Git. A file save, local commit, remote push, and user acceptance are distinct events.
