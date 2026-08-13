---
description: "Mandatory execution rules for every Copilot session in the assistance mono-repo."
applyTo: "**/*"
---

# Copilot Execution Rules

These rules apply to **every** Copilot session.

---

## 0. Context Router — Mandatory First Step

Before selecting agents or skills, consult `.github/context-router.md`.
Identify the task type from its table and load **only** the listed agents and skills for that type.
Do not load agents not listed for the current task type.

---

## 1. Branch-Based Workflow

All work on branches. Never commit to `main`. If on `main`, create a branch first.

---

## 2. Architecture & Decisions

Before modifying code, check `docs/decisions/` and `<project>/docs/decisions/` for ADRs.
New architectural choices require a new ADR (`docs/decisions/template.md`).

---

## 3. Lessons Learned

Before starting: read `docs/lessons.md`. After non-trivial sessions: append new lessons.
Format: `### Topic (YYYY-MM-DD)` followed by numbered findings.

---

## 4. Session Summary

Every session ends with a summary **in the chat response** (not only in the PR description):
- **Agents Used** table — every agent considered, with ✅/⏭️/❌ status and one-line result
- Decisions made (ADRs created/updated)
- Lessons learned
- Recommendations for next session

See `self-management.md` for the required output template.

---

## 5. Backlog Discipline

Check `<project>/docs/todo.md` before starting. Create entries for discovered work.
Update status of items you worked on. Reference backlog items in PRs.

---

## 6. Concept-Before-Code

Non-trivial features (effort ≥ M): check for concept in `docs/concepts/` or create one
using `docs/concepts/template.md`. Move fully implemented concepts to `concepts/implemented/`.

---

## 7. Implementation Planning

Check `<project>/docs/plans/plan-*.md` for an active plan (🟢).
If plan exists → implement next open step (⬜). If complete → archive to `plans/implemented/`.
If no plan → scan backlog, create a new 3–8 step plan.
See `.github/instructions/implementation-planning.instructions.md` for full workflow.

---

## 8. parallel_validation — Code Changes Only

Run `parallel_validation` **only when** Swift source files were changed AND the changes are not purely documentary.

**Skip `parallel_validation` for:** plan updates, ADRs, backlog entries, README edits, `.md`-only PRs.

---

## 9. Destructive Decisions — Mandatory User Approval

No agent may unilaterally: delete user data, remove features, change persistence strategy,
introduce breaking API changes, or alter data models destructively.

**Process:** Stop → describe change → explain consequences → propose alternatives → wait
for explicit approval → document in ADR.

When in doubt, ask. Your risk assessment may be wrong.

---

## 10. Single-Project Focus

Every session operates on **exactly ONE sub-project.** Determine from branch name FIRST.

**In practice:**
- Only read/modify the target project's files
- Never scan multiple projects' backlogs
- If asked about all projects: "I'm focused on [project]. Want me to switch?"
- Exception: adding a one-line backlog entry to another project's `docs/todo.md`

**Sub-projects:** `toogether` · `toogether-app` · `wald-igel-app` · `oneOone-app` ·
`earworm-hunt-app` · `mosQuit-app` · `sprite-optimizer-app` ·
`shared-ui` · `template-project`

`toogether` + `toogether-app` = one logical project. `shared-ui` may be touched
alongside its consumer if directly required.
