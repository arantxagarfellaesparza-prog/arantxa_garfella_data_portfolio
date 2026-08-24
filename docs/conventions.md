# Conventions

Small, boring rules. Their value is that they remove decisions from every commit.

## Branches

```
<type>/<short-description>
```

`feat/funnel-cohort-queries`, `fix/leakage-in-train-split`, `docs/credit-risk-readme`,
`chore/bump-ruff`.

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `exp` (an experiment
that may be thrown away).

Work on a branch, merge into `main` when the milestone closes. `main` should
always be in a state I would be happy for someone to open.

## Commits

[Conventional Commits](https://www.conventionalcommits.org/), with the project
as scope:

```
feat(credit-risk): add temporal train/test split
fix(product-analytics): correct session boundary at midnight
docs(credit-risk): record why PR-AUC is the primary metric
```

Write the subject as what the commit *does*, in the imperative. If the body
needs to explain a decision, the decision probably belongs in `DECISIONS.md` and
the commit should link to it.

## Project layout

Every project under `projects/` is copied from `templates/project/` and keeps
this shape:

```
projects/NN-name/
├── README.md          Case study
├── DECISIONS.md       Technical choices + trade-offs
├── data/              raw / interim / processed — gitignored
├── notebooks/         Exploration only, numbered: 01-eda.ipynb
├── src/               Reusable code: anything a notebook would import twice
└── tests/             pytest, mirrors src/
```

Prefix projects with a two-digit number so they sort in the order they were
built: `01-product-analytics`, `02-credit-risk`.

## Naming

- Notebooks: `NN-verb-noun.ipynb` — `02-build-funnel.ipynb`.
- Test files: `test_<module>.py`, mirroring the module they cover.
- SQL files: `NN_purpose.sql` — `03_retention_cohorts.sql`.
- Columns and variables: `snake_case`, spelled out. `days_since_signup`, not `dss`.

## The data rule

`data/` is gitignored. A dataset arrives in the repo as *the script that
produces it*, never as the file itself — that is what makes "clone and re-run"
true rather than aspirational.

Exception: small hand-written fixtures under `tests/fixtures/` are tracked,
because deterministic tests need them.

## Code style

Enforced, so it is not worth arguing about: `ruff` for lint and formatting,
88-character lines, type hints on anything in `src/`.

Comments explain **why**, not **what**. The code already says what it does.
