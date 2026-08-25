"""Toy parameters throughout: these verify the machinery, not the blinded run.

If the injection did not produce the lift it was asked for, the reveal would
score the analysis against a number that was never actually in the data.
"""

import numpy as np
import pandas as pd
import pytest
from experiment import Params, run_experiment


def population(n: int = 40_000, base: float = 0.10, mobile_share: float = 0.5):
    rng = np.random.default_rng(0)
    device = np.where(rng.random(n) < mobile_share, "mobile", "desktop")
    return pd.DataFrame(
        {
            "user_pseudo_id": [f"u{i}" for i in range(n)],
            "device_category": device,
            "purchased": rng.random(n) < base,
        }
    )


NEUTRAL = Params(
    seed=1,
    window_days=7,
    assign_prob={"mobile": 0.5, "desktop": 0.5},
    lift={"mobile": 0.0, "desktop": 0.0},
)


def test_a_zero_lift_leaves_the_outcome_untouched() -> None:
    pop = population()
    out = run_experiment(pop, NEUTRAL)
    assert (out["outcome"].to_numpy() == pop["purchased"].to_numpy()).all()


def test_the_injected_lift_is_the_lift_requested() -> None:
    params = Params(
        seed=2,
        window_days=7,
        assign_prob={"mobile": 0.5, "desktop": 0.5},
        lift={"mobile": 0.30, "desktop": 0.0},
    )
    out = run_experiment(population(n=200_000), params)
    mobile = out[out["device_category"] == "mobile"]
    treated = mobile[mobile["arm"] == "treatment"]["outcome"].mean()
    control = mobile[mobile["arm"] == "control"]["outcome"].mean()
    assert treated / control == pytest.approx(1.30, abs=0.04)


def test_lift_is_confined_to_the_named_segment() -> None:
    params = Params(
        seed=3,
        window_days=7,
        assign_prob={"mobile": 0.5, "desktop": 0.5},
        lift={"mobile": 0.30, "desktop": 0.0},
    )
    out = run_experiment(population(n=200_000), params)
    desktop = out[out["device_category"] == "desktop"]
    treated = desktop[desktop["arm"] == "treatment"]["outcome"].mean()
    control = desktop[desktop["arm"] == "control"]["outcome"].mean()
    assert treated / control == pytest.approx(1.0, abs=0.06)


def test_unequal_assignment_probability_produces_a_ratio_mismatch() -> None:
    # A real SRM is usually a bug that touches one slice of traffic rather than
    # a uniformly biased coin, so assignment probability varies by covariate.
    params = Params(
        seed=4,
        window_days=7,
        assign_prob={"mobile": 0.40, "desktop": 0.60},
        lift={"mobile": 0.0, "desktop": 0.0},
    )
    out = run_experiment(population(n=200_000), params)
    share_mobile_treatment = (
        out[out["arm"] == "treatment"]["device_category"].eq("mobile").mean()
    )
    share_mobile_control = (
        out[out["arm"] == "control"]["device_category"].eq("mobile").mean()
    )
    # The arms differ in composition, which is what a balance check must catch.
    assert share_mobile_treatment < share_mobile_control - 0.10


def test_assignment_is_reproducible_from_the_seed() -> None:
    pop = population()
    first = run_experiment(pop, NEUTRAL)["arm"].to_numpy()
    second = run_experiment(pop, NEUTRAL)["arm"].to_numpy()
    assert (first == second).all()
