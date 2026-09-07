# tests/

Mirrors `src/`: `src/features.py` → `tests/test_features.py`.

Worth testing in a data project, in priority order:

1. **Anything that fails silently** — path resolution, joins that drop rows,
   splits that leak future information into training.
2. **Feature engineering** — a small hand-built fixture with a known answer.
3. **Data contracts** — expected columns, dtypes, ranges, and the null rate you
   agreed to tolerate.

Not worth testing: whether scikit-learn works.

Small fixtures live in `tests/fixtures/` and *are* tracked — deterministic tests
need them.
