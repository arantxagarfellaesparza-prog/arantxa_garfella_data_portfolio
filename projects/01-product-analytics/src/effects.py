"""Effect estimation. Diagnostic only under the DECISIONS 006 stop.

Three estimates, answering three different questions:

  * **Naive** -- the difference between arms as they came out. Carries the
    compositional bias the balance check measured.
  * **Standardised** -- each segment's effect reweighted to the population's
    composition, which removes the bias from the imbalance we can see. It cannot
    remove bias from an imbalance we cannot see, which is why it does not lift
    the stop.
  * **Per segment** -- whether the effect is the same everywhere, plus a test of
    the difference between segments rather than eyeballing two intervals.

Comparing two confidence intervals for overlap is not a test of whether they
differ. Two effects can have overlapping intervals and still differ
significantly, so the interaction is tested directly.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from validity import two_proportion_test


def _arm_mask(frame: pd.DataFrame, arm_column: str = "arm") -> np.ndarray:
    return (frame[arm_column] == "treatment").to_numpy()


def naive_effect(
    frame: pd.DataFrame,
    *,
    outcome: str = "outcome",
    arm_column: str = "arm",
    alpha: float = 0.05,
) -> dict[str, float]:
    """The headline difference, imbalance and all."""
    return two_proportion_test(
        frame[outcome].to_numpy(), _arm_mask(frame, arm_column), alpha=alpha
    )


def effect_by_segment(
    frame: pd.DataFrame,
    segment: str,
    *,
    outcome: str = "outcome",
    arm_column: str = "arm",
    alpha: float = 0.05,
) -> pd.DataFrame:
    """One estimate per level of `segment`, with that level's share of the whole."""
    rows = []
    for level, block in frame.groupby(segment):
        result = two_proportion_test(
            block[outcome].to_numpy(), _arm_mask(block, arm_column), alpha=alpha
        )
        rows.append({segment: level, "weight": len(block) / len(frame), **result})
    return pd.DataFrame(rows).sort_values("weight", ascending=False)


def standardised_effect(
    frame: pd.DataFrame,
    segment: str,
    *,
    outcome: str = "outcome",
    arm_column: str = "arm",
    alpha: float = 0.05,
) -> dict[str, float]:
    """Direct standardisation: per-segment effects reweighted to the population.

    Each segment's difference is estimated inside that segment, where assignment
    was not imbalanced, and the segment effects are then combined using the
    population's composition rather than either arm's.
    """
    per_segment = effect_by_segment(
        frame, segment, outcome=outcome, arm_column=arm_column, alpha=alpha
    )

    weights = per_segment["weight"].to_numpy()
    diffs = per_segment["absolute_diff"].to_numpy()
    ses = per_segment["se"].to_numpy()

    diff = float((weights * diffs).sum())
    # Segments are disjoint, so their estimates are independent and variances add
    # under the squared weights.
    se = float(np.sqrt((weights**2 * ses**2).sum()))
    z = diff / se
    half = stats.norm.ppf(1 - alpha / 2) * se

    # Weighted to the population rather than to either arm, so these two are
    # comparable with each other and with the naive pair.
    control_rate = float((per_segment["weight"] * per_segment["rate_control"]).sum())
    treatment_rate = float(
        (per_segment["weight"] * per_segment["rate_treatment"]).sum()
    )
    return {
        "rate_treatment": treatment_rate,
        "rate_control": control_rate,
        "absolute_diff": diff,
        "relative_lift": diff / control_rate if control_rate else np.nan,
        "se": se,
        "z": z,
        "p_value": float(2 * (1 - stats.norm.cdf(abs(z)))),
        "ci_low": diff - half,
        "ci_high": diff + half,
    }


def interaction_test(
    frame: pd.DataFrame,
    segment: str,
    level_a: str,
    level_b: str,
    *,
    outcome: str = "outcome",
    arm_column: str = "arm",
) -> dict[str, float]:
    """Do two segments respond differently? A difference of differences.

    This is the test heterogeneity claims need. Finding an effect in one segment
    and not another is not evidence that they differ -- that comparison has its
    own standard error, and it is larger than either effect's.
    """
    per_segment = effect_by_segment(
        frame, segment, outcome=outcome, arm_column=arm_column
    ).set_index(segment)

    a, b = per_segment.loc[level_a], per_segment.loc[level_b]
    diff = float(a["absolute_diff"] - b["absolute_diff"])
    se = float(np.sqrt(a["se"] ** 2 + b["se"] ** 2))
    z = diff / se

    return {
        f"effect_{level_a}": float(a["absolute_diff"]),
        f"effect_{level_b}": float(b["absolute_diff"]),
        "difference": diff,
        "se": se,
        "z": z,
        "p_value": float(2 * (1 - stats.norm.cdf(abs(z)))),
    }
