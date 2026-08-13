---
description: "PR checklist for Swift code changes."
applyTo: "**/*.swift"
---

# PR Checklist (Swift)

- [ ] No force-unwraps (`!`), `try!`, or `as!`
- [ ] `[weak self]` in all escaping closures
- [ ] `@Observable` used — never `@ObservedObject` or `ObservableObject`
- [ ] `@MainActor` annotations correct and complete
- [ ] No `DispatchQueue.main.async` in new code
- [ ] Sensitive data in Keychain, not `UserDefaults`
- [ ] No API keys or secrets in source
- [ ] All new public APIs documented (DocC)
- [ ] Tests added or updated
- [ ] SOLID / KISS / DRY applied
- [ ] Single-project scope: PR touches only one sub-project
