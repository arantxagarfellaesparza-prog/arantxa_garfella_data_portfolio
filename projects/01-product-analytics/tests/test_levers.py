"""Round numbers, chosen so every expected value can be produced on paper."""

import pytest
from levers import BaseRates, sensitivity

# 1,000 sessions; 20% view; 10% of viewers buy  ->  20 purchases.
# 500 identifiers; 20% return; 10% of returners buy later.
TOY = BaseRates(
    sessions=1_000,
    identifiers=500,
    p_view=0.20,
    p_buy_given_view=0.10,
    p_return=0.20,
    p_buy_after_return=0.10,
)


def test_baseline_follows_the_decomposition() -> None:
    assert TOY.purchases == pytest.approx(20.0)


def test_one_point_is_worth_different_amounts_per_lever() -> None:
    got = sensitivity(TOY).set_index("lever")["purchases_per_1pp"].to_dict()
    # discovery:  1000 * 0.01 * 0.10 = 1
    # conversion: 1000 * 0.20 * 0.01 = 2
    # retention:   500 * 0.01 * 0.10 = 0.5 -> rounds to 0
    assert got["discovery"] == pytest.approx(1.0)
    assert got["conversion"] == pytest.approx(2.0)


def test_relative_shocks_make_discovery_and_conversion_identical() -> None:
    # Purchases = sessions x P(view) x P(buy|view). Scaling either factor by the
    # same proportion scales the product identically, so arithmetic cannot
    # separate these two levers -- only feasibility can.
    got = sensitivity(TOY).set_index("lever")["purchases_per_10pct_relative"].to_dict()
    assert got["discovery"] == got["conversion"]


def test_a_relative_shock_lifts_purchases_by_that_proportion() -> None:
    got = sensitivity(TOY, relative=0.10).set_index("lever")
    assert got.loc["discovery", "pct_uplift_10pct_relative"] == pytest.approx(10.0)


def test_retention_is_flagged_as_an_upper_bound() -> None:
    # The figure comes from observational P(buy later | returned); returners are
    # self-selected, so it caps the value of induced retention.
    got = sensitivity(TOY).set_index("lever")["caveat"].to_dict()
    assert "upper bound" in got["retention"]
    assert got["discovery"] == ""


def test_unknown_lever_is_rejected() -> None:
    from levers import _incremental

    with pytest.raises(ValueError, match="unknown lever"):
        _incremental(TOY, "pricing", 0.01)
