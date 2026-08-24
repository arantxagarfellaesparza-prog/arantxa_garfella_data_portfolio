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
