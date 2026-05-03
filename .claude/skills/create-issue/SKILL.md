---
name: create-issue
description: Interactively create a well-formed GitHub issue following the project's conventions.
disable-model-invocation: true
---

# Create Issue

Guide the user through creating a GitHub issue. Gather the necessary information conversationally, propose a complete draft for review, and create it with `gh` only after explicit approval.

## When to Activate

- User wants to create a new GitHub issue
- User says "create issue", "new issue", "open an issue", or similar

## Rules

- Issues are self-contained — no references to future issues or planning context
- Title is short and descriptive — written so an outsider can understand what the issue is about
- Use the user's input as raw material, not as final text — rephrase and structure it clearly for someone unfamiliar with the project
- Infer what you can from context and conversation; ask only when inference would require guessing
- Templates in [templates](./templates) are guides, not rigid requirements — remove sections that don't add value for this specific issue

## Workflow

### 1. Gather information

Ask questions one at a time. Only ask what is needed — do not re-ask anything the user already explained.

- What needs to be done or fixed? (if not already clear)
- Why is this needed? What problem does it solve?
- Is there relevant context? (optional but makes the issue richer)
  - How does it work today?
  - Any constraints or decisions already made?
- How will we know it is done? (acceptance criteria)
- Are there subtasks — specific steps that can be checked off one by one? (optional)

For bug reports also ask:
- How can it be reproduced?
- What is the expected behavior vs what actually happens?
- Is it happening consistently or intermittently?

**Writing guidance:**
- Write for someone external to the project — assume no context
- Open with a background section that explains the problem before the solution
- Do not infer or add technical details the user did not provide
- Structure clearly: Background → What / Why → Acceptance criteria → Subtasks (if any)

### 2. Fetch labels

Run `gh label list` to see what labels exist in the repo. Propose the most appropriate one based on the issue content.

### 3. Present the plan

Call `EnterPlanMode`, then write the complete draft to the plan file. The plan file path is provided in the plan mode system message.

Check if [templates](./templates) contains a relevant template and use it as a starting point. If not, structure the body using good judgement.

The plan file must contain the full draft — title, label, and body — formatted exactly as it will appear in GitHub.

Once the plan file is written, call `ExitPlanMode`. This presents the plan UI to the user so they can review and iterate. If the user requests changes, update the plan file and call `ExitPlanMode` again.

### 4. Create

Only once the user approves from the plan UI, run:

```bash
gh issue create --title "<title>" --label "<label>" --body "<body>"
```

Report the issue number and URL. Remind the user that the branch should be named `<type>/<number>-<description>`.
