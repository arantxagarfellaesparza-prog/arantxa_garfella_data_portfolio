"""One place to fix randomness, so a result can be reproduced tomorrow.

Setting `random.seed` alone is not enough: scikit-learn, pandas sampling and
most simulation code draw from NumPy, which keeps its own independent state.
"""

from __future__ import annotations

import os
import random

import numpy as np

DEFAULT_SEED = 42


def set_seed(seed: int = DEFAULT_SEED) -> np.random.Generator:
    """Seed the global RNGs and return a fresh independent Generator.

    Prefer the returned Generator over the module-level `np.random.*` functions:
    passing it explicitly makes the source of randomness visible in the call
    site, so a function that secretly depends on global state cannot hide.
    """
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise TypeError(f"seed must be an int, got {type(seed).__name__}")

    random.seed(seed)
    # NPY002 flags the legacy global RNG, and for new code it is right. Seeding it
    # anyway is the whole point here: scikit-learn with `random_state=None` and
    # `DataFrame.sample()` both draw from this global state, so skipping it would
    # leave the most common sources of randomness unseeded.
    np.random.seed(seed)  # noqa: NPY002
    # Some libraries read this at import time to seed their own internals.
    os.environ["PYTHONHASHSEED"] = str(seed)

    return np.random.default_rng(seed)
