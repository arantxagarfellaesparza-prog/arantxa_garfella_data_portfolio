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
`uv sync --locked` additionally fails if the lockfile drifts from
`pyproject.toml`, so the reproducibility claim is enforced rather than trusted.

Note the flag: `--frozen` looks like the strict one and is not. It installs
exactly what `uv.lock` contains and never reads `pyproject.toml`, so a
dependency added by hand is quietly missing while CI stays green. `--locked`
re-resolves and fails on drift. Verified, not assumed.

**Simpler alternative** Running the commands locally before pushing.

**Complexity added** One workflow file, free on public repositories.

**Worth learning** Yes — CI is a stated goal of the Production ML project.

---

## DuckDB — local analytical database

**Problem** Run analytical SQL over the pinned snapshot on a laptop, without a
server and without a cloud bill.

**Why here** The exploration happens in BigQuery because that is where the source
lives, but BigQuery is not reproducible for a reader: it needs a Google account,
a project, and a dataset that Google could revise. Pinning an export and querying
it locally makes `git clone && run` true. DuckDB reads CSV and Parquet directly,
so there is no load step to get wrong.

**Simpler alternative** pandas alone. Workable, but the point of this project is
demonstrating analytical SQL — window functions, cohort queries, sessionisation —
and rewriting those as DataFrame operations would hide exactly the skill on
display. A local PostgreSQL would also work and costs a server, a schema
migration and a load step for no analytical gain.

**Complexity added** One dependency, no server, no configuration.

**Worth learning** Yes. DuckDB has become the default for local analytical work,
and the SQL is standard enough that the knowledge transfers to any warehouse.

---

## pandas — dataframes at the analysis boundary

**Problem** Move query results into plotting, statistical tests and the
experiment layer.

**Why here** scipy, statsmodels and matplotlib all speak DataFrame. The division
of labour is deliberate: SQL does the set-based work against the data, pandas
handles what comes after the aggregation.

**Simpler alternative** DuckDB's own relational API, or plain Python. Neither
connects cleanly to the statistical libraries this project needs.

**Complexity added** A large dependency, and a standing temptation to do in
pandas what SQL should do. The rule for this project: aggregation happens in SQL.

**Worth learning** Yes, and it is already partly known — the gap this portfolio
addresses is the SQL side.

---

## Deliberately *not* here (yet)

Added only when a project actually needs it, with an entry above:

| Tool | Waiting for |
|---|---|
| Polars | Not planned — pandas covers this project |
| scikit-learn, XGBoost/LightGBM, SHAP | Project 02 |
| statsmodels | Projects 01 and 03 |
| MLflow, FastAPI, Docker | Project 04 |
| Anthropic/OpenAI SDK, Pydantic | Project 05 |

Not planned: Spark, Kubernetes, deep learning frameworks. None of them solves a
problem these projects have, and adding them to look advanced is the failure
mode this file exists to prevent.
