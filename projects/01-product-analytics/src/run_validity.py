"""Run the pre-registered validity phase, in the pre-registered order.

Stops before estimating the treatment effect. That boundary is enforced here
rather than left to discipline: the script cannot show a lift, so the validity
verdict has to be written without one on screen.

Order fixed on 2026-09-04:
    A/A calibration  ->  SRM  ->  balance  ->  written verdict  ->  (only then) effect
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from validity import ALPHA_SRM, aa_simulation, balance, srm

EXPERIMENT = Path(__file__).parents[1] / "data" / "interim" / "experiment.csv"
AA_REPS = 1_000
AA_ALPHA = 0.05


def main() -> int:
    frame = pd.read_csv(EXPERIMENT)
    print(f"{len(frame):,} identifiers\n")

    print("=" * 72)
    print("1. A/A calibration -- does the estimator behave under a true null?")
    print("=" * 72)
    aa = aa_simulation(
        frame["outcome"].to_numpy(), n_reps=AA_REPS, seed=1234, alpha=AA_ALPHA
    )
    rejection = aa["rejected"].mean()
    coverage = aa["covers_zero"].mean()
    print(f"  replications                 {AA_REPS:,}")
    print(f"  rejection rate               {rejection:.4f}  (nominal {AA_ALPHA})")
    print(f"  interval coverage of zero    {coverage:.4f}  (nominal {1 - AA_ALPHA})")
    print(
        f"  mean absolute difference     {aa['absolute_diff'].mean():+.6f}  (nominal 0)"
    )
    print(f"  median p-value               {aa['p_value'].median():.4f}  (nominal 0.5)")

    print("\n" + "=" * 72)
    print(f"2. SRM -- hard gate, alpha = {ALPHA_SRM}")
    print("=" * 72)
    srm_result = srm(frame["arm"])
    print(srm_result)

    print("\n" + "=" * 72)
    print("3. Balance -- diagnostic, not a gate")
    print("=" * 72)
    print(balance(frame, "device_category"))

    print("\n" + "=" * 72)
    print("Effect estimation is deliberately not run here. Write the validity")
    print("verdict first; the effect comes from a separate step.")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
