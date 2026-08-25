# data/

Gitignored except the `.sha256` pins, which are committed. The snapshot itself is
rebuilt by re-running the export.

## Rebuilding the snapshot

1. Run [`../src/extract_sessions.sql`](../src/extract_sessions.sql) in BigQuery
   against `bigquery-public-data.ga4_obfuscated_sample_ecommerce`. A sandbox
   project is enough; no billing account is required.
2. **Save results → CSV → Google Drive.** Not "Google Sheets", and not the local
   download.
3. Download from Drive to `raw/ga4_sessions.csv`.
4. Validate, then pin:

   ```bash
   uv run python projects/01-product-analytics/src/snapshot.py \
       projects/01-product-analytics/data/raw/ga4_sessions.csv --pin
   ```

Expected: 270,154 identifiers, ~355k rows.

## Why those two constraints in step 2

Both were found the hard way, and both fail silently.

**Not Sheets.** A `user_pseudo_id` looks like `1005317.0661766703`. Opened in a
spreadsheet under a European locale, the dot reads as a thousands separator, the
value becomes the 17-digit integer 10053170661766703, and a spreadsheet keeps 15
significant figures — so the last two digits of **every** identifier are zeroed
and distinct users merge. The first export of this snapshot had 100% of its
identifiers ending in `00`.

The column is exported untransformed on purpose: prefixing it would make the
committed query and the pinned snapshot different artefacts. The defence is this
route, and the contract check below.

**Not the local download.** It caps at 10MB against a file of roughly 48MB, and
the truncation is not announced. A short export hashes perfectly well and loads
without complaint; the first sign of trouble would have been a retention figure
biased upward, because dropping sessions at random turns returning identifiers
into one-visit ones.

That is why `snapshot.py` validates against aggregates measured at source before
it will pin anything. The checksum proves a file has not changed. It says nothing
about whether the file was ever right.
