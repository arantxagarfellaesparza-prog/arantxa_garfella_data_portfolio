"""Blinded synthetic experiment over real users.

Randomisation and outcomes are real; the treatment effect is injected. The point
of the exercise is not to estimate an effect -- it is to check whether an
experiment is valid *before* estimating anything, on a dataset where the truth
is known and can be revealed afterwards to score the attempt.

What this design can and cannot teach:

  * It can teach validity checking, power, effect estimation and subgroup
    analysis against known ground truth.
  * It cannot teach mediation. The effect is injected directly on the outcome
    rather than on P(view_item) and allowed to propagate, so the causal chain
    the treatment is supposed to act through is not simulated.
  * It is cleaner than reality on identity. Identifier instability would
    contaminate a real experiment by putting one human in both arms; here the
    effect is injected at identifier level, so the estimand is defined on
    identifiers and the estimate is unbiased by construction.

Parameters live outside the repository while the experiment is blinded, and are
committed at the reveal so the result becomes reproducible.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

# Committed at the reveal (DECISIONS 007). While the experiment was blinded this
# pointed outside the repository, so the estimate could not be made with the
# answer in view; now it lives here, because a result nobody can regenerate is
# not a result.
PARAMS_PATH = Path(__file__).parent / "experiment-params.json"
OUTPUT_PATH = Path(__file__).parents[1] / "data" / "interim" / "experiment.csv"

# Randomisation is per identifier (DECISIONS 001). The outcome is aggregated to
# the same unit: analysing sessions while randomising identifiers would
# understate the standard error, because sessions within an identifier are
# correlated. At 1.33 sessions per identifier that costs ~0.3pp of MDE and
# removes the clustering entirely.
POPULATION_SQL = """
WITH per_user AS (
  SELECT
    user_pseudo_id,
    min(session_start_us)                              AS first_seen_us,
    min(CASE WHEN purchased THEN session_start_us END) AS first_purchase_us,
    arg_min(device_category, session_start_us)         AS device_category
  FROM sessions
  GROUP BY user_pseudo_id
),
bounds AS (SELECT max(session_start_us) AS last_us FROM sessions)
SELECT
  user_pseudo_id,
  device_category,
  -- Purchased within the window of first being seen. NULL first_purchase_us
  -- means never purchased, which is a genuine zero rather than missing data.
  coalesce(
    first_purchase_us <= first_seen_us + {window_days} * 86400000000, false
  ) AS purchased
FROM per_user, bounds
-- Right-censoring: an identifier first seen with fewer than `window_days` left
-- in the data never had the chance to convert inside the window. Keeping them
-- would count absence of opportunity as absence of effect.
WHERE first_seen_us <= last_us - {window_days} * 86400000000
"""


@dataclass(frozen=True)
class Params:
    """Generative truth. Hidden while the experiment is blinded."""

    seed: int
    window_days: int
    assign_prob: dict[str, float]
    lift: dict[str, float]

    @classmethod
    def load(cls, path: Path = PARAMS_PATH) -> Params:
        raw = json.loads(path.read_text())
        return cls(**raw)


def build_population(
    con: duckdb.DuckDBPyConnection, *, window_days: int
) -> pd.DataFrame:
    """Eligible identifiers with their pre-treatment covariate and real outcome."""
    return con.execute(POPULATION_SQL.format(window_days=window_days)).df()


def run_experiment(population: pd.DataFrame, params: Params) -> pd.DataFrame:
    """Assign arms and inject the effect.

    Assignment probability is allowed to vary by covariate, which is how a real
    sample ratio mismatch usually arises -- not as a clean coin-flip error, but
    as a bug that touches one slice of traffic.
    """
    rng = np.random.default_rng(params.seed)
    out = population.copy()

    probs = out["device_category"].map(params.assign_prob).fillna(0.5).to_numpy()
    out["arm"] = np.where(rng.random(len(out)) < probs, "treatment", "control")

    # Inject a relative lift by promoting non-purchasers. To move a rate from p0
    # to p0(1+lift), each existing zero must flip with probability
    # p0 * lift / (1 - p0).
    out["outcome"] = out["purchased"].to_numpy()
    for device, lift in params.lift.items():
        if lift == 0:
            continue
        treated = (out["arm"] == "treatment") & (out["device_category"] == device)
        p0 = out.loc[out["device_category"] == device, "purchased"].mean()
        flip_prob = p0 * lift / (1 - p0)
        zeros = treated & ~out["purchased"]
        out.loc[zeros, "outcome"] = rng.random(int(zeros.sum())) < flip_prob

    return out[["user_pseudo_id", "device_category", "arm", "outcome"]]


def _main() -> int:
    """Generate the blinded dataset. Prints nothing about the parameters."""
    from analysis import open_snapshot

    params = Params.load()
    population = build_population(open_snapshot(), window_days=params.window_days)
    result = run_experiment(population, params)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_PATH, index=False)
    print(f"Wrote {len(result):,} rows to {OUTPUT_PATH}")
    print(f"Columns: {list(result.columns)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
