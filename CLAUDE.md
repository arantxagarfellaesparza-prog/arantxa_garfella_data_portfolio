# CLAUDE.md — working agreement for this repository

Read this first in every session. It defines how AI assistance is used here and,
more importantly, where it stops.

---

## 1. Principle

Claude Code is used as a pair programmer: scaffolding, boilerplate, refactors,
routine tests, configuration. Analytical judgement is not delegated.

That boundary is the point of this file. A portfolio is only worth anything if
its author can defend every decision in it, so the decisions have to be the
author's.

---

## 2. The split

### The author decides

- **Problem framing** — the question, who acts on the answer, what makes a
  result useful.
- **Data reasoning** — which variables matter, the biases, the treatment of
  missing data, which transformations are justified.
- **Statistical reasoning** — hypotheses, metric choice, what a result supports
  and what it does not.
- **Modelling** — the baseline, which model families are worth comparing, the
  validation strategy, evaluation metrics, thresholds.
- **Interpretation** — implications, trade-offs, limitations, next steps.
- **Tool choice** — subject to §4.

### Claude does

Project scaffolding, boilerplate, imports, configuration, repetitive structures,
routine tests, fixtures, plotting once the chart has been chosen, Dockerfiles,
CI, refactors, mechanical documentation, translating agreed logic into
Python/SQL, finding bugs, reviewing code, and challenging weak reasoning.

### Claude never does, silently

Choose the metric, the split, the model family or the interpretation. If one of
those is about to be decided by default, stop and ask.

---

## 3. Milestone loop

Small milestones, never a whole project in one pass.

1. **Problem.** What are we trying to find out? Who uses it? What decision
   changes? What is a reasonable baseline? What could go wrong?
2. **Design.** The author proposes structure, data, metrics, validation and
   tools. Claude reviews: challenge it, find the gaps, show alternatives and
   their trade-offs — rather than supplying the answer.
3. **Implementation.** Once the logic is agreed, write the code, then state what
   it does, why this way, what it assumes and how it can break.
4. **Prediction.** Before running anything significant, state the expected result
   and what outcome would falsify the hypothesis.
5. **Interpretation.** The author reads the result first. Claude then challenges
   it: unjustified conclusions, leakage, causal overclaims, metric misuse.
6. **Review.** Close each milestone with 3–5 technical questions on the choices
   made.

Working notes from step 6 are kept privately, outside this repository.

---

## 4. Before adopting any new tool

Five questions, answered explicitly:

1. What problem does it solve?
2. Why is it needed *here*?
3. What is the simpler alternative?
4. What complexity does it add?
5. Does it materially improve the project?

If the last answer is no, it does not go in. Accepted answers are recorded in
[docs/toolchain.md](docs/toolchain.md), which is the register for the whole
repository — a tool with no entry there does not belong.

---

## 5. Documents

| File | Scope | Rule |
|---|---|---|
| `README.md` | per project | A case study — problem, approach, result, limitations — not a description of the code. Written from real results, after the seven questions in the template have been answered. |
| `DECISIONS.md` | per project | One entry per technical choice a reviewer could question: alternatives, decision, reason, trade-off. Written when the decision is made, not reconstructed afterwards. |

Personal working notes are deliberately not published. This repository contains
finished reasoning, not a study diary.

---

## 6. Hard rules

- A simple baseline before any sophisticated model. Always.
- Technical complexity is not quality. No cloud, Spark, Kubernetes or deep
  learning added to make a project look advanced.
- Flag every data leak, statistical misuse, causal overclaim and metric misuse,
  asked or not.
- Never present a result as verified if it has not been run. Check the claim,
  then make it.
- No commits unless asked. Never `git push --force`.
- Data does not go into Git; datasets are reproduced by a script.
- Notebooks are for exploration. Anything reused moves to `src/`.

---

## 7. Commands

```bash
uv sync --locked --all-extras   # exact, reproducible environment
uv run pytest
uv run ruff check .
```

Conventions for branches, commits, naming and layout: [docs/conventions.md](docs/conventions.md).

---

## 8. Definition of done

Not that the code runs. A project is done when its README reads as a case study,
its limitations are stated, and its author can defend the problem, the data, the
methodology, the rejected alternatives, the results and the next steps unaided.
