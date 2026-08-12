# Data quality findings — Food.com recipe dataset

**Status:** generated from `analyze_quality.py` against the full dataset (231,637 recipes, 1,132,367 interactions) on 2026-08-12. Phase 1, Step 3.

## Findings that need follow-up before modeling

1. **`minutes` contains an integer-overflow sentinel, not a real value.** Max = `2,147,483,647` = `2^31 - 1`. This is corrupted/placeholder data from upstream, not a genuinely slow recipe. **Must be excluded or capped** before `minutes` is used in any scoring, filtering, or ML feature — as-is, it would badly skew anything that touches the raw column (mean, normalization, etc.).
2. **`calories` has an implausible max of 434,360.** Also almost certainly a data error (`p99` is a much more reasonable 3,517). Needs a cap or exclusion rule before it's trusted.
3. **Raw ingredient strings aren't canonicalized.** `garlic` (18,087 recipes) and `garlic cloves` (25,748 recipes) are counted separately, despite referring to the same ingredient. This is concrete evidence for why Phase 1 Step 4 (ingredient normalization) is necessary — it's not a hypothetical problem.
4. **The `tags` field isn't split into a "cuisine" dimension.** The most frequent tags (`preparation`, `time-to-make`, `course`, `main-ingredient`, `dietary`, `cuisine`, `equipment`, ...) are Food.com's own *category labels*, not the content within those categories — `"cuisine"` appears 91,165 times as a literal tag, not as e.g. `"mexican"` or `"italian"`. A real cuisine-frequency analysis needs to filter down to genuine cuisine values, not take a naive top-N over the whole tag vocabulary.

## Findings that are informational, not blocking

- **0 duplicate recipe IDs, 0 exact duplicate rows, 0 recipes with an internal duplicate ingredient** — the primary key and per-recipe ingredient lists are clean.
- **1,451 duplicate recipe names** (case-insensitive) — expected at this scale from independent contributors; relevant only if name similarity is ever used as a signal.
- **`description` missing in 2.15% of recipes (4,979 rows), `name` missing in 1 row.** Minor; doesn't block current work.
- **Every recipe has at least one interaction** (0 recipes with zero interactions) — no cold-start-from-zero rows in this dataset.
- **Median interactions per recipe is 2; mean rating is 4.35.** Long-tail popularity distribution with likely rating-inflation bias (users mostly rate what they liked). Relevant context for Phase 3 (ML ranking) and for any cold-start discussion.

## Method notes

- Outlier detection uses a generic IQR rule (`Q1/Q3 ± 3x IQR`, wider than the conventional 1.5x) rather than hand-picked domain thresholds — see `analyze_quality.outlier_report()`. This is a starting point, not a final cleaning rule: for a right-skewed field like `minutes`, IQR-based flagging catches a mix of genuinely corrupt values (like the overflow sentinel) and legitimately slow recipes (e.g. multi-day ferments), so the flagged set needs a human look before being turned into a hard filter.
- Full per-field stats (min/p50/p99/max/outlier count) are in the script output, not reproduced here — this file captures conclusions, not raw numbers, so it doesn't go stale if the analysis is re-run with different parameters.
