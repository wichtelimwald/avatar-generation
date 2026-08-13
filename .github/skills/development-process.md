---
name: Development Process
description: >
  Spec-driven development and code review process.
  Covers the 5-phase spec workflow and structured PR review with severity tiers.
  Merges: spec-driven-development + review-process.
---

# Skill: Development Process

## Spec-Driven Development

### When to Use
- New features (M effort or larger), architecture changes, non-trivial refactoring.
- Skip for: bug fixes with clear root cause, docs-only, style fixes, XS-effort.

### Five Phases

1. **Discover** — Explore context, ask questions, propose 2–3 approaches, get approval.
2. **Spec** — Write `<project>/docs/concepts/<feature>.md` with: Problem, Goals, Non-Goals,
   Approach, Alternatives, Acceptance Criteria, Risks.
3. **Plan** — Create `<project>/docs/plans/plan-NNN-<feature>.md` (3–8 steps).
4. **Tasks** — Define file paths, tests, dependencies, effort per step.
5. **Implement** — Execute step by step with TDD. Update plan progress.

### Design Principles
- **Isolation:** Units with one purpose, well-defined interfaces.
- **YAGNI:** Remove unnecessary features. Implement what's needed, not imagined.
- **Codebase first:** Explore existing patterns before proposing changes.

---

## Code Review Process

### Review Summary Format
```
**Risk**: 🔴 High / 🟡 Medium / 🟢 Low
**Scope**: [what this PR does]
**Verdict**: Approve / Request Changes / Needs Discussion
```

### Severity Tiers

| Tier | When |
|------|------|
| 🔴 Must Fix | Bugs, crashes, security issues, data loss — blocks merge |
| 🟡 Should Fix | Memory leaks, retain cycles, concurrency issues, missing tests — before shipping |
| 🟠 Refactor | Code smells, convention violations, duplication — follow-up |
| 🟢 Suggestion | Idiomatic improvements, docs, performance micro-opts — optional |
| 💬 Discussion | Architecture trade-offs, subjective choices |

### Swift Review Checklist

**Memory & Concurrency:**
- `[weak self]` in escaping closures
- `@MainActor` correct and complete
- No `DispatchQueue` in new code
- Errors propagate (no silent `try?` on meaningful failures)

**SwiftUI:**
- `@State` is `private`
- `@Observable` only (never `@ObservedObject`/`ObservableObject`)
- Views don't contain business logic
- `.task {}` not `.onAppear { Task {} }`

**Security:**
- No secrets in source code
- Keychain for sensitive data
- HTTPS only, input sanitized

**Testing:**
- Critical logic has unit tests
- Async functions have `async throws` tests
- UI tests use `accessibilityIdentifier`

### Tone
- Direct, not harsh. Suggest, don't dictate.
- Acknowledge good work. Ask questions for unclear intent.
- Prefix optional opinions with "Nit:".
