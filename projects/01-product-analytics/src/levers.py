"""Put the three candidate levers on one scale: incremental purchases.

The three headline rates -- 78.6% of sessions never view a product, 93.7% of
viewers do not buy, 82.5% of identifiers never return -- have different
denominators and cannot be compared as they stand. What can be compared is the
effect of improving each one on the quantity the business actually counts.

Two shocks are reported on purpose. An absolute +1pp is the same *arithmetic*
step for every lever and a wildly different *amount of work*: one point on a
21.4% base is a 4.7% improvement, one point on a 6.3% base is 15.9%. A +10%
relative shock equalises the effort assumption instead of the arithmetic.

Neither shock says which lever is easier to move. That is not knowable from this
data, and the analysis deliberately stops short of pretending otherwise: it
supplies the derivative, and whoever owns the roadmap supplies the feasibility.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class BaseRates:
    """Measured rates the sensitivity is computed from. See base_rates.sql."""

    sessions: int
    identifiers: int
    p_view: float
    p_buy_given_view: float
    p_return: float
    p_buy_after_return: float

    @property
    def purchases(self) -> float:
        """Baseline purchases implied by the decomposition.

        Checked against the observed count in the tests: if the identity does
        not reproduce reality, the sensitivity built on it means nothing.
        """
        return self.sessions * self.p_view * self.p_buy_given_view


def _incremental(rates: BaseRates, lever: str, delta: float) -> float:
    """Incremental purchases from moving one lever by `delta` (absolute)."""
    if lever == "discovery":
        # More sessions reach a product; they convert at the observed rate.
        return rates.sessions * delta * rates.p_buy_given_view
    if lever == "conversion":
        # The same viewers convert more often.
        return rates.sessions * rates.p_view * delta
    if lever == "retention":
        # More identifiers come back, each carrying the observed probability of
        # buying on a later visit. Upper bound -- see `caveat` below.
        return rates.identifiers * delta * rates.p_buy_after_return
    raise ValueError(f"unknown lever {lever!r}")


LEVERS = {
    "discovery": ("p_view", "Sessions reaching a product view"),
    "conversion": ("p_buy_given_view", "Viewers who purchase"),
    "retention": ("p_return", "Identifiers returning for a second session"),
}

# Retention's figure is computed from P(buy on a later visit | returned), which
# is observational. Identifiers who return did so unprompted and are
# self-selected for interest, so an intervention that *induces* returns cannot
# assume the induced returner behaves like the natural one. The number is a
# ceiling on the value of induced retention, not an estimate of it.
_UPPER_BOUND = {"retention"}


def sensitivity(
    rates: BaseRates, *, absolute_pp: float = 1.0, relative: float = 0.10
) -> pd.DataFrame:
    """Incremental purchases per lever, under an absolute and a relative shock."""
    baseline = rates.purchases
    rows = []
    for lever, (attr, description) in LEVERS.items():
        base_rate = getattr(rates, attr)
        rows.append(
            {
                "lever": lever,
                "what_improves": description,
                "base_rate_pct": round(100 * base_rate, 2),
                "purchases_per_1pp": round(
                    _incremental(rates, lever, absolute_pp / 100), 0
                ),
                "purchases_per_10pct_relative": round(
                    _incremental(rates, lever, base_rate * relative), 0
                ),
                "pct_uplift_10pct_relative": round(
                    100 * _incremental(rates, lever, base_rate * relative) / baseline, 1
                ),
                "caveat": "upper bound (selection)" if lever in _UPPER_BOUND else "",
            }
        )
    return pd.DataFrame(rows).sort_values(
        "purchases_per_10pct_relative", ascending=False
    )
