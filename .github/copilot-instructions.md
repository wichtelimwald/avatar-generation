# GitHub Copilot – Instructions (avatar-generation)

Python CLI tool · Python 3.10+ · Flask selector UI.

This repository contains exactly **one** Python tool: avatar-generation.
It batch-generates branded character avatars via the Leonardo.ai API
and lets a human curator pick keepers via a small Flask web UI.

---

## Scope

Domain context: [`docs/USAGE.md`](../docs/USAGE.md).

Consumers: every `wichtelimwald/*` Apple app that ships character
avatars (toogether, studienmap, …) clones this repo at a tagged version
when (re)generating its asset set.

---

## Architecture & Principles

- **Single-purpose CLI** — one tool, one job, no plugin system.
- **Idempotent runs** — re-running `generate` against an already-rendered
  character should be a no-op (skip + log).
- **Never log secrets** — `LEONARDO_API_KEY` only via env, never in error
  messages or generated metadata.
- **Selector UI is read-only** with respect to the API — no generation
  is triggered from the web UI.

---

## Hard Gates

- No code before design — non-trivial features need a spec.
- No fixes without root cause.
- Never commit `.env`, API keys, or any output/ artefacts.
- Never commit to `main` — all work on branches.

---

## Code Style

| Rule | Value |
|------|-------|
| Language | English |
| Naming | PEP 8 |
| Formatting | 4-space indent, 100 char max, `black`-compatible |
| Type hints | Required on every function signature |
| Errors | Raise typed exceptions; no bare `except:` |
| Logging | `logging` module; never `print()` from library code |

---

## Build & Test

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python -m py_compile avatar_generation/*.py
```

---

## Release Workflow

1. Land changes on `main` via PR.
2. Tag `v<x.y.z>` and push.
3. (Optional) Create a GitHub Release.
