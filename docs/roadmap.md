# Roadmap

Five projects, built in this order, each chosen to cover a different family of
problems rather than repeat the same one with a new dataset. Roughly 90–110
hours of deliberate work in total.

The order matters: SQL and applied statistics come first because they run
underneath everything else; production engineering comes fourth because it
reuses a model rather than starting a new statistical problem.

---

## Phase 0 — Foundation ✅

Project structure, dependency management, linting, tests, CI, and the working
agreement in [CLAUDE.md](../CLAUDE.md). Shared helpers limited to the two things
every project needs: path resolution and reproducible seeding.

**Done when** a clean clone installs, lints and passes its tests in CI.

---

## 01 — Product Analytics & Experimentation

> Where does the funnel leak, which behaviours predict retention, and how would
> we design a test for a fix?

Build an event dataset and answer it in SQL: funnels, activation, cohorts,
retention, segmentation, channel quality. Then design an experiment properly —
randomisation, metric selection, power analysis, duration, and an honest reading
of the result.

**Stack** SQL · DuckDB or PostgreSQL · pandas · scipy/statsmodels · matplotlib

**Done when** I can explain, unaided: how to build a funnel in SQL, activation vs
retention, what a cohort is, when a window function is the right tool, what a
confidence interval means, what statistical power is, and why statistical
significance is not business impact.

---

## 02 — Credit Risk Modelling

> Can we estimate probability of default with probabilities calibrated well
> enough to be used in a risk decision?

The flagship, and the one closest to my thesis work on credit risk, A-IRB and
NPLs. Logistic regression as a serious baseline before any boosting; evaluation
built around PR-AUC, KS, Brier score and calibration curves rather than accuracy;
SHAP for explanation; a model card for the limitations.

**Stack** scikit-learn · XGBoost/LightGBM · SHAP · statsmodels

**Done when** I can explain: why logistic regression is a strong baseline,
discrimination vs calibration, ROC-AUC vs PR-AUC, class imbalance, leakage,
threshold selection against the cost of false positives and false negatives, and
why the best model by AUC may not be the best model for the business.

---

## 03 — Revenue Forecasting Under Uncertainty

> What revenue can we expect next, and what is the honest range around it?

Finance as the context, forecasting as the skill. Naïve and seasonal-naïve
baselines first, then ETS and ARIMA, then boosting on lag features — kept only
if it beats the baseline. Walk-forward backtesting throughout, because a random
split silently destroys a temporal problem. Ends in prediction intervals and
scenarios, not a single number.

**Stack** statsmodels · scikit-learn · pandas

**Done when** I can explain: why a random split breaks temporal problems, what
autocorrelation represents, why a naïve baseline is non-negotiable, prediction
vs interval, how to backtest, and when the more complex model is not worth it.

---

## 04 — Production ML

> How does a notebook that produces a prediction become a system that can be
> trained, tested, versioned and served?

Reuses the model from 02 or 03 — the statistical problem is already solved, so
all the learning goes into the engineering. Notebook to package, training and
inference pipelines, tests, experiment tracking, an API, a container, CI, and a
written monitoring plan.

**Stack** pytest · MLflow · FastAPI · Docker · GitHub Actions

**Done when** I can explain: training vs inference, why data code needs tests,
what MLflow records, what Docker is for, what to monitor in production, data
drift vs concept drift, and which parts of a pipeline must be deterministic.

---

## 05 — AI Data Analyst Agent

> Can an agent turn business questions into reliable SQL — and how would we
> prove that it is reliable?

The interesting part is not the agent, it is the evaluation. A golden question
set, execution accuracy vs semantic accuracy, a failure taxonomy, hallucination
rate, latency and cost. Guardrails are part of the design: read-only access,
schema restrictions, query validation, rejection of unsafe SQL.

```
Question → schema context → SQL generation → validation/guardrails
        → read-only database → result → analysis → answer + chart
```

**Stack** Anthropic/OpenAI SDK · DuckDB/PostgreSQL · Pydantic · pytest

**Done when** I can explain: why a working demo does not demonstrate
reliability, how to build an evaluation set, execution vs semantic accuracy,
the failure modes, the guardrails, the cost/latency picture — and when a
deterministic workflow beats an agent.

---

## Optional — BI layer

A Power BI semantic model over the Project 01 data, if I apply seriously to
Data Analyst / BI roles. Not allowed to delay the five above.

---

## Explicitly out of scope

Titanic, Iris, generic house prices, generic sentiment analysis, chat-over-PDF,
Kaggle notebooks with no narrative, dashboards with no business question, a DCF
mechanically translated to Python, and any technology added to inflate the stack
rather than solve a problem.
