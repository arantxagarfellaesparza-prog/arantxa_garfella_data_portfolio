# Data audit — M0

Findings from the data, target and modelling-population viability audit.
**M0 is closed.** The maturity cutoff is frozen at +3 months past contractual
term (DECISIONS 004); the sensitivity analysis behind that choice is in §3.

Source: `bigquery`-free — Lending Club accepted and rejected loans, 2007 to
2018Q4, from the public Kaggle mirror. 2,260,668 accepted loans, 151 columns.

Reproduce with `src/audit_schema.py` and `src/population.py`. The source files
are not in this repository and the scripts say how to obtain them.

---

## 1. Target timestamp gate

A fixed 12-month horizon would be preferable: it gives every loan the same
observation window, so older vintages do not look riskier merely for having been
watched longer.

**It cannot be built from these files.** Confirmed against the file rather than
against the published data dictionary:

| Present | Absent |
|---|---|
| `issue_d`, `last_pymnt_d`, `next_pymnt_d`, `last_credit_pull_d` | First-delinquency date |
| `hardship_start_date`, `hardship_end_date`, `payment_plan_start_date` | Default date |
| `debt_settlement_flag_date`, `settlement_date` | Charge-off date |
| | Monthly performance panel |

A trap worth naming: `mths_since_last_delinq` and its thirteen relatives are
**bureau fields measured at origination about the borrower's prior history**.
They describe the applicant, not this loan's performance, and are routinely
mistaken for the latter.

No public, legitimately redistributable monthly performance panel linkable by
loan id was found. Research on Lending Club payment data exists, but that data
came from the investor feed.

**Consequence.** The target is lifetime charge-off on mature cohorts, not a
one-year PD. A proxy built from `last_pymnt_d` was rejected: that field is early
for loans that *prepaid* as well as loans that failed, and even conditioned on
`Charged Off` it measures the cessation of payment rather than default — on an
assumption that could only be checked with the panel that does not exist.

## 2. The snapshot is four months later than the filename suggests

`max(last_credit_pull_d) = 2019-04`, against a maximum `issue_d` of 2018-12. The
file is named for the last issuance quarter, not the observation cutoff. Cohort
age is computed against the derived date; assuming 2018-12 would have discarded
four months of maturity.

## 3. Maturity is measured, not assumed

`issue_d + term <= snapshot` does **not** imply a resolved cohort: charge-off
follows the last payment by some months, so a loan deteriorating near the end of
its term resolves after its contractual maturity.

Terminal resolution by months past contractual term:

| months past term | 36m terminal | 60m terminal |
|---:|---:|---:|
| 0 | 69.2% | 84.5% |
| +1 | 87.2% | 93.5% |
| +2 | 98.4% | 98.5% |
| +3 | 99.4% | 99.7% |
| +5 | 99.9% | 100% |

Vertical to +2, flat from +3, in both books.

### Cutoff sensitivity — the decision is nearly free

Cumulative population (36-month, policy-compliant), where the residue is what
the bias depends on:

| cutoff | N | defaults | residue | rate | upper bound | rel. bias | marginal loss | last vintage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| +2 | 670,015 | 93,477 | 0.110% | 13.967% | 14.005% | 0.27% | — | 2016 |
| +3 | 641,406 | 89,188 | 0.045% | 13.911% | 13.932% | 0.15% | 4.27% | 2016 |
| +5 | 588,392 | 81,241 | 0.008% | 13.808% | 13.811% | 0.02% | 4.90% | 2015 |
| +6 | 563,123 | 77,511 | 0.004% | 13.765% | 13.766% | 0.01% | 4.29% | 2015 |
| +9 | 487,215 | 66,604 | 0.001% | 13.670% | 13.670% | 0.00% | 4.68% | 2015 |

Two things this settles.

**Censoring is informative but small.** At the cohort margin the unresolved
residue is two-thirds `Late` and `In Grace Period` rather than healthy `Current`
loans, so dropping it understates default. At population level the effect is
0.27% relative even at +2.

**The rate drift across cutoffs is vintage composition, not bias correction.**
The measured rate falls from 13.97% to 13.67% as the cutoff tightens because
stricter cutoffs drop recent vintages, which default more. Reading that column as
a bias correction would invert the interpretation.

Marginal sample loss is flat at 4–5% per month, so there is no knee to find.

**Frozen at +3** (DECISIONS 004): 641,406 loans, 89,188 charge-offs, originated
2007-06 to 2016-01. Moving to +5 would drop 53,014 loans — two months, 2015-12
and 2016-01 — to remove 0.13 points of a bias already at 0.15%.

## 4. Population composition

| status | loans | share |
|---|---:|---:|
| Fully Paid | 1,076,751 | 47.63% |
| Current | 878,317 | 38.85% |
| Charged Off | 268,559 | 11.88% |
| Late (31–120 days) | 21,467 | 0.95% |
| In Grace Period | 8,436 | 0.37% |
| Late (16–30 days) | 4,349 | 0.19% |
| Does not meet the credit policy | 2,749 | 0.12% |
| Default | 40 | 0.002% |

`Default` has forty loans in 2.26 million: Lending Club moves from `Late` to
`Charged Off` without using it, so it is not a usable category.

### Off-policy loans are a separate population

They default at roughly twice the rate and are concentrated in exactly the
vintages the macro question needs — 58% of the 2007 book and 35% of 2008.

| vintage | policy-compliant n | rate | off-policy n | rate |
|---|---:|---:|---:|---:|
| 2007 | 251 | 17.93% | 352 | 32.10% |
| 2008 | 1,562 | 15.81% | 831 | 29.96% |
| 2009 | 4,716 | 12.60% | 565 | 22.83% |
| 2010 | 8,466 | 9.95% | 690 | 22.90% |

Removing them halves the apparent crisis peak: the pooled range was 26.2% to
10.9%, and the policy-compliant range is 17.9% to 9.95%. Roughly half of what
looked like a cycle effect was a population Lending Club stopped approving.

### 36- and 60-month loans are different products

| term | N | defaults | rate | period | mean rate | median amount |
|---|---:|---:|---:|---|---:|---:|
| 36 | 588,392 | 81,241 | 13.81% | 2007–2015 | 12.06% | $10,000 |
| 60 | 51,048 | 12,838 | 25.15% | 2010–2013 | 17.31% | $20,000 |

Sixty-month loans add 8.7% more sample at nearly double the default rate, five
points more interest, twice the loan size, and **no exposure to 2007–2009**.
Provisionally excluded from the primary model.

### Hardship and settlement need no special rule

Settlement is coded correctly: 20,693 of 21,232 end `Charged Off` and four end
`Fully Paid`. Hardship loans are 45% unresolved — the programme extends the
schedule — so the maturity filter already removes them without a dedicated
exclusion.

## 5. The population changed enormously, and adjustment reverses the trend

Medians by vintage, 36-month policy-compliant:

| vintage | FICO | DTI | revolving util. | credit history | amount |
|---|---:|---:|---:|---:|---:|
| 2007 | 705 | 9.9 | 37.6 | 10.8 y | $6,500 |
| 2010 | 710 | 12.8 | 47.3 | 12.1 y | $8,250 |
| 2012 | 695 | 16.2 | 60.2 | 13.1 y | $10,000 |
| 2015 | 685 | 17.9 | 52.5 | 15.0 y | $10,000 |

The safest FICO×DTI cell fell from 30.1% of the 2007–2010 book to 8.1% of 2015;
the riskiest rose from 2.3% to 11.8%.

All nine FICO×DTI cells are populated in every vintage group (smallest cell
n=340), so there is common support and direct standardisation is not
extrapolation.

Standardised to the 2015 composition:

| vintage | n | crude | standardised | 95% CI |
|---|---:|---:|---:|---|
| 2007 | 251 | 17.93% | 25.59% | [16.92, 34.26] |
| 2008 | 1,562 | 15.81% | **17.38%** | [14.92, 19.83] |
| 2009 | 4,716 | 12.60% | 15.36% | [13.79, 16.93] |
| 2010 | 8,466 | 9.95% | 12.40% | [11.38, 13.42] |
| 2011 | 14,101 | 10.63% | 13.56% | [12.75, 14.38] |
| 2012 | 43,470 | 13.58% | 14.96% | [14.59, 15.32] |
| 2013 | 100,422 | 12.33% | **12.88%** | [12.67, 13.09] |
| 2014 | 162,570 | 13.73% | 13.81% | [13.64, 13.97] |
| 2015 | 252,833 | 14.80% | 14.80% | [14.66, 14.94] |

Standardisation does two opposite things at once.

**It removes the apparent upward trend from 2011 to 2015.** Crude 10.63% →
14.80% looks like rising risk; standardised it oscillates without direction. That
movement was composition.

**It reveals a crisis-era elevation the crude series understated.** 2008 rises
from 15.81% to 17.38% while 2010 sits at 12.40%. The 2008 and 2013 intervals do
not overlap. Because the crisis cohorts had *better* observables, adjusting for
them makes their excess default larger, not smaller.

2007 rises to 25.6% but on 251 loans the interval spans 16.9 to 34.3 and
supports nothing.

**The finding is invariant to the maturity cutoff**: the 2008-minus-2013 gap is
4.49–4.50 points at every cutoff from +2 to +8.

## 6. The benchmark's calibration drifts sharply

Default rate within `grade`, 36-month policy-compliant:

| vintage | A | B | C | D | E | F | G |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2010 | 4.4 | 9.3 | 12.7 | 16.1 | 19.2 | — | — |
| 2012 | 7.2 | 12.6 | 17.6 | 21.1 | 21.9 | 18.4 | — |
| 2013 | 4.6 | 9.8 | 15.3 | 20.4 | 23.3 | 26.8 | — |
| 2014 | 5.4 | 10.7 | 17.2 | 22.2 | 27.0 | 29.5 | 36.3 |
| 2015 | 5.4 | 11.8 | 19.3 | 25.9 | 32.5 | 42.1 | 44.4 |

Grade F went from 18.4% in 2012 to 42.1% in 2015. Grade A stayed between 4.4%
and 7.2%.

Discrimination and calibration move in opposite directions: the A-to-worst-grade
spread widened from 14.8 points in 2010 to 39 points in 2015, so grade got
**better at ranking** while its **level meaning drifted badly**.

Consequence for the benchmark comparison: a pooled `grade → PD` mapping is not a
stable yardstick, and an apparent challenger improvement out of time could partly
reflect the incumbent deteriorating. The comparison has to be made per vintage,
with discrimination and calibration reported separately.

## 7. The rejected file is thin

Nine columns against 151, with `Application Date` at daily granularity where the
accepted file is monthly. The selection analysis in M3 lives inside that limit,
and no reject-inference method is attempted.

---

## Carried into M1 and beyond

**Macro viability is the weakest part of the plan, and is documented as such.**
The crisis elevation is real and survives adjustment, but it sits in 6,278 loans
— 1.07% of the population — and after 2010 there is no trend left to explain,
only a ~2-point year-to-year oscillation. Walk-forward validation makes that
conflict explicit rather than solving it: with an expanding window the crisis
falls into training in almost every fold. M6 proceeds as a predictive test, and
a null result would be a legitimate finding rather than a failure.
