# Skill: New Project Setup

## Purpose

Step-by-step guide for setting up a new project or product in the `assistance`
mono-repo. Covers the full lifecycle from initial idea through concept, scaffold,
infrastructure integration, and first PR.

This skill is the single source of truth for the process. It generalises the
workflow that was successfully applied for the **toogether** and
**earworm-hunt-app** projects.

---

## When to Use

- A new app or library idea needs to be formalised
- A new Swift Package or Xcode project is being added to the mono-repo
- You need a refresher on the expected documentation, CI, and agent setup

---

## Phase 1 — Idea & Backlog Entry

**Goal:** Capture the idea and make it visible in the backlog.

1. Add a `New Projects` entry to **`docs/todo.md`**:
   ```markdown
   - [ ] [feat][P1][L] **ProjectName** — One-line description
     - Project directory: [`project-name/`](project-name/)
     - Concept: *pending — product discovery interview first*
     - Next step: complete product-discovery interview
   ```
2. If the idea is project-specific to an existing project, add it to
   `<project>/docs/todo.md` instead.

---

## Phase 2 — Product Discovery Interview

**Goal:** Understand the product vision, target users, and MVP scope before
writing any code.

1. Open your AI chat of choice (Claude, ChatGPT, Gemini, etc.) and paste the
   **interview prompt** from
   `docs/prompts/product-discovery-interview-prompt.md`.
2. Answer the questions interactively — the AI will ask one at a time.
3. When done, the AI produces a formatted Markdown file. Copy it to
   `<project>/docs/concepts/interview-questionnaire.md`.
4. The interview covers:
   - Target users & context
   - Core functionality
   - Prioritisation & interaction model
   - Data & privacy stance
   - Look & feel / UX direction
   - Future vision & monetisation
   - Technical preferences
5. Compile answers in English — short bullet points are fine.

**Quick-start:** See [`HOW2START-NEW.md`](../../HOW2START-NEW.md) for the
2-step overview (interview first, then hand off to Copilot).

**Reference:** The toogether interview questionnaire
(`toogether/docs/concepts/interview-questionnaire.md`) demonstrates the expected
depth and format.

---

## Phase 3 — Concept Document

**Goal:** Translate interview findings into a structured concept document.

1. Copy the **concept template** from `docs/concepts/template.md`.
2. Place it at `<project>/docs/concepts/<project-name>.md` (e.g.
   `my-app/docs/concepts/my-app.md`).
3. Fill in all sections:
   - **Goal** — one or two paragraphs on what the product does
   - **Motivation** — user stories, pain points, why now
   - **Scope** — in-scope (MVP) vs. out-of-scope (later)
   - **Proposed Approach** — architecture sketch, key design decisions, data
     model draft
   - **Alternatives** — at least two alternatives with reasons rejected
   - **Open Questions** — unknowns that need resolution
   - **Acceptance Criteria** — measurable criteria for the MVP
   - **Impact Assessment** — performance, security, test coverage
   - **Implementation Plan** — ordered steps with effort estimates
4. Set status to `Draft` until reviewed.

---

## Phase 4 — Scaffold the Project

**Goal:** Create the project directory with code, tests, and documentation
scaffolding.

### For a Swift Package (library / domain core)

1. **Copy the template:**
   ```bash
   cp -r template-project <project-name>
   cd <project-name>
   ```

2. **Rename the package** in `Package.swift`:
   ```swift
   let package = Package(
       name: "MyProject",
       // ...
       targets: [
           .target(name: "MyProject", ...),
           .testTarget(name: "MyProjectTests", dependencies: ["MyProject"], ...),
       ]
   )
   ```

3. **Rename source directories:**
   ```bash
   mv Sources/TemplateProject Sources/MyProject
   mv Tests/TemplateProjectTests Tests/MyProjectTests
   ```

4. **Update source files** — rename `TemplateProject` references to `MyProject`
   in `Sources/MyProject/TemplateProject.swift` (rename the file too) and
   `Tests/MyProjectTests/TemplateProjectTests.swift`.

5. **Verify the build:**
   ```bash
   swift build && swift test
   ```

   > **Note:** `swift test` requires macOS with Xcode Command Line Tools installed.
   > On Linux, XCTest-based tests may fail with `no such module 'XCTest'` unless
   > the Swift toolchain includes XCTest (e.g. via `swift-corelibs-xctest`).
   > CI runs on macOS where this is not an issue.

### For an Xcode App (iOS)

1. Create a new Xcode project in the mono-repo root directory.
2. Use the same directory naming convention: lowercase with hyphens (e.g.
   `my-app`).
3. Ensure the scheme is shared (`Manage Schemes → Shared` checkbox).
4. Add `CODE_SIGNING_ALLOWED=NO` to CI build commands.

---

## Phase 5 — Project Documentation

**Goal:** Establish the project-specific documentation tree.

Create the following files inside `<project-name>/`:

| File | Purpose |
|------|---------|
| `copilot-instructions.md` | Project-specific context for Copilot agents |
| `docs/concepts/<project-name>.md` | Concept document (from Phase 3) |
| `docs/concepts/interview-questionnaire.md` | Completed interview (from Phase 2) |
| `docs/decisions/ADR-0001-initial-architecture.md` | First architecture decision |
| `docs/todo.md` | Project-specific backlog |
| `README.md` | Project overview, build & test commands |
| `.swiftlint.yml` | SwiftLint config (copy from `template-project/`) |

### copilot-instructions.md Template

```markdown
# <Project Name> – Project-Specific Copilot Instructions

## Overview
One or two sentences describing the project.

## Domain
Key domain concepts and terminology.

## Architecture
High-level architecture (layers, key types, patterns).

## Conventions
Project-specific rules beyond the global ones.

## Relevant Agents
List which global and project-specific agents apply.

## Build & Test
Commands to build, test, and lint locally.
```

---

## Phase 6 — Integrate with Mono-Repo Infrastructure

**Goal:** Wire the new project into CI, code ownership, and documentation.

### 6.1 CI Workflow (`.github/workflows/ci.yml`)

**For SPM packages** — add to the `spm-filter` in the `detect-changes` job:

```yaml
- uses: dorny/paths-filter@v3
  id: spm-filter
  with:
    filters: |
      template-project:
        - 'template-project/**'
      toogether:
        - 'toogether/**'
      my-project:                    # ← ADD
        - 'my-project/**'           # ← ADD
```

**For Xcode apps** — this requires multiple additions to `ci.yml`. Follow the
`build-earworm-hunt-app` / `swiftlint-earworm-hunt-app` pattern:

1. **Path filter** — add the app directory to `app-filter` in the
   `detect-changes` job:

   ```yaml
   - uses: dorny/paths-filter@v3
     id: app-filter
     with:
       filters: |
         toogether-app:
           - 'toogether-app/**'
         earworm-hunt-app:
           - 'earworm-hunt-app/**'
         my-app:                        # ← ADD
           - 'my-app/**'               # ← ADD
   ```

2. **Output** — add the new filter result to `detect-changes` outputs:

   ```yaml
   outputs:
     my-app-changed: ${{ steps.app-filter.outputs.my-app }}  # ← ADD
   ```

3. **Build job** — create a `build-my-app` job (copy `build-earworm-hunt-app`,
   replace project/scheme names with the `.xcodeproj` and scheme from your
   Xcode project):

   ```yaml
   build-my-app:
     name: Build & Test – my-app
     needs: detect-changes
     if: ${{ needs.detect-changes.outputs.my-app-changed == 'true' }}
     runs-on: macos-15
     # ... (copy the full job from build-earworm-hunt-app)
   ```

4. **SwiftLint job** — create a `swiftlint-my-app` job:

   ```yaml
   swiftlint-my-app:
     name: SwiftLint – my-app
     needs: detect-changes
     if: ${{ needs.detect-changes.outputs.my-app-changed == 'true' }}
     runs-on: macos-14
     # ... (copy from swiftlint-earworm-hunt-app)
   ```

5. **CI summary** — add both new jobs to the `ci-success` job:
   - Add to the `needs` list
   - Add failure checks to the `if` block in the "Check results" step

### 6.2 CODEOWNERS (`.github/CODEOWNERS`)

```
/my-project/    @wichtelimwald
```

### 6.3 Root README (`README.md`)

Add the project to the **Projects** table:

```markdown
| `my-project` | Brief description | 🚧 In Development |
```

### 6.4 Root Backlog (`docs/todo.md`)

Update the existing backlog entry from Phase 1 with the concept link:

```markdown
- [ ] [feat][P1][L] **MyProject** — Brief description
  - Project directory: [`my-project/`](my-project/)
  - Concept: [`my-project/docs/concepts/my-project.md`](my-project/docs/concepts/my-project.md)
  - Backlog: [`my-project/docs/todo.md`](my-project/docs/todo.md)
  - Next step: implement domain model
```

### 6.5 CLAUDE.md (root)

Add the project to the **Project Overview** table and update build & test
commands.

### 6.6 Architecture Overview (`docs/architecture/overview.md`)

Add the new project to the repository diagram if it introduces a new layer or
cross-project dependency.

---

## Phase 7 — Optional: Project-Specific Agents & Skills

**Goal:** Create specialised agents if the project has unique domain needs.

If the project needs domain-specific agents (e.g. a music domain expert for a
music app):

1. Create `<project>/.github/agents/<agent-name>.md` following the existing
   agent format.
2. Reference the agent in `<project>/copilot-instructions.md`.
3. Add a delegating agent in `.github/agents/` if the agent should be accessible
   mono-repo-wide.
4. Update `.github/context-router.md` with the new agent mapping.

If the project needs specialised skills:

1. Create `<project>/.github/skills/<skill-name>.md`.
2. Reference the skill in the project's `copilot-instructions.md`.

---

## Phase 8 — Concept Review & First PR

**Goal:** Get the concept reviewed and merge the scaffold.

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/add-my-project
   ```

2. **Open a PR** targeting `develop` with:
   - Link to the backlog entry in `docs/todo.md`
   - Summary of the concept and scaffold contents
   - Checklist from the PR template

3. **Request review** — the architecture-review agent and code-review agent will
   provide automated feedback.

4. **Address feedback** and merge.

---

## Checklist — New Project Setup

Use this checklist to track progress:

- [ ] Backlog entry added to `docs/todo.md`
- [ ] Product discovery interview completed
- [ ] Concept document written
- [ ] Project directory scaffolded (Package.swift or Xcode project)
- [ ] `copilot-instructions.md` created
- [ ] `docs/decisions/ADR-0001` created
- [ ] `docs/todo.md` (project-specific) created
- [ ] `README.md` created
- [ ] `.swiftlint.yml` copied and configured
- [ ] CI workflow updated (path filters + jobs)
- [ ] CODEOWNERS updated
- [ ] Root README updated (projects table)
- [ ] Root backlog updated (concept link)
- [ ] CLAUDE.md updated
- [ ] Local build & test passing
- [ ] PR opened and reviewed

---

## References

- Quick-start guide: [`HOW2START-NEW.md`](../../HOW2START-NEW.md)
- Interview prompt: [`docs/prompts/product-discovery-interview-prompt.md`](../../docs/prompts/product-discovery-interview-prompt.md)
- Interview template: [`docs/concepts/product-discovery-interview.md`](../../docs/concepts/product-discovery-interview.md)
- Concept template: [`docs/concepts/template.md`](../../docs/concepts/template.md)
- ADR template: [`docs/decisions/template.md`](../../docs/decisions/template.md)
- Template project: [`template-project/`](../../template-project/)
- CI workflow: [`.github/workflows/ci.yml`](../workflows/ci.yml)
- Contributing guide: [`CONTRIBUTING.md`](../../CONTRIBUTING.md)
- Toogether concept (reference): [`toogether/docs/concepts/activity-planning-app.md`](../../toogether/docs/concepts/activity-planning-app.md)
- Toogether interview (reference): [`toogether/docs/concepts/interview-questionnaire.md`](../../toogether/docs/concepts/interview-questionnaire.md)
