"""Synthetic throughout. These check the instruments, not the blinded run.

A validity check that is itself broken is worse than no check: it produces a
PASS that nobody re-examines.
"""

import numpy as np
import pandas as pd
import pytest
from validity import aa_simulation, balance, srm, two_proportion_test


def arms(n_treatment: int, n_control: int) -> pd.Series:
    return pd.Series(["treatment"] * n_treatment + ["control"] * n_control)


def test_srm_passes_an_even_split() -> None:
    assert srm(arms(50_000, 50_000)).passed


def test_srm_fails_a_split_that_is_off_by_one_point() -> None:
    # 50.5/49.5 on 250k is a real deviation, not noise.
    result = srm(arms(126_600, 124_100))
    assert not result.passed
    assert result.detail["deviation from 50% (pp)"] == pytest.approx(0.5, abs=0.02)


def test_srm_tolerates_a_deviation_too_small_to_distinguish() -> None:
    # 0.05pp on 250k: below what this sample size can separate from chance.
    assert srm(arms(125_480, 125_230)).passed


def test_balance_passes_when_assignment_ignores_the_covariate() -> None:
    rng = np.random.default_rng(0)
    n = 100_000
    frame = pd.DataFrame(
        {
            "arm": np.where(rng.random(n) < 0.5, "treatment", "control"),
            "device_category": rng.choice(["desktop", "mobile"], n, p=[0.6, 0.4]),
        }
    )
    assert balance(frame, "device_category").passed


def test_balance_fails_when_assignment_depends_on_the_covariate() -> None:
    # The realistic shape of a broken assignment: a bug touching one slice.
    rng = np.random.default_rng(1)
    n = 100_000
    device = rng.choice(["desktop", "mobile"], n, p=[0.6, 0.4])
    prob = np.where(device == "mobile", 0.45, 0.55)
    frame = pd.DataFrame(
        {
            "arm": np.where(rng.random(n) < prob, "treatment", "control"),
            "device_category": device,
        }
    )
    result = balance(frame, "device_category")
    assert not result.passed
    assert result.detail["mobile: treat - control (pp)"] < -5


def test_two_proportion_test_arithmetic() -> None:
    # 100 of 1000 treated convert, 50 of 1000 control: +5pp, a 100% relative lift.
    outcome = np.array([True] * 100 + [False] * 900 + [True] * 50 + [False] * 950)
    treated = np.array([True] * 1000 + [False] * 1000)
    got = two_proportion_test(outcome, treated)
    assert got["rate_treatment"] == pytest.approx(0.10)
    assert got["rate_control"] == pytest.approx(0.05)
    assert got["absolute_diff"] == pytest.approx(0.05)
    assert got["relative_lift"] == pytest.approx(1.0)
    assert got["ci_low"] < 0.05 < got["ci_high"]


def test_aa_rejects_at_about_alpha_under_a_true_null() -> None:
    # The estimator validating itself. A rejection rate far from alpha means the
    # standard error is wrong, and every p-value it produces is wrong with it.
    rng = np.random.default_rng(2)
    outcome = rng.random(60_000) < 0.015
    got = aa_simulation(outcome, n_reps=400, seed=7, alpha=0.05)
    assert got["rejected"].mean() == pytest.approx(0.05, abs=0.025)


def test_aa_intervals_cover_zero_at_about_the_nominal_rate() -> None:
    rng = np.random.default_rng(3)
    outcome = rng.random(60_000) < 0.015
    got = aa_simulation(outcome, n_reps=400, seed=8, alpha=0.05)
    assert got["covers_zero"].mean() == pytest.approx(0.95, abs=0.025)


def test_aa_p_values_are_uniform_under_the_null() -> None:
    from scipy import stats

    rng = np.random.default_rng(4)
    outcome = rng.random(60_000) < 0.015
    got = aa_simulation(outcome, n_reps=400, seed=9)
    # Kolmogorov-Smirnov against Uniform(0,1): non-uniform p-values mean the
    # test is miscalibrated even if its rejection rate happens to look right.
    assert stats.kstest(got["p_value"], "uniform").pvalue > 0.01
