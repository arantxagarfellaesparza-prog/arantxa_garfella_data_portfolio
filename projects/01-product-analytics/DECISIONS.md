# Decisions

One entry per technical choice a reviewer could reasonably question. Written
when the decision is made, not reconstructed afterwards.

---

## 001 — Unit of analysis: dual by grain, no identity reconstruction

**Date:** 2026-08-24

### Context

The dataset is `bigquery-public-data.ga4_obfuscated_sample_ecommerce`
(Google Merchandise Store, 1 Nov 2020 – 31 Jan 2021, ~4.3M events). Two facts
make the unit of analysis the first decision rather than a detail:

- Google states that "internal consistency of the dataset might be somewhat
  limited" because of obfuscation.
- `user_pseudo_id` derives from a client-side `client_id`, which browsers with
  tracking prevention reset. A returning human can therefore appear as several
  identifiers.

The choice of unit sets the denominator of retention, the grain of the funnel
and the randomisation unit of the experiment, so it constrains all three
research questions.

### Alternatives considered

- **A — `user_pseudo_id` everywhere.** The standard approach. Accepts
  over-counting of users and under-estimation of retention.
- **B — Session everywhere.** Sidesteps identity entirely, but retention is a
  cross-session behaviour by definition, so it would remove the question rather
  than answer it.
- **C — Reconstructed identity.** Stitch sessions belonging to the same human
  from device, geo and timing signals.
- **D — Dual definition by grain.** Choose the unit per question, and treat
  identity stability as an object of analysis rather than an assumption.

### Decision

**D.** Specifically:

| Question | Unit | Rationale |
|---|---|---|
| Retention | `user_pseudo_id` | Strictly a *pseudonymous identifier*, never "a person". |
| Funnel | Session, keyed `(user_pseudo_id, ga_session_id)` | The question is conversion within a visit; it does not need cross-session identity. |
| Experiment | `user_pseudo_id` | Randomisation unit, assumption documented below. |

Identity stability is investigated by sensitivity analysis across browser,
device and other signals — not assumed.

**C is explicitly rejected.** Building a `true_user_id` from geo, timing and
device on obfuscated data would be an unverifiable inference: there is no ground
truth against which the stitching could be validated, so any error it introduced
would be invisible and would propagate into every downstream result.

### Reason

The unit should follow the question. Forcing one definition across all three
would either import an identity assumption where none is needed (funnel) or
remove a question that matters (retention).

### Trade-off accepted

**The retention curve cannot be described as "people coming back".** It measures
the reappearance of pseudonymous identifiers. That is the claim this project is
allowed to make, and it is stated wherever the curve appears.

The sensitivity of that estimate to identity stability is part of the analysis,
not a caveat appended to it.

### Open questions this decision does not settle

Carried into M1/M3 rather than resolved here:

1. **Session grain still depends on identity.** `ga_session_id` is scoped to
   `user_pseudo_id`, so a mid-session identifier reset splits one session into
   two. Session grain reduces exposure to instability; it does not remove it.
   To be confirmed against the schema in M1.
2. **Cross-session purchases.** If a material share of purchases have their
   `view_item` / `add_to_cart` in an earlier session, a strictly within-session
   funnel understates conversion and would bias the business recommendation
   toward "checkout is broken". Measured in M3 before the funnel is built.
3. **Randomisation under unstable identifiers.** In a real experiment, one human
   across two identifiers lands in both arms and attenuates the effect toward
   zero. In this simulation the effect is injected *at identifier level*, so the
   estimand is the effect on identifiers and the estimate is unbiased. The
   simulation is therefore cleaner than reality on this axis — a limitation of
   the design, not evidence that the method is sound. Goes in the README
   limitations.

---

## 002 — The browser/ITP explanation for identifier instability is rejected

**Date:** 2026-08-24

### Context

Decision 001 left identity stability as an object of analysis. The working
hypothesis was that `user_pseudo_id` churn — driven by browsers with tracking
prevention resetting `client_id` — distorts the retention curve, and that the
distortion should therefore be visible as a browser-level difference.

Baseline established first: **82.47% of identifiers have exactly one session**,
and only 17.53% reappear in a second. That is the number the cohort curve must
reconcile against.

### What was tested

Share of single-session identifiers, split by browser, over all 270,154
identifiers.

| Browser | users | single-session % |
|---|---:|---:|
| Chrome | 183,734 | 82.47 |
| Safari | 64,857 | 82.37 |
| Edge | 5,997 | 82.64 |
| Firefox | 5,064 | 83.08 |
| Android Webview | 3,513 | 83.15 |
| `<Other>` | 6,989 | 82.24 |

Safari − Chrome = **−0.10pp** (SE 0.17pp, z ≈ 0.6, p ≈ 0.57). The whole range
across six browsers spans 0.91pp.

### Decision

**The browser/ITP mechanism is rejected as the explanation for the
single-session rate**, and browser is dropped as a candidate segmentation
dimension for the identity question.

### Reason

This is a *well-powered* null, not an absent result. At n = 183,734 and 64,857
the minimum detectable difference at 80% power is ≈ 0.5pp; real identifier churn
from tracking prevention would produce tens of percentage points. The capacity to
detect a small effect existed and no effect is there — so absence of evidence is,
here, evidence of absence.

The observed difference is also in the opposite direction to the hypothesis,
which removes any reading of "a real effect that is merely small".

### Trade-off accepted

Browser labels are themselves contaminated (see below), which attenuates any
real browser effect toward zero. A contamination rate of ~3% cannot turn an
effect of tens of percentage points into −0.10pp, so the rejection stands — but
the caveat is stated wherever the result appears rather than dropped.

### Measured contamination of the device dimension

Between 1.00% and 2.92% of identifiers appear under more than one browser, which
is not possible behaviour: `client_id` lives in a first-party cookie that one
browser cannot read from another.

The rate is lowest for Chrome and roughly equal for every other browser, which is
the signature of labels reassigned at random from the marginal distribution: a
reassignment is invisible when it lands on the browser the identifier already
had. A one-parameter model, `pct_multi_browser(b) ≈ r × (1 − share(b))`,
calibrated on Chrome alone gives **r ≈ 3.1%** and predicts Safari — the largest
held-out group — at 2.38% against 2.27% observed.

Small browsers run ~0.4pp below prediction, plausibly because fewer events mean
fewer opportunities to catch a reassignment. Recorded as an unexplained residual
rather than smoothed over.

This turns Google's general warning about limited internal consistency into a
measured figure for this dataset.

### Open — decides whether Q1 survives

The multi-browser evidence does **not** identify *what* was contaminated, and the
two candidates have opposite consequences:

- **(a) The browser field was randomised on some events**, identifiers intact →
  retention is real, only device segmentation is unreliable.
- **(b) Events were reassigned between identifiers**, browser intact → the
  retention curve is an artefact and the research question changes.

Discriminant: under (a) the rest of the `device` block stays stable for an
identifier while browser varies; under (b) operating system and device category
scramble alongside it, because whole events moved. Tested next, before any
cohort work is built on top of the identifier.

---

## 003 — The contamination mechanism stays unresolved; the impact is bounded instead

**Date:** 2026-08-24

### Context

Decision 002 measured device-block contamination at ~3.1% of identifiers and
left two candidate mechanisms open, with opposite consequences for the retention
curve:

- **(b)** Whole events reassigned between identifiers → retention partly an
  artefact.
- **(c')** The `device` block swapped for another coherent profile, identifiers
  intact → retention unaffected.

Two observations narrowed the field. Individual events are internally
consistent — Safari appears on iOS, Macintosh and unresolved `Web`, never on
Android, and on Windows for exactly one identifier. But identifiers are not:
among the 3,890 with more than one browser, 67.69% also carry more than one
operating system against a background rate of 0.88%, a factor of 77.

Together these rule out a *field-level* randomisation of `browser` alone. What
moved were coherent blocks.

### The discriminant that failed

`geo.country` was chosen to separate (b) from (c'): under (b) the country travels
with the event, under (c') it stays put.

| group | users | multi-country % |
|---|---:|---:|
| single browser | 266,264 | 0.00 |
| multi-browser | 3,890 | 0.00 |

**Zero in both rows**, against non-zero background rates for OS (0.88%) and
device category (0.62%). Real traffic over 92 days produces some multi-country
identifiers through travel, VPNs, corporate proxies and mobile IP geolocation;
exactly zero across 270,154 identifiers does not occur naturally.

The reading is that `geo.country` was itself normalised to one value per
identifier during obfuscation. A field forced constant returns the same 0% under
either hypothesis, so it carries no discriminating power. **The test is
inconclusive, and the 0% cannot be used as evidence that identifiers are
intact.**

### Decision

**The mechanism is left unresolved and recorded as such.** No further budget is
spent identifying it, because the decision it feeds does not depend on it.

Instead the *impact* is bounded, which holds under both hypotheses:

```
retention observed (2+ sessions)        17.53%
worst case under (b), all spurious      -3.10pp
                                        ───────
floor                                    14.43%
```

Under (c') the effect is zero by construction: a swapped device block does not
create a session. Under (b) the worst case assumes every contaminated identifier
owes its second session to a foreign event, which is deliberately pessimistic.

The bound survives a factor-two error in the contamination estimate: at r = 6.2%
the floor is still 11.3pp.

### Reason

Identifying the mechanism would change nothing about what this project can
claim. The question that matters — *can identifier instability explain the
retention signal?* — is answered by the magnitude, and the magnitude is
answerable without the mechanism.

### Trade-off accepted

The project cannot state why the device block is contaminated, only that it is
and by roughly how much. Any later work that depends on the mechanism rather
than the magnitude must reopen this.

### Dimensions burned for segmentation

Two candidate segmentation dimensions are lost, for different reasons, and both
are recorded before segments are chosen rather than after:

| Dimension | Status | Why |
|---|---|---|
| Browser / device | **Contaminated**, ~3.1% | Reassigned per event |
| `geo.country` | **Degenerate** | Forced constant per identifier |

`geo` is the more dangerous of the two: it does not fail loudly. Cohorts split by
country will come out clean, deterministic and entirely artefactual.

Remaining candidate, and the one closest to the business question: **new versus
returning**, derived from session counts, which device contamination does not
touch. A third would come from `traffic_source`, subject to auditing its
`<Other>` rate first.

---

## 004 — `add_to_cart` is not a reliable funnel step; report two reconciled funnels

**Date:** 2026-08-24

### Context

Decision 001 left open whether a within-session funnel understates conversion
because purchases are prepared across sessions. Measured before building the
funnel, as that entry required.

Of 4,848 purchase sessions, 96.91% contain a `view_item` but only **58.75%
contain an `add_to_cart`** — roughly 2,000 sessions purchasing with nothing added
to a cart, which is not possible as behaviour.

Splitting those 2,000:

| | sessions | share |
|---|---:|---:|
| Cart in an earlier session (cross-session) | 252 | 12.6% |
| Cart only *after* the purchase | 153 | 7.7% |
| **Never added to cart at all, in 92 days** | **1,595** | **79.8%** |

### What this does and does not invalidate

**The session grain survives.** The dominant explanation is not cross-session
preparation — that accounts for 12.6% — it is that `add_to_cart` does not fire on
a large share of purchase paths. That defect is grain-independent: at identifier
grain there would still be ~1,600 buyers who never cart. Decision 001 was
stress-tested by a check designed to invalidate it, and held.

What failed was an undeclared assumption: that `add_to_cart` is a reliable step.

A second timing check settles the adjacent question. Across 11,104 sessions
containing both, the gap from `begin_checkout` to `add_shipping_info` has a
median under 5ms and p90 of 4.92s. No human completes a shipping form in five
seconds, so the two fire programmatically. They are **one step**, and the reason
matters: not that there is no friction between them, but that no user action
occurs there, so friction is **unmeasurable**. It is a blind spot, not a clean
pass.

### Decision

Report **two reconciled funnels**:

1. **Instrumented path**, session grain:
   `view_item → add_to_cart → begin_checkout → add_payment_info → purchase`,
   with `begin_checkout` and `add_shipping_info` collapsed into one step.
2. **Overall conversion**, against the 1.64% identifier-level baseline.

The gap between them is reported and explained rather than hidden. `add_to_cart`
is kept but explicitly marked non-exhaustive: no `add_to_cart → purchase` rate is
computed as though every purchase passed through it.

### Reason

Dropping `add_to_cart` would discard the step where most e-commerce funnels lose
people. Keeping it silently would produce a number that is wrong for ~40% of
conversions. Reconciling against a baseline that already exists is precisely the
job a baseline is for, and it costs about an hour.

### Trade-off accepted

The report carries two numbers where a reader would prefer one, and the
difference has to be explained every time it is shown.

### Instrumentation defects, accumulated

| # | Defect | Effect |
|---|---|---|
| 1 | `begin_checkout` / `add_shipping_info` fire together (<5ms) | Blind spot; no measurable step between them |
| 2 | `view_item_list`: 71 events, 44 identifiers | Not instrumented; excluded |
| 3 | `add_to_cart` absent from ~80% of cartless purchase sessions | Covers only part of the real purchase path |
| 4 | 3,038 identifiers with a session but no `session_start` | Open |

Consequence for the business question: the funnel **endpoints** are sound —
61,252 identifiers view an item, 4,419 purchase, 17.53% return — but its
**interior** is not measurable. The project is therefore on track to answer
*whether* the loss sits in the funnel or in retention, while being unable to say
*which step* to fix. That is a narrower and more useful answer than "the data
cannot tell", and it is not yet settled: it holds only if the funnel endpoints
survive the reconciliation in 1.

---

## 005 — Compare the levers on incremental purchases, and drop segmentation to one dimension

**Date:** 2026-08-25

### Context

The funnel answered less than hoped and more than expected. Three candidate
levers came out of it, each with a different denominator and therefore not
comparable as stated:

| | |
|---|---|
| 78.61% of sessions never view a product | |
| 93.71% of sessions that view a product do not buy | |
| 82.47% of identifiers never return | |

Read as raw leak rates, retention looks like the largest problem in the
business. That reading is what this entry exists to test.

### Scope change

Added: a lever comparison on incremental purchases (~2h), which was not in the
original plan. Removed to pay for it: segmentation drops from two or three
pre-registered dimensions to **one — new versus returning**, derived from
session counts and untouched by the device contamination in DECISIONS 002.

Without the comparison the project ends at "the levers cannot be compared",
which is not a usable answer for someone with one slot in a quarter.

### Decision

Convert all three to the unit the business counts, using the identity

```
purchases = sessions x P(view) x P(buy | view)
```

which reproduces the observed 4,848 purchase sessions exactly. Retention is
modelled separately because it changes the number of sessions rather than a
conditional rate.

Report **two shocks**, not one:

| lever | base | +1pp | +10% relative | uplift |
|---|---:|---:|---:|---:|
| discovery | 21.39% | 227 | **485** | 10.0% |
| conversion | 6.29% | 770 | **485** | 10.0% |
| retention | 17.53% | 141 | 246 *(upper bound)* | 5.1% |

### Findings

**Discovery and conversion are exactly equivalent under a relative shock**, and
necessarily so: they are multiplicative factors of the same product, so scaling
either by 1.10 scales purchases by 1.10. Arithmetic cannot rank them. Only
feasibility can, and feasibility is not in this data.

**The +1pp column ranks conversion 3.4x above discovery, and that ordering is an
artefact of the base rates** — one point on 6.29% is a 15.9% improvement, one
point on 21.39% is 4.7%. Neither shock is universally right: the correct one
depends on how the expected effect of an intervention is expressed. Absent any
historical effect sizes, the relative shock leads and the absolute is reported
as sensitivity.

**Retention is the smallest of the three, at roughly half the others**, and its
figure is a ceiling rather than an estimate. The raw 82.47% invited the opposite
conclusion; the difference is between reading leak rates and reading marginal
impact on the outcome.

**The original question offered the wrong choice.** It asked checkout or repeat
purchase. `conversion` is approximately "fix checkout"; `discovery` — getting
visitors to a product page at all — ties with it and was not on the list.

### Trade-off accepted

Segmentation is now a single dimension, so this project cannot say whether any
lever behaves differently across device, channel or country. Two of those three
were already unusable (DECISIONS 003); the loss is real only for channel.

The lever model is deliberately simple: it assumes the levers are independent
and that improving one does not change the others. Over a shock of this size
that is reasonable; it would not survive being extrapolated to a large change.

### What the analysis will not claim

- Which step inside the funnel to fix. The interior is not measurable
  (DECISIONS 004), and the one defensible interior figure — 43.4% of sessions
  that begin checkout go on to purchase — says only that checkout completion is
  mediocre rather than broken.
- Which of discovery and conversion to choose. Supplying the derivative is the
  analysis; supplying the achievability is the roadmap owner's.

---

## 006 — Validity verdict: hard stop on causal interpretation

**Date:** 2026-09-04

### Pre-registered protocol

Fixed before any number from the experiment was looked at, and recorded in the
docstring of `src/validity.py`:

| Check | Role | Threshold |
|---|---|---|
| SRM, chi-square against 50/50 | **Hard gate** | α = 0.025 |
| Balance on `device_category`, chi-square + effect size | Diagnostic, not a gate | α = 0.025 |
| A/A by re-randomisation with zero effect, repeated | Calibration of the estimator | rejection ≈ α, coverage ≈ 1−α |

Order: A/A → SRM → balance → written verdict → **only then** effect.

α = 0.025 rather than 0.05, accepting slightly less power to detect small
invalidity in exchange for a lower chance of discarding a healthy experiment. At
this sample size the choice moves the detection threshold from 0.280pp to
0.308pp, so it is close to inconsequential either way.

**No multiplicity correction**, deliberately. The checks are hierarchical and do
different jobs: SRM is the gate, balance is diagnostic, and the A/A is one
calibration check evaluated on the distribution of 1,000 replications rather
than as 1,000 competing hypotheses.

### Results

**A/A — pass.** Over 1,000 replications: rejection rate 0.0580 against a nominal
0.05, interval coverage 0.9420 against 0.95, mean difference +0.000000, median
p-value 0.5218. The rejection rate sits 1.2 standard errors from nominal, which
is noise. Coverage runs 0.8pp low, not significantly, but in the direction theory
predicts for a Wald interval at a base rate near 1.3% — noted as a limitation
rather than a failure.

**SRM — fail.** 126,399 treatment against 124,312 control, a share of 50.4162%
and a deviation of +0.4162pp. χ² = 17.373, p = 3.07e-05, against a threshold of
0.025.

**Balance — fail.** χ² = 381.016, p = 1.83e-83, Cramér's V = 0.039. Desktop is
over-represented in treatment by 3.75pp, mobile under-represented by 3.80pp, and
**tablet is untouched at +0.06pp**. Noise does not produce that shape: two
categories moving four points in opposite directions while the third stays put
points to a systematic or selective mechanism, though its cause is not
identified here.

### Quantifying the imbalance

Reweighting each arm's known base rates by that arm's actual composition, with no
treatment effect assumed:

```
compositional bias   -0.199% relative
experiment MDE       +9.74%  relative
```

The direction is against treatment — treatment carries more desktop, whose base
rate (1.316%) is below mobile's (1.383%). The magnitude is a fiftieth of the
smallest effect this experiment could detect.

### Decision

**Hard stop on causal interpretation.** The effect may be computed for
diagnosis; it is not read causally and does not inform a product decision.

### Reason

The −0.199% quantifies only the bias explained by the *observed* imbalance in
`device_category`. It does not bound the total bias produced by whatever
mechanism caused the SRM.

The SRM says the realised sample does not follow the 50/50 process the design
specified. It does not say why. Until the cause is identified and shown to be
ignorable with respect to the outcome, the fact that the measurable component is
trivial licenses nothing about the rest: an imbalance on an unobserved covariate
correlated with purchase would be invisible to every check run here.

That is the whole reason a sample ratio mismatch is treated as a canary rather
than as a bias to be corrected. If the footprint of the fault were knowable, it
could simply be adjusted for. It is not, so it cannot.

Balance failing as well does not change the verdict — under the pre-registered
rule it is diagnostic — but it does sharpen the diagnosis: the fault
discriminates between desktop and mobile and leaves tablet alone.

### Trade-off accepted

An experiment that may well carry a real effect is set aside on the strength of a
0.42pp deviation. That is the intended cost of the rule: a threshold that bends
when the effect looks promising is not a threshold.

---

## 007 — Reveal: what the experiment was, and what it found

**Date:** 2026-09-04

Generative parameters, hidden until this point and now committed at
[`src/experiment-params.json`](src/experiment-params.json):

```
assign_prob:  desktop 0.52   mobile 0.48   tablet 0.50
lift:         desktop  0%    mobile +20%   tablet   0%
```

Estimates were made and written down before this file was opened.

### Scoring the blind analysis

| Claim made blind | Truth |
|---|---|
| SRM present | Correct — assignment was skewed by design |
| Imbalance is systematic, not noise, because tablet did not move | Correct — tablet's assignment probability was exactly 0.50 |
| Heterogeneity, stronger on mobile | Correct in direction |
| Heterogeneity **not established** (interaction p = 0.25) | Methodologically correct, factually a miss: the effect was real |
| Tablet's −36.98% is unstable, not a finding | Correct — its true effect was exactly zero |
| Overall effect not significant | Correct |
| Naive lift ≈ +8% | The true population-weighted lift is **+8.2%**; the experiment measured +3.26% |

### Realised power against the true effect

| | true effect | expected z | observed z | power |
|---|---:|---:|---:|---:|
| desktop | 0% | 0.00 | 0.33 | 5.0% |
| mobile | +20% | 3.56 | 1.71 | **94.5%** |
| tablet | 0% | 0.00 | −1.81 | 5.0% |
| interaction | 20 vs 0 | 2.82 | 1.15 | **80.6%** |

### What this establishes

**A 94.5%-powered test missed.** The mobile effect was real, large and
well-powered, and the realised draw landed 1.85 standard errors below its
expectation — roughly a one-in-thirty outcome. Power is a probability, not a
promise, and this is what the unlucky tail looks like from the inside.

**The interaction test is structurally weaker than the effects it compares.** At
80.6% it had fourteen points less power than the mobile main effect, because a
difference of differences carries both standard errors. That is why claims of
heterogeneity fail in both directions so often: real heterogeneity goes
undetected, and subgroup noise gets promoted.

**The false signal nearly fired while the real one did not.** Tablet, whose true
effect was zero, reached p = 0.070 on 2,871 treated identifiers; mobile, with a
+20% effect, reached only p = 0.088. Across three subgroups, the chance of at
least one reaching p < 0.10 under a complete null is 27%.

**Correct method produced the wrong answer, and was still correct.** Declining to
claim heterogeneity at p = 0.25 was the right call and it was, this time, a false
negative. Claiming it from a subgroup p of 0.088 would have been right here and
wrong more often than not. A method does not promise the right answer; it
promises an error rate that can be stated in advance.

### What the project can therefore say about Q3

It can say that an apparently winning experiment is not trustworthy on the
strength of its estimate, and give the order of operations that establishes
this: calibrate the estimator, gate on assignment, quantify what imbalance costs,
and only then look at the effect.

It cannot say that this particular treatment works. The experiment failed its
gate, and even setting that aside, it was one unlucky draw away from the
opposite conclusion.
