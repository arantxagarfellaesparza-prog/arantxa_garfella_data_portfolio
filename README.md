# Data Portfolio — Arantxa Garfella Esparza

Applied data science, built to be defended in an interview rather than skimmed.

Each project here starts from a business question, states its assumptions, picks
metrics on purpose, and ends with what the result would actually let someone
decide — including where the analysis stops being trustworthy.

**Positioning:** business-trained data practitioner who can analyse, model,
automate and ship.

---

## Projects

| # | Project | Question it answers | Core skills | Status |
|---|---------|--------------------|-------------|--------|
| 01 | Product Analytics & Experimentation | Where does the funnel leak, which behaviours predict retention, and how would we test a fix? | SQL (window functions, cohorts, sessionization), applied statistics, A/B design & power | Not started |
| 02 | Credit Risk Modelling | Can we estimate probability of default with probabilities calibrated well enough to make risk decisions? | Feature engineering, logistic regression → boosting, PR-AUC / KS / Brier, calibration, SHAP | Not started |
| 03 | Revenue Forecasting Under Uncertainty | What revenue can we expect next, and how wide is the honest uncertainty band? | Time-series validation, ETS/ARIMA, walk-forward backtesting, prediction intervals, scenarios | Not started |
| 04 | Production ML | How does a notebook model become a system that can be retrained, tested, versioned and served? | Package structure, pytest, MLflow, FastAPI, Docker, CI, drift monitoring | Not started |
| 05 | AI Data Analyst Agent | Can an agent turn business questions into *reliable* SQL — and how would we prove it? | LLM tool calling, SQL guardrails, golden eval set, execution accuracy, failure taxonomy | Not started |

Status is updated when a project is genuinely finished, which here means its
README is a case study and I can defend it without notes — not when the code runs.

📍 **Currently:** Phase 0 — foundation and tooling. See [docs/roadmap.md](docs/roadmap.md).

---

## How this repo is organised

```
projects/            One folder per project, each self-contained
templates/project/   The skeleton every new project is copied from
src/portfolio_core/  The few helpers shared by all projects (paths, seeds)
docs/                Roadmap, conventions, and the toolchain register
```

Every project carries three documents on purpose:

- **`README.md`** — the case study: problem, approach, result, limitations.
- **`DECISIONS.md`** — technical choices with the alternatives considered and the
  trade-off accepted. Written *before* the result is known, so it records
  reasoning rather than justification after the fact.
- **`LEARNING_LOG.md`** — concepts in my own words, and the ones I could not yet
  explain without notes.

---

## Running it

Requires [uv](https://docs.astral.sh/uv/) and Python 3.13 (uv installs it).

```bash
git clone https://github.com/arantxagarfellaesparza-prog/arantxa_garfella_data_portfolio.git
cd arantxa_garfella_data_portfolio
uv sync --all-extras
uv run pytest
```

Optional, recommended before the first commit:

```bash
uv run pre-commit install
```

<details>
<summary>Without uv (plain venv + pip)</summary>

```bash
python3.13 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

You lose the lockfile, so exact dependency versions are no longer pinned.
</details>

---

## A note on how this was built

I use Claude Code as a pair programmer for scaffolding, boilerplate and
refactors. The problem framing, metric choices, validation strategy, model
selection and interpretation are mine — that split is written down and enforced
in [CLAUDE.md](CLAUDE.md), because a portfolio that demonstrates skills I do not
have is worse than no portfolio.

## Licence

[MIT](LICENSE).
