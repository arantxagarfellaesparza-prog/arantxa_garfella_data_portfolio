"""Validity checks, run and judged before the effect is estimated.

The order is the whole point. Once a lift is on screen it becomes very hard to
read a sample ratio mismatch as anything other than an inconvenience, so the
thresholds are fixed in advance and these run first.

Pre-registered protocol (2026-08-26):

  * SRM     -- chi-square goodness-of-fit against 50/50, alpha = 0.025.
  * Balance -- chi-square test of independence on device_category, with an
               effect size, used as a randomisation sanity check and not as a
               business segmentation.
  * A/A     -- re-randomisation with zero effect, repeated, to check that the
               estimator's false positive rate and interval coverage are what
               they claim. This validates the analysis code rather than the
               experiment.

  Stopping rule: if SRM fails its threshold, the causal reading stops. The effect
  may still be computed for diagnosis, but is not interpreted causally and does
  not inform a product decision.

No effect-size floor is applied to the SRM test, deliberately. At n = 250,711 a
detection means a real deviation of around 0.3pp or more, and a mechanism that
deviates systematically is a bug in assignment regardless of how small the
deviation looks. The danger of SRM is what it reveals about the pipeline, not
the imbalance itself.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats

ALPHA_SRM = 0.025
ALPHA_BALANCE = 0.025


@dataclass
class CheckResult:
    name: str
    statistic: float
    p_value: float
    alpha: float
    detail: dict[str, float] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.p_value >= self.alpha

    def __str__(self) -> str:
        verdict = "PASS" if self.passed else "FAIL"
        line = (
            f"{self.name:<22} chi2={self.statistic:9.3f}  "
            f"p={self.p_value:.3e}  [{verdict}]"
        )
        extras = "".join(f"\n  {k:<28} {v:,.4f}" for k, v in self.detail.items())
        return line + extras


def srm(arms: pd.Series, *, alpha: float = ALPHA_SRM) -> CheckResult:
    """Is the split what the design asked for?

    Goodness-of-fit against an even split. Rejecting means the assignment
    mechanism is not the fair coin it was supposed to be.
    """
    counts = arms.value_counts().sort_index()
    n = int(counts.sum())
    statistic, p = stats.chisquare(counts.to_numpy())

    treated = int(counts.get("treatment", 0))
    return CheckResult(
        name="SRM (50/50)",
        statistic=float(statistic),
        p_value=float(p),
        alpha=alpha,
        detail={
            "treatment": treated,
            "control": n - treated,
            "treatment share %": 100 * treated / n,
            "deviation from 50% (pp)": 100 * (treated / n - 0.5),
        },
    )


def balance(
    frame: pd.DataFrame,
    covariate: str,
    *,
    arm_column: str = "arm",
    alpha: float = ALPHA_BALANCE,
) -> CheckResult:
    """Do the arms have the same composition on a pre-treatment covariate?

    Cramer's V accompanies the p-value because a chi-square on 250k rows answers
    "is there any dependence at all", which is not the same question as "is the
    dependence large enough to distort anything".
    """
    table = pd.crosstab(frame[arm_column], frame[covariate])
    statistic, p, dof, _ = stats.chi2_contingency(table)

    n = table.to_numpy().sum()
    cramers_v = float(np.sqrt(statistic / (n * (min(table.shape) - 1))))

    shares = 100 * table.div(table.sum(axis=1), axis=0)
    detail = {"Cramers V": cramers_v, "dof": float(dof)}
    for level in table.columns:
        gap = shares.loc["treatment", level] - shares.loc["control", level]
        detail[f"{level}: treat - control (pp)"] = gap

    return CheckResult(
        name=f"Balance ({covariate})",
        statistic=float(statistic),
        p_value=float(p),
        alpha=alpha,
        detail=detail,
    )


def two_proportion_test(
    outcome: np.ndarray, treated: np.ndarray, *, alpha: float = 0.05
) -> dict[str, float]:
    """Difference in conversion between arms, with a Wald interval.

    Kept separate from the checks above so the same estimator can be exercised by
    the A/A simulation -- an estimator validated on real data only is validated
    on exactly one draw.
    """
    y_t, y_c = outcome[treated], outcome[~treated]
    n_t, n_c = len(y_t), len(y_c)
    p_t, p_c = y_t.mean(), y_c.mean()

    diff = p_t - p_c
    se = np.sqrt(p_t * (1 - p_t) / n_t + p_c * (1 - p_c) / n_c)
    z = diff / se
    p_value = 2 * (1 - stats.norm.cdf(abs(z)))
    half = stats.norm.ppf(1 - alpha / 2) * se

    return {
        "n_treatment": n_t,
        "n_control": n_c,
        "rate_treatment": p_t,
        "rate_control": p_c,
        "absolute_diff": diff,
        "relative_lift": diff / p_c if p_c else np.nan,
        "se": se,
        "z": z,
        "p_value": p_value,
        "ci_low": diff - half,
        "ci_high": diff + half,
    }


def aa_simulation(
    outcome: np.ndarray,
    *,
    n_reps: int = 500,
    seed: int = 0,
    alpha: float = 0.05,
    treatment_share: float = 0.5,
) -> pd.DataFrame:
    """Re-randomise with no effect injected, repeatedly.

    Under a true null the p-values must be uniform, the rejection rate must land
    near alpha and the intervals must cover zero (1 - alpha) of the time. If they
    do not, the estimator is wrong and every number it produces on the real
    experiment is wrong with it.
    """
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(n_reps):
        treated = rng.random(len(outcome)) < treatment_share
        result = two_proportion_test(outcome, treated, alpha=alpha)
        rows.append(
            {
                "p_value": result["p_value"],
                "rejected": result["p_value"] < alpha,
                "covers_zero": result["ci_low"] <= 0 <= result["ci_high"],
                "absolute_diff": result["absolute_diff"],
            }
        )
    return pd.DataFrame(rows)
