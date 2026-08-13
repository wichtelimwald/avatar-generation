# Contributing to `assistance`

Thank you for contributing to this mono-repository! This guide explains how to
set up your development environment, follow the code style, and submit your work.

---

## Table of Contents

- [Development Environment Setup](#development-environment-setup)
- [Branching Strategy](#branching-strategy)
- [Code Style Guide](#code-style-guide)
- [Pull Request Workflow](#pull-request-workflow)
- [Architecture Decision Records (ADRs)](#architecture-decision-records-adrs)
- [Concept Documents](#concept-documents)
- [Backlog Management](#backlog-management)

---

## Development Environment Setup

### Prerequisites

| Tool | Minimum Version | Purpose |
|------|----------------|---------|
| Xcode | 15.4+ | iOS/macOS development |
| Swift | 5.9+ | Language runtime |
| SwiftLint | 0.57+ | Code style enforcement |
| Git | 2.x | Version control |

### Steps

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/wichtelimwald/assistance.git
   cd assistance
   ```

2. **Install SwiftLint** (if not already installed):
   ```bash
   brew install swiftlint
   ```

3. **Build a Swift Package project** (e.g. `template-project`):
   ```bash
   cd template-project
   swift build
   swift test
   ```

4. **Build the Xcode app project** (e.g. `toogether-app`):
   ```bash
   cd toogether-app
   xcodebuild build \
     -project toogether.xcodeproj \
     -scheme toogether \
     -destination 'platform=iOS Simulator,name=iPhone 16 Pro' \
     CODE_SIGNING_ALLOWED=NO
   ```

---

## Branching Strategy

This repository follows **Git Flow Lite**:

| Branch | Purpose | Merge Target |
|--------|---------|-------------|
| `main` | Production-ready code | — |
| `develop` | Integration branch | `main` via PR |
| `feature/<name>` | Feature work | `develop` |
| `fix/<name>` | Bug fixes | `develop` (or `main` for hotfixes) |
| `concept/<name>` | Concept / planning work | `develop` |

**Rules:**
- Never commit directly to `main` or `develop`.
- Always open a Pull Request; at least one approval is required.
- All CI checks must pass before merging.
- Commits on `main` must be signed (GPG or SSH).

---

## Code Style Guide

Full rules → [`.github/copilot-instructions.md`](.github/copilot-instructions.md#code-style).
Per-project SwiftLint config → `<project>/.swiftlint.yml`.

```bash
swiftlint lint --config <project>/.swiftlint.yml <project>
```

---

## Pull Request Workflow

1. **Create a branch** from `develop`:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/my-feature
   ```

2. **Make your changes** in small, focused commits.

3. **Run tests locally:**
   ```bash
   swift test    # for Swift Package projects
   ```

4. **Push and open a PR** targeting `develop`:
   ```bash
   git push origin feature/my-feature
   ```

5. **Fill in the PR template** — describe the change, link the backlog item, and
   check all items in the checklist.

6. **Address review comments** from the assigned code reviewer and/or Copilot agents.

7. **Merge** after approval and all CI checks pass.

---

## Testing on Device

Use the `test-on-device.sh` script to pull the latest code and open the project
in Xcode — then pick your device and press ⌘R:

```bash
# Pull latest and open in Xcode
./scripts/test-on-device.sh -p toogether

# Test a specific branch
./scripts/test-on-device.sh -p toogether -b feature/my-feature
```

The script handles pulling the latest code and opening the right Xcode project.
Run `./scripts/test-on-device.sh --help` for all options.

See [`scripts/README.md`](scripts/README.md) for full documentation.

---

## Architecture Decision Records (ADRs)

Significant design or architecture decisions **must** be documented as ADRs.

- **Template:** [`docs/decisions/template.md`](docs/decisions/template.md)
- **Location:** `docs/decisions/` (mono-repo-level) or `<project>/docs/decisions/`
  (project-specific)

**When to write an ADR:**
- Choosing a framework, library, or persistence strategy
- Changing the architecture or module boundaries
- Making a security-sensitive decision

---

## Concept Documents

Non-trivial features must start with a concept document, reviewed before
implementation begins.

- **Template:** [`docs/concepts/template.md`](docs/concepts/template.md)
- **Location:** `docs/concepts/` (mono-repo-level) or `<project>/docs/concepts/`
  (project-specific)
- **Implemented concepts:** Move to `docs/concepts/implemented/` (or
  `<project>/docs/concepts/implemented/`) once fully implemented.

**Workflow:**
```
Backlog entry → Concept document → Architecture review → Implementation → Move to docs/concepts/implemented/
```

---

## Backlog Management

All work items are tracked in:

- [`docs/todo.md`](docs/todo.md) — mono-repo-level backlog
- `<project>/docs/todo.md` — project-specific backlog

Before starting any work:
1. Ensure there is an entry in the relevant `todo.md`.
2. Assign yourself and change status to in-progress.
3. Reference the backlog entry in your PR description.

---

## Copilot / AI Session Rules

Follow the execution protocol in
[`.github/instructions/execution-rules.instructions.md`](.github/instructions/execution-rules.instructions.md).
Pre-Flight → During → Close-Out with Session Summary.
