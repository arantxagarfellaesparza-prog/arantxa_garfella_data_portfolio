# notebooks/

Exploration only. Numbered in reading order: `01-eda.ipynb`, `02-build-funnel.ipynb`.

Anything a second notebook would import moves to `src/`. Notebooks are where a
question is asked; they are a bad place for the answer to live, because they run
top-to-bottom only in theory.

Outputs are stripped on commit by `nbstripout` — the diff stays readable and no
rows of data end up in a public repository.
