---
name: Memory Bank
description: >
  Defines a persistent context and memory system for maintaining project knowledge
  across coding sessions. Ensures continuity by structured capture of project brief,
  technical context, system patterns, active context, and progress.
  Inspired by mrballistic/copilot-memory-bank-template and thedotmack/claude-mem.
---

# Skill: Memory Bank

## Purpose

Coding agents lose context between sessions. This skill defines how to maintain
persistent project knowledge through structured documentation files that capture
technical context, system patterns, and active work state.

---

## When to Use

- **Start of every session** — load context from memory files
- **During execution** — update active context as you learn
- **End of session** — persist learnings, progress, and decisions
- **After major changes** — refresh memory files to reflect new state

---

## Memory File Structure

The repo already has most of this infrastructure. This skill formalises it:

| File | Purpose | Update Frequency |
|------|---------|------------------|
| `CLAUDE.md` / `README.md` | Project brief, build commands, structure | Rarely — on major changes |
| `<project>/copilot-instructions.md` | Project-specific context, domain knowledge | On architectural changes |
| `docs/architecture/overview.md` | System patterns, layer rules, dependency graph | On architectural changes |
| `docs/todo.md` | Active backlog, priorities, what to work on next | Every session |
| `docs/lessons.md` | Session learnings, anti-patterns, discoveries | Every session |
| `<project>/docs/plans/plan-*.md` | Active execution plan, current step, progress | Every session |
| `docs/decisions/*.md` | ADRs — architectural decisions and rationale | When decisions are made |

---

## Session Entry Protocol

At the start of every session:

```
1. Read CLAUDE.md               → understand project structure and commands
2. Read docs/todo.md            → know what's prioritised
3. Read docs/lessons.md (tail)  → avoid repeating known mistakes
4. Check <project>/docs/plans/  → find active plan, resume at next open step
5. Read relevant ADRs           → respect existing decisions
```

---

## Session Exit Protocol

Before ending a session:

```
1. Update plan progress         → mark steps ✅, add notes
2. Append to docs/lessons.md    → capture session learnings
3. Update docs/todo.md          → mark completed items, add new discoveries
4. Write session summary        → agents involved, decisions, recommendations
```

---

## Active Context Pattern

When working on a complex task spanning multiple interactions, maintain
active context by keeping the implementation plan updated:

```markdown
## Progress Log

| Date | Session | Steps Completed | Notes |
|------|---------|-----------------|-------|
| 2026-03-24 | PR #42 | Steps 1, 2, 3 | Found edge case in validation |
```

This provides continuity between sessions without relying on chat history.

---

## Context Layers (Progressive Disclosure)

Not all context is needed for every task. Load context in layers:

| Layer | When to Load | Files |
|-------|-------------|-------|
| **1. Always** | Every session | `CLAUDE.md`, current plan |
| **2. Task-specific** | Based on task type | Relevant `copilot-instructions.md`, ADRs |
| **3. Deep context** | Complex tasks, debugging | `lessons.md`, `architecture/overview.md`, concept docs |
| **4. Full history** | Major refactoring, new team member | All of the above + all concept docs + all plans |

---

## What to Capture

### Always Capture
- Decisions made and why (→ ADRs)
- Mistakes made and how to avoid them (→ lessons.md)
- Backlog items discovered during work (→ todo.md)
- Plan progress (→ plan files)

### Capture When Relevant
- Build/test commands that work (→ CLAUDE.md)
- Non-obvious project structure (→ copilot-instructions.md)
- Integration patterns (→ concept docs or ADRs)

### Never Capture
- Secrets, API keys, passwords
- Personal information
- Temporary debugging artifacts
- Session-specific state that won't generalise

---

## Relationship to Existing Infrastructure

This skill doesn't introduce new files — it formalises the **workflow** around
existing repo infrastructure:

| Existing Pattern | This Skill Adds |
|-----------------|-----------------|
| `docs/todo.md` exists | Systematic update at session start/end |
| `docs/lessons.md` exists | Structured capture protocol |
| `docs/plans/` exists | Entry/exit protocol for plan continuity |
| `docs/decisions/` exists | Trigger conditions for creating ADRs |
| `CLAUDE.md` exists | Progressive disclosure layers |

---

## Anti-Patterns

| Anti-Pattern | Better Approach |
|-------------|-----------------|
| Relying on chat history for context | Write it to files |
| "I'll remember this" | Write it to `lessons.md` |
| Starting without checking plans | Always check `<project>/docs/plans/` first |
| Ignoring lessons.md | Read the tail — last 10 entries minimum |
| Updating everything at once | Update relevant files as you go, not in a big batch |
