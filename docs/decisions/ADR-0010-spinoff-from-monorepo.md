# ADR-0010 — Spin-off `avatar-generation` into a Dedicated Repository

**Status:** Accepted
**Date:** 2026-05-20
**Related:** ADR-0012 in `wichtelimwald/assistance` (mono-repo split strategy)

## Context

`avatar-generation` originated as `scripts/avatar-generation/` inside
the Swift mono-repo `wichtelimwald/assistance`. It is a Python tool — it
has no Swift dependencies, runs in its own venv, and is invoked once per
new character cast (a few times per year).

Keeping a Python tool inside a Swift mono-repo had three structural
problems:

1. Mono-repo CI runs Swift toolchains; the Python tool's dependencies
   (Pillow, requests, Flask) had nowhere natural to live.
2. The tool's release cadence is decoupled from the apps' release
   cadence — bumping its dependencies should not require a mono-repo
   commit.
3. Other future projects (outside `wichtelimwald/`) might want to use the
   same generator; embedding it in a closed mono-repo blocks that.

## Decision

Extract `scripts/avatar-generation/` into a dedicated repository
`wichtelimwald/avatar-generation` without preserving Git history. The
new repo:

- Houses the Python package under `avatar_generation/` (renamed from
  the flat layout for PEP-8 friendliness).
- Ships the Flask selector UI under `selector/`.
- Has its own Python CI workflow (`.github/workflows/ci.yml`).
- Tags `v1.0.0` as the initial release (this tool is already in
  production use inside the mono-repo prior to spin-off — `0.x` would
  understate maturity).

## Consequences

**Positive**
- Independent release line.
- Standalone Python CI; faster signal.
- Reusable outside the `wichtelimwald/*` Apple-app family.
- The mono-repo no longer carries Python toolchain concerns.

**Negative**
- Consumers cloning a specific tag now (instead of running directly
  from the mono-repo working tree). Acceptable — the tool is run rarely.
- Two places to look for "how do I generate avatars?" until mono-repo
  cleanup deletes `scripts/avatar-generation/`.

## Implementation notes

- The migration script (`scripts/migrate-avatar-generation/migrate.sh`
  in the mono-repo) copies the Python sources, the `characters/` schema,
  and the `selector/` Flask app; renames the top-level package directory
  to `avatar_generation/`; pulls in `HOW2GENERATE-AVATARS.md` as
  `docs/USAGE.md`; and tags `v1.0.0`.
- `.env` and `output/` artefacts are explicitly skipped — they never
  enter the new repo.
- Mono-repo cleanup (deletion of `scripts/avatar-generation/` and
  `HOW2GENERATE-AVATARS.md`) is a separate PR.
