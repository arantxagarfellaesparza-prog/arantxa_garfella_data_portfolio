# Projects

One folder per project, self-contained, numbered in the order it was built.

- **[01-product-analytics](01-product-analytics)** — product analytics and
  experimentation on the public GA4 e-commerce sample. In progress.

See [../docs/roadmap.md](../docs/roadmap.md) for what follows.

## Starting a new project

```bash
cp -R templates/project projects/01-product-analytics
```

Then, in order:

1. Fill in the **Problem** section of `README.md`. Nothing else — the rest of the
   case study is written from real results, not predicted ones.
2. Open `DECISIONS.md` with the first real choice (usually the dataset, or the
   metric). Personal working notes stay outside the repository.
3. Add the project's own dependencies to the root `pyproject.toml` as an
   optional group, and record each new tool in [../docs/toolchain.md](../docs/toolchain.md).

A project folder is only added to Git once it has a real first commit. An empty
scaffold in a public repository advertises an abandoned project.
