---
name: Product Delegators
description: >
  Index of product-domain agents that delegate to project-specific implementations.
  Each entry routes to the actual agent in the target project's .github/agents/ directory.
model: claude-sonnet-4
scope: global
version: "2.0"
last-updated: "2026-04-03"
tools:
  - read
  - search
---

# Product Delegators

> These are **delegating agents**. Project-specific implementations live in
> `<project>/.github/agents/<agent-name>.md`. Use the project-specific agent
> directly when working on the corresponding task.

## Delegated Agents

| Agent | Purpose | Project Locations |
|-------|---------|-------------------|
| **Lead Designer** | Design system | `toogether/.github/agents/lead-designer.md` |
| **UX Expert** | User experience | `toogether/.github/agents/ux-expert.md` |
| **Asset Designer** | Visual asset generation | `toogether/.github/agents/asset-designer.md` |
| **Asset Design Developer** | Programmatic visual effects | `toogether/.github/agents/asset-design-developer.md` |
| **Brand & Content** | Brand, content strategy, marketing | `toogether/.github/agents/brand-content.md` |
| **Product Strategy** | Business model, product discovery | `toogether/.github/agents/product-strategy.md` |
| **Character Maintenance** | Avatar characters | `toogether/.github/agents/character-maintenance.md` |
