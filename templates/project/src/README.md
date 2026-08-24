# src/

Reusable code for this project: dataset construction, feature engineering,
training, evaluation.

Rules of thumb: functions take explicit inputs and return values rather than
reading globals; type hints on anything exported; randomness comes from a seeded
generator passed in, not from module-level `np.random`.

If it is here, `tests/` covers it.
