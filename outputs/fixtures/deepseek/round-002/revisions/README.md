# Revision evidence

`r003` archives the current candidate's actual SVGs, 1024 renders, original execution prompts, generator and design record. These are byte copies of existing files, not recreated earlier results.

Audit limitation: the first two intermediate candidates were rendered and viewed, then overwritten before per-revision archival was introduced. Their historical renderer hashes remain in the session tool records, but those intermediate files are not claimed to exist here. The visual correction history in the round README is retrospective, not a claim that a separate revision prompt was saved before each early edit.

Future edits start from this saved candidate and must save the concrete revision prompt before execution. No user acceptance has been recorded.

`r004` is the narrowly scoped full-only alpha-seam repair authorized after independent review. Its revision prompt was saved before editing. The added opaque material underlap changes 134 pixels in the 1024 render; the originally reported 19 nonopaque interior pixels become alpha255. Short SVG and all four short PNGs remain byte-identical to rendering the archived r003 short SVG. `repair-check.json` records actual hashes and comparisons; independent checking is a separate result.
