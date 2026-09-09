# Credit Risk Prediction Engine — Lending Club

> Can historical origination-time data build a calibrated model that predicts
> lifetime charge-off risk for future 36-month loans — and can those
> probabilities be trusted as populations, policy and conditions change?

Lending Club accepted loans, 2007–2018Q4 · IRB-informed, not regulatory

**Project status: M0 — data, target and modelling-population viability audit.**
No model has been trained. M0 is not closed: the maturity cutoff is still open.

---

## What this is

A credit-risk **prediction** model, built from historical origination-time data,
with rigorous validation as the proof that its probabilities can be trusted —
not validation as the exercise itself.

```
historical loans  ->  model learns risk relationships  ->  new application
                                                        ->  calibrated probability
                                                            of lifetime charge-off
```

**Primary question.** Can historical origination-time data build a calibrated
model that predicts lifetime charge-off risk for future 36-month Lending
Club-like loans?

**Secondary.** Does it rank risk better than Lending Club's historical
`grade` / `sub_grade`? Does macroeconomic information genuinely available at
origination improve prediction on future vintages? How stable is it as borrower
populations, policy and economic conditions change?

Success is not the highest AUC. It is discrimination *and* calibration *and*
out-of-time stability *and* a stated domain of applicability.

### What it is not

The model's output is a risk estimate. Underwriting and pricing would be later
layers consuming it, and Lending Club data cannot validate either: the
counterfactuals are unobserved, so neither "we would have approved better
borrowers" nor "we would have priced better" is identifiable here.

Because the development sample contains only accepted loans, the model predicts
for applicants Lending Club would have accepted. Applied to one it would have
rejected, it extrapolates. That is a condition of applicability, not a footnote.

### Target

**Lifetime charge-off risk on sufficiently mature 36-month Lending Club
cohorts.** `Charged Off` → 1, `Fully Paid` → 0, over the contractual life.

Deliberately **not a Basel one-year PD**, and not a TTC or regulatory PD. The
files carry no first-delinquency, default or charge-off date and no monthly
performance panel, so a genuine 12-month horizon cannot be reconstructed without
an assumption that cannot be tested. Rejected alternatives are recorded in
[DECISIONS.md](DECISIONS.md).

## M0 findings so far

Full evidence in **[DATA_AUDIT.md](DATA_AUDIT.md)**. The headlines:

- **No default-date field exists**, which is why the target is lifetime rather
  than one-year. A proxy from `last_pymnt_d` was rejected: that field is early
  for prepaid loans as well as failed ones.
- **The snapshot is 2019-04, not 2018-12** — the filename names the last
  issuance quarter, not the observation cutoff.
- **Maturity is measured, not assumed.** Resolution is vertical to +2 months
  past contractual term and flat from +3. Population-level censoring bias is
  0.27% relative even at the loosest cutoff, and the rate drift across cutoffs
  is vintage composition rather than bias correction.
- **Off-policy loans default at twice the rate** and concentrate in 2007–2008,
  where they are 58% and 35% of the book. Removing them halves the apparent
  crisis peak.
- **Standardising for FICO×DTI reverses the story twice.** The apparent upward
  trend from 2011 to 2015 is composition and disappears; a 2008–2009 elevation
  the crude series understated appears, because the crisis cohorts had *better*
  observables.
- **The benchmark's calibration drifts sharply.** Grade F defaulted at 18.4% in
  2012 and 42.1% in 2015 while grade A stayed flat — so `grade` got better at
  ranking while its level meaning moved. A pooled `grade → PD` mapping is not a
  stable yardstick.

### Still open

- The **maturity cutoff** (+3 or +5): 53,014 loans and the 2016 vintage against
  0.13 points of relative bias.
- **Macro viability.** The crisis elevation is real but sits in 1.07% of the
  population, and after 2010 there is no trend left to explain. M6 remains a
  strictly predictive question — does origination-time macro improve out-of-time
  prediction — evaluated walk-forward on expanding windows, never as a causal
  claim about recessions.

### Out of scope

Cash-flow underwriting, financial networks, household and legal context,
cross-border evidence, country adapters, age and gender fairness analysis, and
any AI agent. The data required to validate those layers is not in this project,
and architecture without evidence is not a result.

---

## Reproducing

The Lending Club files are not in this repository. Download
`wordsforthewise/lending-club` from Kaggle into `data/raw/` without
decompressing, then:

```bash
uv sync --locked --all-extras
uv run python projects/02-credit-risk/src/audit_schema.py   # what the files contain
uv run python projects/02-credit-risk/src/population.py     # build the local table
```

Both fail with instructions if the source is missing.

## Approach

_Not written yet — no model has been trained._

## Results

_Not written yet._

## Limitations

_Not written yet — beyond those already recorded in DECISIONS.md._

## What I would do next

_Not written yet._
