# Decisions

One entry per technical choice a reviewer could reasonably question. Written when
the decision is made, not reconstructed afterwards.

---

## 001 — Project framing, and why the target is not a one-year PD

**Date:** 2026-09-04

### What this project is

An **IRB-informed PD challenger / model-validation case study**. Not an
underwriting engine, not a pricing engine, not a production IRB model, and not a
regulatory compliance exercise.

**Research question.** Can an origination-time PD challenger produce calibrated,
temporally robust risk estimates and improve risk differentiation relative to
Lending Club's historical rating system on the observed accepted-loan
population — and under what conditions does that challenger cease to be reliable?

**Secondary, conditional on the temporal audit supporting it.** If sufficient
macro variation exists, does adding point-in-time macroeconomic information
available at origination improve out-of-time discrimination or calibration?

**Primary reader.** A model validation team receiving a challenger and deciding
whether it can be trusted for its proposed scope. Their output is one of: fit for
purpose, recalibrate, restrict scope, monitor, keep as challenger, reject. The
project does not decide whether an individual borrower gets a loan, and it does
not set prices — Lending Club data cannot identify either counterfactually.

### Baseline and benchmark are different things

| | What it is | What it tests |
|---|---|---|
| **Baseline** | The unconditional historical default rate. Every borrower gets the same PD. | Whether the modelling process contains *any* borrower-level information beyond the population average. Essentially zero discrimination by construction. |
| **Benchmark** | Lending Club's historical `grade` / `sub_grade`. | Whether the challenger differentiates risk better than the incumbent system did. |

Conflating them makes the comparison meaningless. The benchmark also carries a
limit that must be stated wherever it appears: `grade` set the interest rate,
which set the instalment, which affects repayment. The benchmark is **causally
upstream of the outcome**, not merely correlated with it.

Therefore the project may claim *"the challenger differentiated subsequent
observed credit risk better than the historical grade among accepted
borrowers"*. It may **not** claim better pricing or a better approval policy.

### The target: what the data actually permit

The methodologically preferable target would be a fixed 12-month horizon: it
gives every loan the same observation window, removing the exposure bias that
otherwise makes older vintages look riskier simply for having been watched
longer. It is also the Basel horizon.

**It cannot be built from these files.** The accepted dataset carries `issue_d`,
`last_pymnt_d`, `next_pymnt_d`, `last_credit_pull_d`, and hardship/settlement
dates for small selected subsets. It does **not** carry a first-delinquency date,
a default date, a charge-off date, or a monthly performance panel.

A related trap, recorded because it is a common error: `mths_since_last_delinq`
and its relatives are **bureau fields measured at origination about the
borrower's prior history**. They say nothing about this loan's performance.

No public, legitimately redistributable monthly performance panel linkable by
loan id was found. Research using Lending Club payment data exists, but that data
came from the investor feed rather than an open publication. Building on a source
that cannot be redistributed would break the project's reproducibility claim.

### Alternatives considered

- **A — lifetime charge-off on a sufficiently mature population.** `Charged Off`
  against `Fully Paid`, restricted to cohorts old enough to have resolved.
  Directly observable. Not a one-year PD.
- **B — a 12-month proxy from `last_pymnt_d`.** Requires conditioning on
  `Charged Off`, because `last_pymnt_d` is also early for loans that *prepaid*,
  and Lending Club borrowers prepay often. Even conditioned, it measures the
  cessation of payment rather than default, and misses a borrower who stopped at
  month 6, resumed, and failed at month 20. The assumption that it approximates
  12-month default is precisely the one that cannot be checked, since checking it
  would need the panel that does not exist.
- **C — switch to Fannie Mae / Freddie Mac**, which publish monthly performance
  and therefore support a genuine one-year PD. Rejected for now: neither publishes
  a per-loan lender rating, so the incumbent benchmark disappears and with it the
  comparison that defines this project.

### Decision

**A**, provisionally, described only as:

> **lifetime charge-off risk on sufficiently mature Lending Club loan cohorts**

It is the only option that does not require believing something unverifiable.

**Explicitly prohibited:** calling this a Basel one-year PD, a TTC model, a
structural PD, or a regulatory PD. The application-only model is an
*application-only pooled PD model*; the extension is an *application +
point-in-time macro challenger*.

### The refinement that keeps A honest

`issue_d + contractual term ≤ snapshot` does **not** imply a resolved cohort.
Charge-off follows the last payment by some months, so a loan that deteriorates
near the end of its term can be charged off after its contractual maturity and
land outside the snapshot.

Maturity is therefore **measured, not assumed**. M0 computes terminal-resolution
rate as a function of cohort age for each `issue vintage × term`, and the cutoff
is chosen with that distribution in view.

Two things the threshold decision must keep apart:

1. **Censoring is informative.** Loans still unresolved at an age past their term
   are disproportionately `Late` or `In Grace Period` — near-certain future
   charge-offs. Dropping them biases the default rate *downward*, and the bias
   grows as the threshold falls.
2. **Dropping and assigning are different decisions.** Whether `Late (31-120)`,
   `Default` and `In Grace Period` are treated as bad, good, or excluded is a
   separate judgement from where the threshold sits, and conflating them hides it.

A stricter threshold also pushes the population toward older vintages, which is
where the crisis exposure is. Part of the sample-size cost may return as macro
variation for the secondary question.

Loans flagged `Does not meet the credit policy` are a distinct population and get
their own decision rather than being swept in.

### Open until M0 reports

- Whether enough sample and enough defaults survive the maturity filter.
- Whether enough defaults come from 2007-2010 for the macro question to exist.
- Whether 36- and 60-month loans can share a population or need separating.

---

## 002 — The predictive model is the project; validation is the quality layer

**Date:** 2026-09-09

### Change

Decision 001 framed this as a model-validation case study with a challenger
attached. That hierarchy is inverted. The project builds a **credit-risk
prediction model**, and validation is what establishes whether its probabilities
can be trusted — not an end in itself.

**Primary question.** Can historical origination-time data build a calibrated
model that predicts lifetime charge-off risk for future 36-month Lending
Club-like loans?

**Secondary.** Does it out-rank Lending Club's historical grade? Does
origination-time macro information improve prediction on future vintages? How
stable is it as borrower populations, policy and conditions change?

Nothing methodological is dropped. The same artefacts get built in the same
order; what changes is which number leads and how the work is narrated.

### Two consequences that are not merely presentational

**The accepted-only limitation is promoted, not demoted.** Under a validation
framing, "we only observe accepted loans" was a note about representativeness.
Under a predictive framing — *estimate the risk of a new application* — it
becomes a **condition of applicability**: the model predicts for applicants
Lending Club would have accepted. Applied to one it would have rejected, it
extrapolates. That belongs in the model card as scope, not as a caveat.

**The leakage test gets sharper.** "Would the lender have known this at
origination?" invites argument. The product framing supplies a better one:
**would this field be present in the API request for a new application?** It is
harder to rationalise around, and it is the test M2 will use.

### What the output means

A prediction of 0.18 means: for a new 36-month loan inside the domain of
applicability represented by the accepted, policy-compliant historical loans used
to develop the model, an estimated 18% probability of ending in `Charged Off`
over its contractual life.

The maturity buffer belongs to the construction of the historical development
sample. It is not a condition a new application has to satisfy.

Still prohibited: calling this a Basel one-year PD, a TTC PD, or a regulatory PD.
