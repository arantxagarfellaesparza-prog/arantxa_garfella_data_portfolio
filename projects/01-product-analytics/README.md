# Product Analytics & Experimentation

> One quarter, capacity for one change: fix the checkout, or work on repeat
> purchase? And can the data we have actually tell them apart?

Public GA4 e-commerce sample · 4.3M events · 92 days · 270,154 identifiers

**Status:** complete. Full reasoning in [DECISIONS.md](DECISIONS.md).

---

## Problem

The Google Merchandise Store has capacity for one product change this quarter,
and two candidates with no budget for both: reduce friction in the purchase
funnel, or work on repeat purchase from existing customers.

Whoever prioritises the roadmap decides. What changes with the answer:

| Finding | Decision |
|---|---|
| The large leak is inside the purchase funnel | Invest in checkout |
| Purchases convert but customers do not return | Invest in repeat purchase |
| The data cannot distinguish the two | Invest in instrumentation first |

That third branch is not a hedge. This dataset is obfuscated and its user
identifier is known to be unstable, so "we cannot answer this yet, and here is
exactly what is blocking it" is a legitimate outcome.

Three research questions: **can I trust the data**, **where does conversion
break**, and **can I trust an apparently winning experiment**.

---

## What the analysis found

### The recommendation

**Repeat purchase drops down the list.** Converted to the unit the business
counts, it is the smallest of the three available levers — and its figure is a
ceiling rather than an estimate.

**Discovery and conversion tie, and cannot be separated by arithmetic.**

| lever | base rate | +1pp | +10% relative | uplift |
|---|---:|---:|---:|---:|
| Discovery — sessions reaching a product | 21.39% | 227 | **485** | 10.0% |
| Conversion — viewers who purchase | 6.29% | 770 | **485** | 10.0% |
| Retention — identifiers returning | 17.53% | 141 | 246 *(ceiling)* | 5.1% |

They tie *necessarily*: purchases decompose as
`sessions × P(view) × P(buy | view)`, so scaling either factor by 1.10 scales
purchases by 1.10. Only feasibility can rank them, and feasibility is not in
this data. The analysis supplies the derivative; the roadmap owner supplies the
achievability.

**The question offered the wrong choice.** `conversion` is approximately "fix
checkout". `discovery` — getting visitors to a product page at all — ties with
it and was not on the list. 78.6% of sessions never see a product, the single
largest drop anywhere in this funnel.

**No specific checkout intervention is recommended**, because the funnel's
interior is not measurable. See limitations.

### The counter-intuitive part

Read as raw leak rates, retention looks like the biggest problem in the
business: 82.47% of identifiers never come back. Converted to incremental
purchases it is the *smallest* lever, at roughly half the others.

The gap between those two readings is the difference between a leak rate and a
marginal impact, and it points the roadmap in opposite directions.

### Q1 — can I trust the data?

82.47% of identifiers have exactly one session. The working hypothesis was that
browser tracking prevention resets identifiers and manufactures that number.

**It does not.** Single-session share is 82.37% on Safari against 82.47% on
Chrome — a difference of −0.10pp, in the wrong direction, across a 0.91pp spread
over six browsers. At n = 183,734 and 64,857 the minimum detectable difference
is ~0.5pp while real identifier churn would produce tens of points, so this is a
well-powered null rather than an absent result.

Something else is wrong instead. Between 1.0% and 2.9% of identifiers appear
under more than one browser, which a first-party cookie makes impossible. The
rate tracks `(1 − browser share)`, the signature of labels reassigned from the
marginal distribution: a one-parameter model calibrated on Chrome alone predicts
held-out Safari at 2.38% against 2.27% observed, giving **~3.1% contamination**.

The mechanism behind it is left unresolved on purpose. Both candidates were
bounded instead:

```
retention observed                 17.53%
worst case under either mechanism  −3.10pp
                                   ───────
floor                              14.43%
```

Contamination cannot explain the retention signal under any of the candidate
mechanisms, and the bound survives a factor-two error in the estimate. Naming
the mechanism would not have changed a single downstream number.

### Q2 — where does conversion break?

The endpoints are sound. The interior is not.

| Defect | Effect |
|---|---|
| `begin_checkout` and `add_shipping_info` fire under 5ms apart | No measurable step between them |
| `view_item_list`: 71 events, 44 identifiers | Not instrumented |
| `add_to_cart` missing from 79.8% of cartless purchase sessions | Covers part of the real purchase path |
| 3,038 identifiers with a session but no `session_start` | Unexplained |

The funnel's largest apparent drop — `view_item → add_to_cart`, losing 80.3% —
sits precisely on the event known to be unreliable. It cannot be acted on.

What survives: **of sessions that begin checkout, 43.4% purchase**, chaining the
two steps that do not touch `add_to_cart`. Mediocre, not broken.

### Q3 — can I trust an apparently winning experiment?

A blinded synthetic treatment over real identifiers: randomise by identifier,
outcome is a purchase within 7 days, with two deliberate pathologies. The
thresholds were fixed in writing before any number was looked at.

**The experiment fails its gate.** 126,399 against 124,312 — a 0.4162pp
deviation, χ² = 17.373, p = 3.07e-05 against a pre-registered α of 0.025. Device
balance fails too, and the shape is informative: desktop and mobile move 3.75pp
in opposite directions while tablet stays at +0.06pp, which noise does not do.

The observable bias is trivial — reweighting each arm's base rates by its actual
composition gives **−0.199% relative against an MDE of 9.74%**. That does not
lift the stop, and the reason is the point: it bounds only the bias explained by
the imbalance *we can see*. The mismatch says the realised sample did not follow
the specified process without saying why, so an imbalance on an unobserved
covariate would be invisible to every check run here.

**At the reveal**, the truth was a +20% lift confined to mobile, with assignment
skewed 0.52/0.48 by device and tablet untouched.

| | true effect | expected z | observed z | power |
|---|---:|---:|---:|---:|
| mobile | +20% | 3.56 | 1.71 | **94.5%** |
| desktop | 0% | 0.00 | 0.33 | 5.0% |
| tablet | 0% | 0.00 | −1.81 | 5.0% |
| interaction | 20 vs 0 | 2.82 | 1.15 | **80.6%** |

A 94.5%-powered test missed. The interaction test missed as well, at fourteen
points less power than the effect it compares — structurally, since a difference
of differences carries both standard errors. Meanwhile tablet, whose true effect
was zero, reached p = 0.070.

Declining to claim heterogeneity at p = 0.25 was the right call **and** a false
negative. Both are true. A method does not promise the right answer; it promises
an error rate that can be stated in advance.

---

## Limitations

- **The funnel interior is unmeasurable**, so no specific checkout step can be
  recommended. This is a finding, not a gap in the analysis.
- **The contamination mechanism is unresolved.** Its impact is bounded; its cause
  is not established.
- **`geo.country` is degenerate** — forced constant per identifier by the
  obfuscation — and `browser`/`device` are contaminated at ~3.1%. Only one
  segmentation dimension survived. Device contamination also attenuates measured
  heterogeneity, making it a floor.
- **The lever model assumes independence** between levers and holds for shocks of
  this size, not for extrapolation to large changes.
- **`P(purchase | returned)` is observational.** Returners are self-selected for
  intent, so the retention figure caps the value of *induced* retention rather
  than estimating it. The marginal returner is not the average returner.
- **The synthetic experiment cannot teach mediation.** The effect is injected on
  the outcome rather than propagated through `P(view_item)`.
- **It is also cleaner than reality on identity.** Identifier instability would
  put one human in both arms of a real experiment; here the estimand is defined
  on identifiers, so the estimate is unbiased by construction.
- **A/A interval coverage ran 0.8pp below nominal** — not significant, but in the
  direction theory predicts for a Wald interval at a 1.3% base rate.

---

## What I would do next

1. **Fix the funnel instrumentation.** `add_to_cart` on every purchase path,
   `begin_checkout` and `add_shipping_info` separated into events that reflect
   real user actions. Without this, no checkout intervention can be targeted.
2. **Build the discovery intervention** — a recommendation module using
   pre-exposure signals — in parallel. It is the actionable hypothesis, and it
   is measurable cleanly today.
3. **Run a properly powered and validated A/B test on it**, with the same
   order used here: calibrate the estimator, gate on assignment, quantify what
   imbalance costs, then look at the effect.
4. **Use the repaired tracking** to decide which specific conversion
   intervention deserves the next slot.

---

## Reproducing

Requires a BigQuery sandbox project; no billing account.

```bash
uv sync --locked --all-extras

# 1. Run src/extract_sessions.sql in BigQuery, save results to Google Drive as
#    CSV, download to data/raw/ga4_sessions.csv. See data/README.md -- both
#    constraints there were found the hard way and both fail silently.
uv run python projects/01-product-analytics/src/snapshot.py \
    projects/01-product-analytics/data/raw/ga4_sessions.csv --pin

# 2. Funnel, reconciliation, nesting violations, lever sensitivity
uv run python projects/01-product-analytics/src/analysis.py

# 3. Experiment: generate, validate, then estimate -- in that order
uv run python projects/01-product-analytics/src/experiment.py
uv run python projects/01-product-analytics/src/run_validity.py
uv run python projects/01-product-analytics/src/run_effects.py

uv run pytest projects/01-product-analytics
```

The snapshot is pinned by checksum *and* validated against aggregates measured
at source. A checksum proves a file has not changed; it says nothing about
whether the file was ever right.

## Files

```
src/extract_sessions.sql   Session-grain extract from BigQuery
src/snapshot.py            Checksum pin, schema, data contract
src/analysis.py            Query runner
src/funnel.sql             Purchase funnel, session grain
src/reconciliation.sql     Funnel against overall conversion, both grains
src/nesting.sql            How far the funnel is from actually nested
src/segments.sql           First visit versus return visit
src/base_rates.sql         The six quantities the lever model rests on
src/levers.py              Incremental purchases per lever
src/experiment.py          Blinded synthetic experiment
src/validity.py            SRM, balance, A/A, compositional bias
src/effects.py             Naive, standardised and per-segment estimation
```
