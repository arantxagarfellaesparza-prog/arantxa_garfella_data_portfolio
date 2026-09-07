# data/

Gitignored, on purpose. This folder is rebuilt by the project's dataset script,
which is the tracked artefact.

```
raw/         As downloaded or generated. Never edited by hand.
interim/     Intermediate steps.
processed/   What analysis and models read.
```

Keeping the three apart is what makes "delete everything and re-run" a real
option rather than a hope. If a fix only exists as a manual edit to a file in
`raw/`, the pipeline is not reproducible.

Resolve these paths with `portfolio_core.paths.data_dir("raw")` rather than a
relative string — a notebook and a script have different working directories.
