---
name: Swift Platform
description: >
  Xcode project structure, build settings, SPM, entitlements, debugging,
  and SwiftData persistence patterns.
  Merges: swift-xcode + swift-data.
---

# Skill: Swift Platform (Xcode + SwiftData)

## Xcode Project Structure

```
MyApp/
├── App/           # @main entry, AppDelegate (if needed)
├── Features/      # Feature-sliced (Home/, Settings/, etc.)
├── Core/          # Network/, Storage/, Extensions/
├── Resources/     # Assets, Localizable.xcstrings, Info.plist
└── Tests/         # UnitTests/, UITests/
```

- One file per type, filename = type name. Group by feature, not by type.
- Shared code → local Swift Package, not framework target.

## Build Settings

```
SWIFT_VERSION = 5.9
IPHONEOS_DEPLOYMENT_TARGET = 17.0
ENABLE_STRICT_CONCURRENCY = complete
```

- Schemes: Debug (testability, sanitizers), Release (optimized), Staging (staging API).
- Prefer xcconfig files over inline build settings.
- All dependencies via SPM. Pin exact versions. Commit `Package.resolved`.

## Debugging

- Use `os_log` / `Logger`, not `print`.
- Instruments: Time Profiler, Allocations, Hangs, SwiftUI body re-renders.
- Thread Sanitizer for concurrency bugs. Memory Graph Debugger for retain cycles.

## Testing

- `accessibilityIdentifier` for UI tests, not text strings.
- Async tests: `func test() async throws { }` — no expectations needed.
- Snapshot tests with swift-snapshot-testing for key screens.

## Localization

- `.xcstrings` catalog (Xcode 15+). `String(localized:comment:)` for all UI strings.

---

# SwiftData

## Model Design

- `@Model` on all persistent classes.
- Specify `.cascade`/`.nullify`/`.deny` on relationships.
- `#Unique<T>` for uniqueness constraints.
- Prefix with `SD` when domain model exists (e.g., `SDActivity` wraps `Activity`).

## Container & Context

- One `ModelContainer` per app at `@main`.
- `@Environment(\.modelContext)` in views.
- Background `ModelContext` on a background actor for heavy operations.
- `ModelConfiguration(isStoredInMemoryOnly: true)` for tests/previews.

## Queries

- `@Query` in views for automatic observation.
- `#Predicate` for type-safe filtering. `SortDescriptor` for sorting.
- `FetchDescriptor.fetchLimit` for large datasets.
- Batch inserts: loop `context.insert()`, then `save()` once.

## Migrations

- Lightweight (add/remove properties) works automatically.
- Complex: `SchemaMigrationPlan` + `MigrationStage` + `VersionedSchema`.
- Test migrations with real data before release.

## Anti-Patterns

- ❌ Fetching all records without limit → use `fetchLimit`
- ❌ Saving after every insert in a loop → batch, save once
- ❌ `@Query` in ViewModels → use `FetchDescriptor` with `ModelContext`
- ❌ Force-unwrapping relationships → optional chaining
- ❌ Heavy queries on `@MainActor` → background `ModelContext`
