# Credit Risk — PD Challenger and Model Validation

> A model validation team receives an origination-time PD challenger. Can it be
> trusted, under what conditions, and what controls would it need?

Lending Club accepted loans, 2007–2018Q4 · IRB-informed, not regulatory

**Status:** M0 — data and temporal viability audit.

---

## Problem

An independent validation team is handed a challenger PD model built on
origination-time information, alongside the incumbent system that actually ran:
Lending Club's own `grade` / `sub_grade`.

Their task is not to certify the model as correct under Basel. It is to decide
whether it can be relied on for a defined scope, and to say what would have to be
true for that to hold.

**The decision this analysis supports is at the model level**, not the borrower
level:

| Outcome | Meaning |
|---|---|
| Fit for purpose | Reliable enough for its defined scope |
| Recalibrate | Ranking is useful, predicted levels are systematically wrong |
| Restrict scope | Works in some populations or vintages, not universally |
| Monitor | Acceptable, but calibration or population drift needs watching |
| Keep as challenger | Informative, does not yet justify replacing the incumbent |
| Reject | Not reliable enough for the proposed use |

### Research question

Can an origination-time PD challenger produce calibrated, temporally robust risk
estimates and improve risk differentiation relative to Lending Club's historical
rating system on the observed accepted-loan population — and under what
conditions does that challenger cease to be reliable?

Conditional secondary question: if sufficient macro variation exists, does
point-in-time macroeconomic information available at origination improve
out-of-time discrimination or calibration?

### Estimand

**Lifetime charge-off risk on sufficiently mature Lending Club loan cohorts.**

Deliberately *not* a Basel one-year PD. The data carry no first-delinquency,
default or charge-off date, and no monthly performance panel, so a genuine
12-month horizon cannot be reconstructed without an assumption that cannot be
tested. Reasoning and the rejected alternatives:
[DECISIONS.md](DECISIONS.md#001--project-framing-and-why-the-target-is-not-a-one-year-pd).

### Out of scope

Cash-flow underwriting, financial networks, household and legal context,
cross-border evidence, country adapters, age and gender fairness analysis, and
any AI agent. The data required to validate those layers is not in this project,
and architecture without evidence is not a result.

---

## Approach

_Not written yet._

## Results

_Not written yet._

## Limitations

_Not written yet — beyond those already recorded in DECISIONS.md._

## What I would do next

_Not written yet._
