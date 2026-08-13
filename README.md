# avatar-generation

Python tool to batch-generate branded avatars for the `wichtelimwald/*`
Apple apps via the [Leonardo.ai](https://leonardo.ai) image-generation
API, with a small Flask-based selector UI for review and curation.

> Spun off in 2026 from `wichtelimwald/assistance:scripts/avatar-generation/`.
> See [`docs/decisions/ADR-0010-spinoff-from-monorepo.md`](docs/decisions/ADR-0010-spinoff-from-monorepo.md).

---

## Requirements

- Python 3.10+
- A Leonardo.ai API key (free tier is sufficient for low-volume runs)

## Setup

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
pip install -r selector/requirements.txt
```

Create a `.env` (never commit it) with at minimum:

```
LEONARDO_API_KEY=sk-...
```

## Usage

See [`docs/USAGE.md`](docs/USAGE.md) for the full run-book (character
config, prompt building, batch generation, selector UI).

Quick start:

```bash
python -m avatar_generation.generate --character cast/01-laila
```

## Layout

```
avatar_generation/        Python package (config, generate, prompt_builder, …)
characters/               Character schemas + example casts
selector/                 Flask app for reviewing batch output
docs/USAGE.md             End-to-end run-book
.github/                  Copilot config + CI
```

## Versioning

This tool follows semver. The migration creates `v1.0.0` as the initial
tag (already in production use inside the mono-repo prior to spin-off).
