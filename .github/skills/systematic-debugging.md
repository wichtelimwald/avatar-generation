---
name: Systematic Debugging
description: >
  Use when encountering any bug, test failure, or unexpected behaviour.
  Enforces a 4-phase root-cause process: investigate → analyse → hypothesise → fix.
  Random fixes waste time and create new bugs — always find the root cause first.
  Inspired by obra/superpowers.
---

# Skill: Systematic Debugging

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes.

---

## When to Use

Use for **ANY** technical issue:
- Test failures, build failures
- Bugs in production or development
- Unexpected behaviour or performance problems
- Integration issues, CI failures

**Use this ESPECIALLY when:**
- Under time pressure (emergencies make guessing tempting)
- "Just one quick fix" seems obvious
- You've already tried multiple fixes
- Previous fix didn't work

---

## The Four Phases

Complete each phase before proceeding to the next.

### Phase 1 — Root Cause Investigation

**BEFORE attempting ANY fix:**

1. **Read Error Messages Carefully**
   - Full stack traces — every line
   - Line numbers, file paths, error codes
   - Don't skip warnings

2. **Reproduce Consistently**
   - Can you trigger it reliably?
   - Exact steps to reproduce
   - If not reproducible → gather more data, don't guess

3. **Check Recent Changes**
   - `git diff`, recent commits
   - New dependencies, config changes
   - Environmental differences (Xcode version, simulator, device)

4. **Gather Evidence in Multi-Component Systems**
   - Log what enters/exits each component boundary
   - Verify environment/config propagation at each layer
   - Run once to see WHERE it breaks, THEN investigate that component

5. **Trace Data Flow**
   - Where does the bad value originate?
   - Trace backward through the call stack
   - Fix at the source, not at the symptom

### Phase 2 — Pattern Analysis

1. **Find Working Examples** — similar working code in same codebase
2. **Compare Against References** — read reference implementation completely
3. **Identify Differences** — list every difference, however small
4. **Understand Dependencies** — what components, settings, config does this need?

### Phase 3 — Hypothesis and Testing

1. **Form Single Hypothesis** — "I think X is the root cause because Y"
2. **Test Minimally** — smallest possible change, one variable at a time
3. **Verify Before Continuing** — worked → Phase 4; didn't work → new hypothesis
4. **When You Don't Know** — say so. Don't pretend. Research more.

### Phase 4 — Implementation

1. **Create Failing Test Case** — simplest possible reproduction (use `testing` skill)
2. **Implement Single Fix** — address root cause, ONE change at a time
3. **Verify Fix** — test passes? No other tests broken? Issue resolved?
4. **If Fix Doesn't Work** — STOP. Count attempts.
   - < 3 attempts → return to Phase 1 with new information
   - ≥ 3 attempts → **question the architecture** (see below)

### When 3+ Fixes Fail — Question Architecture

Pattern indicating an architectural problem:
- Each fix reveals new shared state / coupling in a different place
- Fixes require "massive refactoring" to implement
- Each fix creates new symptoms elsewhere

**STOP and question fundamentals.** Discuss with the team before attempting more fixes.

---

## Red Flags — STOP and Follow Process

If you catch yourself thinking:
- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "Add multiple changes, run tests"
- "It's probably X, let me fix that"
- "I don't fully understand but this might work"

**ALL of these mean: STOP. Return to Phase 1.**

---

## Quick Reference

| Phase | Key Activities | Success Criteria |
|-------|---------------|------------------|
| **1. Root Cause** | Read errors, reproduce, check changes, gather evidence | Understand WHAT and WHY |
| **2. Pattern** | Find working examples, compare | Identify differences |
| **3. Hypothesis** | Form theory, test minimally | Confirmed or new hypothesis |
| **4. Implementation** | Create test, fix, verify | Bug resolved, tests pass |

---

## iOS / Swift Specifics

| Symptom | First Step | Second Step |
|---------|-----------|------------|
| Crash with no line number | Enable Address Sanitizer | Check wild pointer / bad memory access |
| Intermittent crash | Thread Sanitizer | Audit `async`/actor isolation |
| Main thread blocked | Time Profiler → filter main thread | Find blocking call |
| Memory growing | Instruments Allocations → heap mark | Find persistent closures holding references |
| SwiftUI not updating | Verify `@Observable` imported correctly | Check `@State` ownership |
| SwiftData not persisting | Check `modelContext.save()` placement | Verify `@ModelActor` isolation |

---

## Common Rationalisations

| Excuse | Reality |
|--------|---------|
| "Issue is simple, don't need process" | Simple issues have root causes too. Process is fast for simple bugs. |
| "Emergency, no time for process" | Systematic debugging is FASTER than guess-and-check thrashing. |
| "Just try this first, then investigate" | First fix sets the pattern. Do it right from the start. |
| "I see the problem, let me fix it" | Seeing symptoms ≠ understanding root cause. |
| "One more fix attempt" (after 2+ failures) | 3+ failures = architectural problem. Question the pattern. |
