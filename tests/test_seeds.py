"""Reproducibility is a claim the repo makes in its README. A test is what
turns that claim into something checkable."""

import random

import numpy as np
import pytest

from portfolio_core.seeds import set_seed


def test_same_seed_gives_the_same_draws() -> None:
    first = set_seed(7).normal(size=5)
    second = set_seed(7).normal(size=5)
    np.testing.assert_array_equal(first, second)


def test_different_seeds_give_different_draws() -> None:
    assert not np.array_equal(set_seed(7).normal(size=5), set_seed(8).normal(size=5))


def test_stdlib_random_is_seeded_too() -> None:
    set_seed(7)
    first = [random.random() for _ in range(3)]
    set_seed(7)
    assert [random.random() for _ in range(3)] == first


def test_bool_is_rejected_as_a_seed() -> None:
    # bool is a subclass of int in Python, so set_seed(True) would otherwise be
    # accepted and silently mean seed=1.
    with pytest.raises(TypeError):
        set_seed(True)  # type: ignore[arg-type]
