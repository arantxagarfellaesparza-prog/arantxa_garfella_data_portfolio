"""Estimate the effect. Diagnostic only -- see DECISIONS 006.

The experiment failed its pre-registered SRM gate, so nothing printed here is a
causal claim. It is run to understand what the experiment would have said, and
to compare against the generative truth at the reveal.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from effects import (
    effect_by_segment,
    interaction_test,
    naive_effect,
    standardised_effect,
)

EXPERIMENT = Path(__file__).parents[1] / "data" / "interim" / "experiment.csv"


def _show(title: str, result: dict[str, float]) -> None:
    print(f"\n{title}")
    print(
        f"  rate  T {result.get('rate_treatment', float('nan')):.5f}"
        f"   C {result.get('rate_control', float('nan')):.5f}"
    )
    print(f"  diff  {100 * result['absolute_diff']:+.4f} pp")
    print(f"  lift  {100 * result['relative_lift']:+.2f} %")
    print(
        f"  95%CI [{100 * result['ci_low']:+.4f}, {100 * result['ci_high']:+.4f}] pp"
        f"   p = {result['p_value']:.4f}"
    )


def main() -> int:
    frame = pd.read_csv(EXPERIMENT)
    print("DIAGNOSTIC ONLY -- the SRM gate failed (DECISIONS 006).")
    print("=" * 72)

    _show("Naive (arms as they came out)", naive_effect(frame))
    _show(
        "Standardised to population composition",
        standardised_effect(frame, "device_category"),
    )

    print("\nBy segment")
    per_segment = effect_by_segment(frame, "device_category")
    show = per_segment[
        [
            "device_category",
            "weight",
            "n_treatment",
            "rate_treatment",
            "rate_control",
            "relative_lift",
            "p_value",
        ]
    ].copy()
    show["weight"] = (100 * show["weight"]).round(1)
    show["relative_lift"] = (100 * show["relative_lift"]).round(2)
    show["rate_treatment"] = show["rate_treatment"].round(5)
    show["rate_control"] = show["rate_control"].round(5)
    show["p_value"] = show["p_value"].round(4)
    print(show.to_string(index=False))

    print("\nInteraction: does mobile respond differently from desktop?")
    for key, value in interaction_test(
        frame, "device_category", "mobile", "desktop"
    ).items():
        print(f"  {key:<22} {value:+.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
