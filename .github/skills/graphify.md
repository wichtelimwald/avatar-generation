---
name: graphify
description: >
  Codebase knowledge graph. Query the graph instead of grepping when answering
  questions about architecture, file relationships, or project content.
  Canonical skill: .claude/skills/graphify/SKILL.md (mirrored in .copilot/ and .agents/).
---

# Skill: graphify

Graphify turns the repo (code, docs, PDFs, images) into a persistent, queryable
knowledge graph with god nodes, community detection, and an EXTRACTED/INFERRED
audit trail. Outputs live in `graphify-out/` (`graph.json`, `GRAPH_REPORT.md`, `graph.html`).

> The full skill — usage, flags, and the build pipeline — is `.claude/skills/graphify/SKILL.md`
> with detailed `references/`. This file is the router entry; do not duplicate it here.

## When to Use

- **Any codebase question** ("How does X work?", "What calls Y?", "Trace data flow through Z")
  when `graphify-out/graph.json` exists — treat it as a graph query first.
- Architecture review, impact analysis, cross-file relationship discovery.

## Core Commands

| Goal | Command |
|------|---------|
| Ask a question | `graphify query "<question>"` |
| Relationship between two nodes | `graphify path "<A>" "<B>"` |
| Explain one concept | `graphify explain "<node>"` |
| Impact of a change | `graphify affected "<X>"` |
| Architectural hubs | `graphify god-nodes` |
| Build / rebuild everything | `/graphify .` |
| Update after code edits (no LLM) | `graphify update .` |

## Rules

- Prefer `graphify query` over raw grep/read for codebase questions when the graph exists.
- Read `graphify-out/GRAPH_REPORT.md` only for broad architecture review.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
- Install / re-install the assistant integrations with `graphify install --project --platform <claude|copilot|agents|…>`.

## Setup

```bash
uv tool install graphifyy        # or: pipx install graphifyy
graphify install --project --platform claude,copilot,agents
```
