# ADR-XXXX – <Short Title>

**Date:** YYYY-MM-DD
**Status:** Proposed | Accepted | Deprecated | Superseded by ADR-XXXX
**Author(s):** 

---

## Context

<!-- Describe the situation and the problem that needs to be solved.
     What is the background? What constraints exist?
     Why does a decision need to be made now? -->

---

## Problem Statement

<!-- One clear sentence: what architectural question are we answering? -->

---

## Options Considered

### Option 1 – <Name>

**Description:**

**Pros:**
-

**Cons:**
-

---

### Option 2 – <Name>

**Description:**

**Pros:**
-

**Cons:**
-

---

### Option 3 – <Name> *(optional)*

**Description:**

**Pros:**
-

**Cons:**
-

---

## Decision Matrix

*Score each option 1 (worst) – 5 (best) for each criterion. Multiply by weight.
The 7 standard criteria are fixed across all ADRs. Up to 3 context-specific
criteria may be added (weight 2 each). All criteria in a single table.*

### Standard Criteria Derivation

The 7 standard criteria are informed by established software quality models —
primarily [ISO/IEC 25010](https://en.wikipedia.org/wiki/ISO/IEC_25010)
(Systems and Software Quality Requirements and Evaluation) and
[FURPS+](https://en.wikipedia.org/wiki/FURPS) — but **adapted and simplified**
for the practical needs of a multi-project Swift mono-repo. They are not a
1:1 extraction from either standard.

#### Mapping to ISO 25010

| Our Criterion | ISO 25010 Counterpart | Adaptation |
|---------------|----------------------|------------|
| Simplicity | Analysability (sub of Maintainability) | ISO 25010 measures how easy a system is to *diagnose*; we broaden this to emphasise low-complexity design from the start — fewer moving parts, less cognitive load. |
| Maintainability | Modifiability (sub of Maintainability) | Focused on ease of change. ISO 25010's broader Maintainability umbrella also includes sub-characteristics we cover separately (Reusability) or exclude (Testability — see below). |
| Extendability | Modularity (sub of Maintainability) | ISO 25010 Modularity enables extension through loose coupling. Extendability explicitly asks: can new behaviour be *added* without modifying existing code? Distinct from Maintainability, which is about *changing* existing behaviour. |
| Reusability | Reusability (sub of Maintainability) | Direct match. ISO 25010 defines this as reuse of assets across systems — in our case, across mono-repo projects. |
| Performance | Performance Efficiency | Direct match. Covers time behaviour, resource utilisation, and capacity. |
| Consistency | — (no direct counterpart) | Not a distinct ISO 25010 or FURPS+ characteristic. Evaluates the option's own specification clarity, behavioural predictability, and absence of edge cases. Cross-project alignment (using the same technology as other mono-repo projects) should be captured as a **context-specific** criterion when it matters. |
| Human Readability | Learnability (sub of Usability) | ISO 25010 Usability targets end users. Human Readability evaluates how easily **developers and reviewers** can read all artefacts they interact with — code, configuration files, external data formats, and specifications. |

#### Challenged Against Industry "Ilities"

Several widely-recognised quality attributes were considered but excluded from
the standard set. They remain available as **context-specific criteria** for
ADRs where they differentiate options.

| Excluded Attribute | ISO 25010 Category | Why excluded from standard set |
|--------------------|-------------------|-------------------------------|
| **Testability** | Maintainability | Valuable but rarely the *decisive* differentiator between architecture options in this mono-repo. When it matters (e.g. protocol-oriented vs concrete types), add as context-specific. |
| **Security** | Security | Critical but typically applies uniformly across viable options — insecure designs should not appear as candidates. When options differ in security posture, add as context-specific. |
| **Reliability** | Reliability | Table stakes — unreliable options should not be evaluated. If reliability genuinely differentiates (e.g. proven vs experimental library), add as context-specific. |
| **Portability** | Portability | This mono-repo targets iOS/macOS exclusively. If multi-platform support becomes relevant, add as context-specific. |
| **Scalability** | Performance Efficiency (Capacity) | Products serve small-to-medium audiences where scalability does not differentiate architecture options at this stage. |
| **Interoperability** | Compatibility | Partially covered by Reusability and Consistency. If system integration is a differentiator, add as context-specific. |

> **Guideline:** If an excluded attribute would change the decision outcome for
> a specific ADR, promote it to a context-specific criterion (weight 2) in that
> ADR's matrix.

#### Criteria and Weights

| Criterion | Weight | Why it matters |
|-----------|--------|----------------|
| **Simplicity** | 3 | Complexity is the primary source of bugs, onboarding friction, and maintenance cost. In a mono-repo, unnecessary complexity in one project leaks cognitive overhead into all others. Highest weight because each additional complexity point increases failure probability non-linearly. |
| **Maintainability** | 3 | Software spends most of its lifetime in maintenance. Decisions that make future changes easy and local reduce total cost of ownership. Equal to Simplicity because long-term maintenance cost almost always dominates initial development cost. |
| **Extendability** | 2 | Products evolve — new features, platforms, and requirements emerge. Decisions that accommodate extension without breaking changes reduce rework. Weight 2 balances foresight with YAGNI pragmatism. |
| **Reusability** | 2 | In a mono-repo, shared patterns, code, and conventions avoid duplication across projects. Reusability requires stable interfaces and consistent design. Weight 2 because not every decision has reuse potential — forcing reusability where it is unnatural increases coupling. |
| **Performance** | 2 | Slow builds, tests, parsing, or UI degrade developer and user experience. Weight 2 because performance is rarely the primary driver for architecture decisions, and premature optimisation is itself a complexity risk. |
| **Consistency** | 2 | Specification clarity and behavioural predictability of the option itself. A technology with an unambiguous spec, few edge cases, and deterministic behaviour across tools scores higher. Weight 2 because technical consistency matters but should not prevent adopting better approaches. **Note:** cross-project alignment (using the same technology as other mono-repo projects) is a separate concern — evaluate it as a context-specific criterion, not here. |
| **Human Readability** | 2 | Code and data are read far more often than written. Readable artefacts are easier to review, debug, and maintain. In AI-assisted workflows, readability helps humans verify generated output. Weight 2 because tooling (formatters, linters, syntax highlighting) can partially compensate for less readable formats. |

**Weight rationale:** Simplicity and Maintainability receive the highest weight
(3) because they have the strongest long-term impact on project health. The
remaining five criteria receive weight 2 — important but not dominant.
Standard criteria account for at least 73 % of the total weight (16 / 22 when
all 3 context-specific slots are used), ensuring decisions are primarily driven
by universal quality attributes rather than context-specific factors.

#### References

- [ISO/IEC 25010:2023 — Systems and software Quality Requirements and Evaluation (SQuaRE)](https://www.iso.org/standard/78176.html)
- [FURPS+ — Functionality, Usability, Reliability, Performance, Supportability](https://en.wikipedia.org/wiki/FURPS)
- [Software Quality Attributes (Wikipedia)](https://en.wikipedia.org/wiki/List_of_system_quality_attributes)

### Matrix Template

| Criterion | Weight | Option 1 | Option 2 | Option 3 |
|-----------|--------|----------|----------|----------|
| Simplicity | 3 | | | |
| Maintainability | 3 | | | |
| Extendability | 2 | | | |
| Reusability | 2 | | | |
| Performance | 2 | | | |
| Consistency | 2 | | | |
| Human Readability | 2 | | | |
| *Context-specific 1* | *2* | | | |
| *Context-specific 2* | *2* | | | |
| *Context-specific 3* | *2* | | | |
| **Weighted Total** | | | | |

---

## Decision

<!-- State the chosen option and the primary reason. -->

**Chosen:** Option X – <Name>

**Rationale:**

---

## Invariants (Must Hold)

<!-- List the invariants that must be preserved for this decision to remain valid. -->

- 
- 

---

## How to Change Safely

<!-- Step-by-step instructions for modifying this decision in the future. -->

- 
- 

---

## Consequences

### Positive
-

### Negative / Trade-offs
-

### Risks
-

---

## Follow-up Actions

- [ ] 
- [ ] 

---

## Supersedes / Superseded by

- **Supersedes:** N/A
- **Superseded by:** N/A

---

## Related Code

<!-- List relevant files, types, or functions affected by this decision. -->

-

---

## References

-
