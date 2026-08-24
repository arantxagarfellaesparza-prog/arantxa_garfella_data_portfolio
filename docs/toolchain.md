# Toolchain register

Every tool in this repository had to answer five questions before it was
adopted (see [CLAUDE.md §4](../CLAUDE.md)). This file is the record. A tool with
no entry here does not belong in the repo.

The point is being able to answer *"why this and not the simpler thing?"* in an
interview, rather than listing technologies.

---

## uv — environments and dependencies

**Problem** Install dependencies, manage the virtual environment, and pin exact
versions so the repo can be rebuilt identically later.

**Why here** Reproducibility is a claim this portfolio makes. `pip install` alone
resolves to whatever is newest on the day it runs, so a result from today may
not reproduce in three months. `uv.lock` records the exact resolved versions.

**Simpler alternative** `python -m venv` + `pip install -e .`. Fine, but no
lockfile — so the reproducibility claim would be weaker than it sounds.

**Complexity added** One binary, one lockfile. `pyproject.toml` stays standard,
so dropping uv later costs nothing.

**Worth learning** Yes. Dependency and environment management appear in every
data role, and "how do you make an analysis reproducible?" is a standard
interview question.

---

## ruff — lint and format

**Problem** Catch unused imports, undefined names, import ordering and likely
bugs; keep formatting consistent so diffs show real changes.

**Why here** In a public repo, inconsistent style reads as carelessness. More
usefully, the `B` (bugbear) and `NPY` rules catch actual mistakes — mutable
default arguments, legacy NumPy RNG use.

**Simpler alternative** black + flake8 + isort: three tools, three configs, same
result.

**Complexity added** One dev dependency, one config block.

**Worth learning** The concept yes (linting, static checks), the specific tool is
interchangeable.

---

## pytest — tests

**Problem** Prove that shared code behaves as claimed, and keep it behaving that
way after a refactor.

**Why here** Path resolution and seeding fail *silently* — the wrong folder gets
created, the write succeeds, and the bug only appears when a result cannot be
reproduced. Tests are how a silent failure becomes a loud one.

**Simpler alternative** `assert` statements in a script. No fixtures, no
parametrisation, no isolation.

**Complexity added** Minimal; it is the default in Python.

**Worth learning** Yes. "Do you test data code?" separates analysts who ship from
analysts who hand over notebooks.

---

## pre-commit — hooks before commit

**Problem** Stop mistakes that are expensive to undo once they are in history.

**Why here** Two specifically: a committed dataset or model file stays in the
Git history forever even after deletion, and notebook outputs can embed rows of
real data into a public repo. `check-added-large-files` and `nbstripout` prevent
both at the only moment where prevention is cheap.

**Simpler alternative** Remembering. This fails exactly once, and once is enough.

**Complexity added** One config file and one `pre-commit install` per clone.

**Worth learning** Moderately — the underlying idea (automate the checks you
would otherwise forget) transfers to CI.

---

## GitHub Actions — CI

**Problem** Verify on a clean machine that the repo installs, lints and passes
its tests.

**Why here** It converts "works on my machine" from an assumption into a check.
`uv sync --frozen` additionally fails if the lockfile drifts from
`pyproject.toml`, so the reproducibility claim is enforced rather than trusted.

**Simpler alternative** Running the commands locally before pushing.

**Complexity added** One workflow file, free on public repositories.

**Worth learning** Yes — CI is a stated goal of the Production ML project.

---

## Deliberately *not* here (yet)

Added only when a project actually needs it, with an entry above:

| Tool | Waiting for |
|---|---|
| pandas / Polars, DuckDB | Project 01 |
| scikit-learn, XGBoost/LightGBM, SHAP | Project 02 |
| statsmodels | Projects 01 and 03 |
| MLflow, FastAPI, Docker | Project 04 |
| Anthropic/OpenAI SDK, Pydantic | Project 05 |

Not planned: Spark, Kubernetes, deep learning frameworks. None of them solves a
problem these projects have, and adding them to look advanced is the failure
mode this file exists to prevent.
