# Product Analytics & Experimentation

> One quarter, capacity for one change: fix the checkout, or work on repeat
> purchase? And can the data we have actually tell them apart?

**Status:** in progress — problem framed, analysis not started.

<!--
Sections below Problem are written from real results, not predicted ones. They
stay empty until there is something true to put in them.
-->

---

## Problem

The Google Merchandise Store has capacity for one product change this quarter.
Two candidates are on the table and there is no budget for both:

- **Reduce friction in the purchase funnel.**
- **Work on repeat purchase** from customers who already bought once.

**Who decides:** whoever prioritises the quarterly roadmap.

**What changes with the answer:**

| Finding | Decision |
|---|---|
| The large leak is inside the purchase funnel | Invest in checkout |
| Purchases convert well but customers do not return | Invest in repeat purchase |
| The data cannot distinguish the two | Invest in instrumentation first |

The third branch is not a hedge. This dataset is obfuscated and its user
identifier is known to be unstable, so "we cannot answer this yet, and here is
precisely what is blocking it" is a legitimate — and actionable — outcome.

### Research questions

1. **Can I trust the data?** Data-quality audit and identity resolution, with
   retention as the concrete case. Hypothesis under test: `user_pseudo_id`
   instability distorts the retention curve, plausibly varying by browser. This
   is treated as a hypothesis to falsify, not a conclusion to confirm.
2. **Where does conversion break?** One funnel, built carefully, at a justified
   grain — rather than many shallow cuts.
3. **Can I trust an apparently winning experiment?** A blinded synthetic
   treatment layer over real users, carrying two deliberate pathologies: sample
   ratio mismatch and a heterogeneous treatment effect. Validity is checked
   *before* the effect is estimated; ground truth is revealed only at the end.

### Data

`bigquery-public-data.ga4_obfuscated_sample_ecommerce` — Google Merchandise
Store, 1 Nov 2020 – 31 Jan 2021, 92 daily tables, ~4.3M events.

Public and obfuscated by Google. No private or company data is used anywhere in
this portfolio.

Pipeline: extract and flatten in BigQuery (`UNNEST` over `ARRAY<STRUCT>`), pin
an exported snapshot with a checksum, analyse locally in DuckDB. The snapshot is
pinned because reproducibility from an external source is only as stable as that
source — a public dataset can be revised or withdrawn.

### Unit of analysis

Dual by grain: sessions for the funnel, pseudonymous identifiers for retention
and randomisation, no reconstructed identity. Reasoning and the cost of that
choice: [DECISIONS.md](DECISIONS.md#001--unit-of-analysis-dual-by-grain-no-identity-reconstruction).

---

## Approach

_Not written yet._

## Results

_Not written yet._

## Limitations

_Not written yet — beyond those already recorded in DECISIONS.md._

## What I would do next

_Not written yet._

---

## Reproducing

_Not written yet._

## Files

```
notebooks/   Exploration, numbered in reading order
src/         Reusable code
tests/       Tests mirroring src/
data/        Gitignored — rebuilt from the pinned snapshot
```
