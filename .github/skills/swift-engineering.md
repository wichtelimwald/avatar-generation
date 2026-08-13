---
name: Swift Engineering
description: >
  Consolidated Swift best practices, code quality standards, and design patterns.
  Apply when writing, reviewing, or refactoring Swift code. Covers value types,
  optionals, error handling, concurrency, memory management, protocol-oriented design,
  Clean Architecture, MVVM, Repository pattern, and code quality metrics.
  Merges: swift-best-practices + code-quality + design-patterns.
---

# Skill: Swift Engineering

## Value Types vs Reference Types

| Prefer | Over | Reason |
|--------|------|--------|
| `struct` | `class` | Value semantics, copy-on-write |
| `enum` | `class` for state machines | Exhaustive pattern matching |
| `protocol` + `struct` | Inheritance | Composition over inheritance |

Exception: `class` for identity, reference semantics, or Obj-C interop.

---

## Optionals

```swift
guard let value = optionalValue else { return }    // ✅
let result = optionalValue ?? defaultValue          // ✅
let value = optionalValue!                          // ❌ Force-unwrap
let value: String! = nil                            // ❌ IUO
```

---

## Error Handling

```swift
// ✅ Typed errors
enum NetworkError: Error {
    case notFound, unauthorized(reason: String), decodingFailed(underlying: Error)
}

// ✅ Propagate, don't swallow
func loadProfile() async throws -> UserProfile {
    let data = try await networkService.fetch("/profile")
    return try decoder.decode(UserProfile.self, from: data)
}

// ❌ try! / try? on important operations
```

---

## Concurrency (Swift Structured Concurrency)

```swift
// ✅ async/await
func loadUser(id: String) async throws -> User { try await repository.fetch(id: id) }

// ✅ Parallel work
async let imageA = loadImage(url: urlA)
async let imageB = loadImage(url: urlB)
let (a, b) = try await (imageA, imageB)

// ✅ Actor for shared mutable state
actor UserCache { private var cache: [String: User] = [:] }

// ✅ @MainActor for all UI code
@MainActor final class HomeViewModel { var items: [Item] = [] }

// ❌ DispatchQueue in new code
```

Check `Task.isCancelled` in loops. Handle `CancellationError` explicitly.

---

## Memory Management

`[weak self]` mandatory in escaping closures. `[unowned self]` only when lifetime guaranteed.

---

## Protocol-Oriented Design

```swift
// ✅ `some` for opaque return types
func makeRepository() -> some UserRepository { RemoteUserRepository() }

// ✅ `any` only when type erasure genuinely needed
var handlers: [any EventHandler] = []
```

---

## Architectural Patterns

### Clean Architecture

```
UI (SwiftUI Views) → Presentation (ViewModels) → Domain (Use Cases, Entities) ← Data (Repos, Services)
```

Dependencies point **inward only**. Domain has zero framework imports.

### MVVM + @Observable

```swift
@Observable @MainActor
final class ItemListViewModel {
    private(set) var items: [Item] = []
    private let fetchItems: FetchItemsUseCase
    init(fetchItems: FetchItemsUseCase) { self.fetchItems = fetchItems }
    func load() async { items = (try? await fetchItems()) ?? [] }
}
```

### Repository Pattern

Protocol in Domain (no imports), implementation in Data, fake for testing.

### Coordinator / Router

Type-safe routing with `NavigationStack` + `NavigationPath` + `AppRoute` enum.

---

## Dependency Injection

Constructor injection preferred. `@Environment` for cross-cutting concerns.
No singletons with shared mutable state.

---

## Code Quality Thresholds

| Metric | Acceptable | Refactor |
|--------|-----------|---------|
| Function length | ≤ 20 lines | > 40 lines |
| Type length | ≤ 150 lines | > 300 lines |
| Cyclomatic complexity | ≤ 5 | > 10 |
| Nesting depth | ≤ 2 | > 3 |
| Parameters per function | ≤ 4 | > 5 |

---

## Guard-First Pattern

Early exit reduces nesting. Multiple `guard` clauses before main logic.

---

## Code Smells

| Smell | Fix |
|-------|-----|
| Long Method (> 40 lines) | Extract Method |
| Large Class (> 300 lines) | Extract Class / Protocol |
| Data Clumps | Introduce Parameter Object |
| Feature Envy | Move Method |
| Primitive Obsession | Introduce Value Object |
| Dead Code | Remove |
| Callback Hell | Refactor to async/await |
| Singleton Abuse | Dependency Injection |

---

## Anti-Patterns

| Anti-Pattern | Fix |
|-------------|-----|
| God Object | Decompose with protocols |
| Massive ViewController | MVVM + Use Cases |
| `ObservableObject` in new code | MUST use `@Observable` |
| String-based identifiers | Typed enums |
| `AnyView` | `@ViewBuilder` |

---

## Naming & Organisation

- Types: `UpperCamelCase`. Functions/variables: `lowerCamelCase`.
- Booleans: `is-`, `has-`, `should-`, `can-` prefix.
- One file per type, filename = type name.
- `// MARK:` for Properties, Initialisation, Public Interface, Private Helpers.
- Mark `private` aggressively.

---

## SwiftUI Patterns

- Views max ~60 lines in body. Extract sub-views.
- `@State private var viewModel = ViewModel()` with `@Observable`.
- `.task { }` over `.onAppear { Task { } }`.
- `NavigationStack` + type-safe routing.
- Never `@StateObject` / `AnyView` in new code.
