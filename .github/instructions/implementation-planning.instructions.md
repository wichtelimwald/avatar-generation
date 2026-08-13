---
description: "Implementation planning workflow. Loaded when working with plan files."
applyTo: "**/docs/plans/**"
---

# Implementation Planning

Every coding session should begin by checking for an active implementation plan. This
avoids wasted context searching through backlogs and concepts to figure out what to
work on next.

---

## 1. Session Entry Point

At the start of every implementation session, follow this sequence:

```
1. Check for an active plan  →  <project>/docs/plans/plan-*.md
2. If plan exists            →  Read it, implement the next open step, update progress
3. If plan is complete       →  Archive it, scan for new work, create next plan
4. If no plan exists         →  Scan backlog + concepts, create a new plan
```

### Where Plans Live

| Scope | Directory | Example |
|-------|-----------|---------|
| Mono-repo level | `docs/plans/` | `docs/plans/plan-001-ci-improvements.md` |
| Project-specific | `<project>/docs/plans/` | `toogether/docs/plans/plan-001-mvp-polish.md` |
| Archived (completed) | `<project>/docs/plans/implemented/` | Moved there when all steps are done |

---

## 2. Plan Format

An implementation plan is a **focused, actionable sprint document** — not a concept or
a strategy paper. It contains **concrete steps with effort estimates** that can be
executed sequentially.

### Required Sections

```markdown
# Implementation Plan: <Title>

**Plan ID:** plan-NNN
**Date:** YYYY-MM-DD (creation date)
**Status:** 🟢 Active | ✅ Complete | ⏸️ Paused
**Scope:** <project name or "mono-repo">
**Source:** <link to backlog items, concepts, or issues that motivated this plan>
**Estimated Effort:** <total hours or T-shirt size>

---

## Goal

One paragraph: What will be different when this plan is complete?

---

## Steps

| # | Task | Type | Effort | Status | Notes |
|---|------|------|--------|--------|-------|
| 1 | <concrete task> | 🤖 Code / 👤 Manual / 📝 Docs | S/M/L | ⬜ / 🟡 / ✅ | |
| 2 | ... | | | | |

### Step Details (expand as needed)

#### Step 1 — <Task Name>
- **What:** Specific description of what to do
- **Where:** File paths or modules affected
- **Acceptance:** How to verify it's done
- **Preconditions:** Steps or external factors that must be true before this step can start
- **Effects:** What will be different in the codebase after this step completes
- **Dependencies:** Other steps or external factors that block this step

---

## Progress Log

| Date | Session | Steps Completed | Notes |
|------|---------|-----------------|-------|
| YYYY-MM-DD | <PR or session ref> | 1, 2, 3 | <brief summary> |

---

## Completion Criteria

- [ ] All steps marked ✅
- [ ] Tests pass (`swift test` / `xcodebuild test`)
- [ ] Backlog updated (completed items marked `[x]`)
- [ ] Lessons learned documented
```

---

## 3. Creating a New Plan

When you need to create a new plan (no active plan exists, or previous plan completed):

### Step 1 — Scan for Work

Check these sources in order:

1. **Active plans** in `<project>/docs/plans/` — resume if one exists
2. **Ready section** in `<project>/docs/todo.md` — check the `🟢 Ready (unblocked)` table for items with no blockers
3. **Backlog** in `<project>/docs/todo.md` — look at highest-priority open `[ ]` items (use task IDs like `TG-001` for reference)
4. **Concepts** in `<project>/docs/concepts/` — find concepts that need implementation
5. **Lessons** in `<project>/docs/lessons.md` — find recurring issues to fix
6. **Reviews** in `<project>/docs/reviews/` — find recommendations to implement

### Step 2 — Select Scope

A good plan covers **3–8 related tasks** that can be completed in **1–3 sessions**.
Group by:

- **Theme:** "Avatar UX polish", "Import pipeline improvements"
- **Priority:** All P2 MVP items, or all P2 items in one feature area
- **Dependency chain:** Tasks that must be done in order

### Step 3 — Write the Plan

Use the format above. Be specific:

- ❌ "Improve avatar UX" (too vague)
- ✅ "Add VoiceOver labels to AvatarPickerView archetype grid cells" (actionable)

### Step 4 — Name the Plan

Format: `plan-NNN-<kebab-case-title>.md`

- `plan-001-mvp-polish.md`
- `plan-002-avatar-ux-improvements.md`
- `plan-003-import-pipeline-v2.md`

Increment the number sequentially within each project's `docs/plans/` directory.

---

## 4. Executing a Plan

When implementing steps from a plan:

1. **Read the plan** — understand context, dependencies, and current progress
2. **Pick the next open step** — marked ⬜ (not started) or 🟡 (in progress)
3. **Implement the step** — follow the step details and acceptance criteria
4. **Update the plan** — mark step ✅, add notes, update the progress log
5. **Update the backlog** — mark corresponding `todo.md` items as complete
6. **Commit progress** — use `report_progress` to push changes

### Status Markers

| Marker | Meaning |
|--------|---------|
| ⬜ | Not started |
| 🟡 | In progress (started in a session, not yet done) |
| ✅ | Complete |
| ⏭️ | Skipped (with reason in Notes) |
| 🚫 | Blocked (with blocker in Notes) |

---

## 5. Completing a Plan

When all steps are ✅ (or ⏭️/🚫 with documented reasons):

1. **Set status** to `✅ Complete` in the plan header
2. **Add final progress log entry** with completion date
3. **Move the plan** to `<project>/docs/plans/implemented/`
4. **Add completion note** at the top:
   ```markdown
   > ✅ **Completed** — YYYY-MM-DD. All steps implemented.
   > See progress log for session references.
   ```
5. **Scan for new work** — follow "Creating a New Plan" (§3) to start the next cycle
6. **Create the next plan** if actionable work remains in the backlog

---

## 6. Plan Hygiene

- **One active plan per project** — avoid plan sprawl. If you need to pause a plan,
  set status to `⏸️ Paused` and document why.
- **Don't over-plan** — 3–8 steps per plan. Create a new plan when you finish, not a
  mega-plan that covers months of work.
- **Keep steps concrete** — each step should be completable in a single session (≤ 4 hours).
  If a step is bigger, break it into sub-steps.
- **Reference backlog items by task ID** — every step should trace back to a `todo.md` entry using its ID (e.g., `TG-009`).
- **Don't duplicate the backlog** — the plan is a *focused execution slice* of the
  backlog, not a copy of it.

---

## 7. Relationship to Other Documents

| Document | Purpose | Relationship |
|----------|---------|-------------|
| `todo.md` | Full backlog (all priorities) | Plans pull from the backlog |
| `concepts/*.md` | Analysis and design | Plans implement concepts |
| `decisions/*.md` | Architectural decisions | Plans respect ADRs |
| `lessons.md` | Learnings from past sessions | Plans avoid known pitfalls |
| `plans/*.md` | **Focused execution** | **This is the "what to do now" document** |
