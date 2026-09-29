# Native interaction

The primary agent owns user interaction. Delegate reading, vector work, or independent review when useful; subagents may not have a native question tool and must not impersonate user answers.

## Discover capabilities

Inspect the tools actually exposed in the current session. Possible names include `request_user_input`, `AskUserQuestion`, and `question`; names are hints, not a universal API. Follow the actual schema, mode restrictions, and result shape. Do not inject unsupported IDs, multi-select fields, timeout fields, or invented tool names.

Keep an internal mapping from stable `question_id` / `option_id` to the labels or text sent to the host. This matters when answers return by question text or option label instead of ID. Retain custom free text.

If a native tool is unavailable, ordinary concise chat is a fallback unless the user specifically requires native questions. With a native-only requirement, explain the actual failure and keep the decision pending; do not silently replace it with another form. Ask no questions that the supplied brief already answers.

## Current frontier

Ask only questions whose prerequisites are known. Good independent dimensions include:

- Which identity cues must survive simplification: silhouette, a distinctive attachment, or a color pattern?
- Which still-open detail should differentiate the candidate set: fringe shape, attachment treatment, or crop strength?
- What display context matters: tiny chat avatar, profile card, or larger decorative icon?
- For a new unspecified project, where should files live and how should revisions be preserved?

Do not re-ask the default eye grammar, crop direction, or background on every job. Ask about these when the user requests a change, a source conflict makes the choice material, or the intended use requires a different variant. Avoid bundling color, hairstyle, and crop into one “style” choice.

Present two or three clear alternatives when they cover the decision, with the recommended choice first and a concrete cost for each. Respect the host's own option and batch limits. Shared facts can support a batch; dependent questions wait for the preceding answer.

Prefer one batch containing all currently independent material questions, up to the actual tool's capacity, when the user wants efficient collection. Do not split a supported batch merely to ask one question at a time, re-poll settled choices, or invent questions to fill the limit. With a blocking native tool, call it directly without an Agent-side deadline for human answers. If no wait-duration parameter exists, do not invent one or claim the host's own timeout is disabled. A display failure is not a preference; preserve the exact result and resume unanswered items when the user requests it.

## Probability and answer provenance

Recommendations normally use observed facts and tradeoffs. If an optional judgment service is available and authorized, attach its actual conditional probability to the matching option ID and disclose the question being judged. Mark unscored options as unscored. A score or confidence value is not a success probability.

Record an actual answer as `answered`. Empty answers, cancellation, host auto-continue, or tool failure are separate states. They do not select the recommendation. Continue independent work but keep dependent decisions unresolved. Host waiting behavior belongs to the host; do not promise that a skill can remove its timeout.

## Candidate feedback

Show previews produced from the actual SVG files, with concise variant labels and matching file links. Describe the one changed design dimension. Prefer “A keeps a broad side fringe; B opens more facial space” to an unexplained taste score.

After a selection, record both the chosen candidate and the requested refinement. Feedback such as “same, but reduce the blush” is a scoped edit, not permission to redraw hair or alter skin color. User acceptance must come from actual feedback.
