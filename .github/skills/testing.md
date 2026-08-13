---
name: Testing
description: >
  Consolidated testing skill: TDD, test quality, and verification before completion.
  Covers RED→GREEN→REFACTOR cycle, test naming, AAA pattern, mocking, async testing,
  coverage goals, and evidence-based verification.
  Merges: tdd + test-quality + verification-before-completion.
---

# Skill: Testing

## TDD — The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

Wrote code before the test? Delete it. Start over.

### RED → GREEN → REFACTOR

1. **RED** — Write ONE minimal failing test for the desired behaviour.
2. **Verify RED** — Run `swift test --filter <test>`. Confirm it fails for the right reason.
3. **GREEN** — Write the simplest code to pass the test. Nothing more.
4. **Verify GREEN** — Run `swift test`. All tests pass.
5. **REFACTOR** — Clean up. Keep tests green. Don't add behaviour.
6. **Repeat** — Next failing test for next behaviour.

### When to Use TDD

Always: new features, bug fixes, refactoring, behaviour changes.
Exceptions (with approval): throwaway prototypes, generated code, view-only SwiftUI.

---

## Test Naming

```
test_<unitUnderTest>_<scenario>_<expectedResult>
```

Examples: `test_fetchUser_whenValidID_returnsExpectedUser()`, `test_validateEmail_whenMissingAtSign_returnsFalse()`

---

## Test Structure (AAA)

```swift
func test_fetchUser_whenValidID_returnsExpectedUser() async throws {
    // Arrange
    let expectedUser = User.fixture()
    mockNetworkService.stubbedResponse = expectedUser
    // Act
    let result = try await sut.fetchUser(id: "user-1")
    // Assert
    XCTAssertEqual(result, expectedUser)
}
```

---

## Test Fixtures

```swift
extension User {
    static func fixture(id: String = "user-1", name: String = "Test User") -> User {
        User(id: id, name: name)
    }
}
```

---

## Mocking

| Type | When | Pattern |
|------|------|---------|
| Stub | Return fixed data | `var stubbedValue: T` |
| Mock | Verify interactions | `var fetchWasCalled: Bool` |
| Spy | Capture arguments | `var capturedIDs: [String] = []` |
| Fake | In-memory implementation | `InMemoryUserRepository` |

---

## Async Testing

```swift
// ✅ async/await directly
func test_loadItems_populatesViewModel() async {
    await sut.load()
    XCTAssertFalse(sut.items.isEmpty)
}

// ✅ Testing throws
do {
    _ = try await sut.execute(userID: "123")
    XCTFail("Expected error")
} catch NetworkError.notFound { /* expected */ }
```

Use `XCTUnwrap` instead of force-unwraps in tests.

---

## Coverage Goals

| Layer | Target | Minimum |
|-------|--------|---------|
| Domain (Use Cases, Entities) | 95% | 90% |
| Data (Repositories) | 85% | 80% |
| Presentation (ViewModels) | 80% | 75% |
| Utilities / Extensions | 90% | 85% |

---

## Verification Before Completion

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

Before claiming any status:
1. **IDENTIFY** — What command proves this claim?
2. **RUN** — Execute the full command (fresh, complete)
3. **READ** — Full output, check exit code
4. **VERIFY** — Does output confirm the claim?

| Claim | Command | Evidence |
|-------|---------|----------|
| Builds | `swift build` | Exit 0, no errors |
| Tests pass | `swift test` | All pass, 0 failures |
| Lint clean | `swiftlint` | 0 violations |
| PR ready | Build + test + lint | All green |

**Red flags:** Using "should", "probably", "seems to" — STOP and run the verification.

---

## Test Anti-Patterns

| Anti-Pattern | Fix |
|-------------|-----|
| Testing implementation details | Test behaviour |
| Shared mutable state | Reset in setUp/tearDown |
| `sleep()` in async tests | Use `await` or expectations |
| Force-unwrap in assertions | Use `XCTUnwrap` |
| Hardcoded test data | Use `.fixture()` factories |
