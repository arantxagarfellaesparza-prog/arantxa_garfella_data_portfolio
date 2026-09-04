"""Deterministic fixtures with no sampling noise, so the expected numbers are
exact rather than approximate."""

import pandas as pd
import pytest
from effects import (
    effect_by_segment,
    interaction_test,
    naive_effect,
    standardised_effect,
)


def block(
    segment: str, arm: str, n: int, converts: int, scale: int = 1
) -> pd.DataFrame:
    """`n` identifiers in one arm of one segment, `converts` of whom convert."""
    return pd.DataFrame(
        {
            "device_category": segment,
            "arm": arm,
            "outcome": [True] * (converts * scale) + [False] * ((n - converts) * scale),
        }
    )


def imbalanced(scale: int = 1) -> pd.DataFrame:
    """Arms imbalanced across segments, with a known effect in one of them.

    segment A: treatment 20%, control 10%  ->  +10pp, but only 25% of A is treated
    segment B: treatment 10%, control 10%  ->    0pp, and 75% of B is treated

    Population weights are 50/50, so the standardised effect is +5pp while the
    naive difference is dragged to +2.5pp by the composition.
    """
    return pd.concat(
        [
            block("A", "treatment", 500, 100, scale),
            block("A", "control", 1500, 150, scale),
            block("B", "treatment", 1500, 150, scale),
            block("B", "control", 500, 50, scale),
        ],
        ignore_index=True,
    )


def test_naive_effect_carries_the_compositional_drag() -> None:
    got = naive_effect(imbalanced())
    assert got["rate_treatment"] == pytest.approx(0.125)
    assert got["rate_control"] == pytest.approx(0.10)
    assert got["absolute_diff"] == pytest.approx(0.025)


def test_standardisation_recovers_the_population_effect() -> None:
    got = standardised_effect(imbalanced(), "device_category")
    # 0.5 * 10pp + 0.5 * 0pp
    assert got["absolute_diff"] == pytest.approx(0.05)


def test_standardised_and_naive_disagree_when_the_arms_are_imbalanced() -> None:
    frame = imbalanced()
    assert (
        standardised_effect(frame, "device_category")["absolute_diff"]
        > (naive_effect(frame)["absolute_diff"])
    )


def test_effect_by_segment_isolates_each_segment() -> None:
    got = effect_by_segment(imbalanced(), "device_category").set_index(
        "device_category"
    )
    assert got.loc["A", "absolute_diff"] == pytest.approx(0.10)
    assert got.loc["B", "absolute_diff"] == pytest.approx(0.0)
    assert got.loc["A", "weight"] == pytest.approx(0.5)


def test_interaction_detects_a_real_difference_between_segments() -> None:
    got = interaction_test(imbalanced(scale=20), "device_category", "A", "B")
    assert got["difference"] == pytest.approx(0.10)
    assert got["p_value"] < 0.001


def test_interaction_finds_nothing_when_segments_respond_alike() -> None:
    same = pd.concat(
        [
            block("A", "treatment", 2000, 400),
            block("A", "control", 2000, 200),
            block("B", "treatment", 2000, 400),
            block("B", "control", 2000, 200),
        ],
        ignore_index=True,
    )
    got = interaction_test(same, "device_category", "A", "B")
    assert got["difference"] == pytest.approx(0.0)
    assert got["p_value"] > 0.99


def test_overlapping_intervals_are_not_a_test_of_difference() -> None:
    # The reason interaction_test exists. Two segment effects whose intervals
    # overlap can still differ significantly, so eyeballing the intervals gives
    # the wrong answer.
    frame = imbalanced(scale=20)
    per_segment = effect_by_segment(frame, "device_category").set_index(
        "device_category"
    )
    a, b = per_segment.loc["A"], per_segment.loc["B"]

    intervals_overlap = a["ci_low"] <= b["ci_high"] and b["ci_low"] <= a["ci_high"]
    assert (
        not intervals_overlap
        or interaction_test(frame, "device_category", "A", "B")["p_value"] < 0.05
    )
