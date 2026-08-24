# Decisions

One entry per technical choice that a reviewer could reasonably question.

Written **when the decision is made**, not afterwards — the value is in
recording the reasoning, and reasoning reconstructed after seeing the result is
just justification.

Newest last.

---

## <Decision title>

**Date:** YYYY-MM-DD

**Alternatives considered**
- Option A —
- Option B —
- Option C —

**Decision**


**Reason**


**Trade-off accepted**
What this costs me, and under what circumstances I would revisit it.

---

<!--
Worked example of the level of detail expected:

## Why PR-AUC is the primary metric

**Date:** 2026-09-01

**Alternatives considered**
- Accuracy — useless here: predicting "no default" for everyone scores 97%.
- ROC-AUC — reported, but the false-positive rate is computed against a huge
  negative class, so large changes in absolute false positives barely move it.
- PR-AUC — summarises precision against recall on the positive class only.

**Decision**
PR-AUC as the primary metric; ROC-AUC and Brier reported alongside.

**Reason**
Defaults are ~3% of the sample. The decision this model supports is about the
minority class, so the metric should be too.

**Trade-off accepted**
PR-AUC is sensitive to class balance, so it is not comparable across datasets
with different default rates. Fine within this project, and a trap if a number
from here is ever quoted next to a published benchmark.
-->
