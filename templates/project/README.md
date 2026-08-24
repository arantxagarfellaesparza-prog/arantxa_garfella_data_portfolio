# <Project name>

> One sentence: the business question, not the technique.

<!--
This README is a case study, not a description of the code. Before writing any
of it, answer the seven questions below for yourself. Only the Problem section
should exist before there are results — the rest is written from what actually
happened, not from what was expected.

  1. What was the problem?
  2. What did we learn?
  3. What decision does it enable?
  4. What approach did we use?
  5. What result did we get?
  6. What are the limitations?
  7. What would I do next?

Delete this comment when the README is real.
-->

**Status:** in progress · **Time invested:** ~Xh

---

## Problem

Who would act on this analysis, and what decision would change depending on the
answer? What would a useful result look like — and what would make it useless?

## Data

Source, size, period covered, how it is obtained (the script, not the file).
Known quality issues and biases. What is missing and why that matters.

## Approach

The baseline first, then what was added and what it bought. Validation strategy
and why it is the right one for this problem. Metrics and why these rather than
the obvious ones.

Full reasoning and rejected alternatives: [DECISIONS.md](DECISIONS.md).

## Results

| Model | <Metric> | <Metric> | <Metric> |
|---|---|---|---|
| Baseline | | | |
| | | | |

What the numbers mean in the language of the decision, not the language of the
metric.

## Limitations

Where this stops being trustworthy. Assumptions that would break it. What a
sceptical reviewer would attack first — write it here before they say it.

## What I would do next

The most valuable next step, and why it is that one and not the flashier one.

---

## Reproducing

```bash
uv sync --all-extras
uv run python src/make_dataset.py   # rebuilds data/ from scratch
uv run pytest projects/<this-project>
```

## Files

```
notebooks/   Exploration, numbered in reading order
src/         Reusable code
tests/       Tests mirroring src/
data/        Gitignored — rebuilt by the script above
```
