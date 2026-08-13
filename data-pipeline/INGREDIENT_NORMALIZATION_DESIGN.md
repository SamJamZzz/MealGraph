# Ingredient normalization — design (Phase 1, Step 5)

**Status:** design validated with real measurements from `normalize_ingredients.py`, 2026-08-12. Builds on `INGREDIENT_REPRESENTATION.md` (Step 4).

## What was tested, and what it showed

**Safe modifier-stripping alone is not sufficient.** Stripping known preparation-modifier words (chopped, minced, fresh, ground, etc. — the same `MODIFIER_WORDS` set from Step 4, chosen because those words describe preparation state, not ingredient identity, so stripping them can't turn one ingredient into a different one) reduces the raw vocabulary from **14,942 to 14,108 unique strings — only a 5.58% reduction.** Most of the sprawl identified in Step 4 isn't caused by prep-modifier words; it's word order, unit words ("cloves"), plurals, and alternate spellings. This rules out "strip a stopword list and call it normalized" as an adequate solution by itself.

**Ingredient usage is heavily concentrated (Zipfian).** The top 50 raw strings cover 40.8% of all 2.1M ingredient mentions; top 500 cover 77.1%; top 1000 cover 86.0%; top 2000 cover 92.9%.

**Comma-based splitting was considered and rejected.** Only 0.34% of strings contain a comma at all, and the pattern found (`"lemon, juice of"`, `"orange, zest of"`) isn't even the "ingredient, modifier" shape that would have justified comma-splitting logic. Checked before writing any comma-handling code, not assumed.

## Design decision

Given the concentration numbers, the highest-leverage approach isn't a single clever algorithm applied uniformly — it's separating the problem by frequency:

1. **Apply safe modifier-stripping universally.** Cheap, zero-risk, still worth doing even though its impact alone is small — it's a strict subset of what any further curation would need to handle anyway.
2. **Hand-curate a canonical mapping for the ~500–1000 most frequent (post-stripping) raw strings.** This is a bounded, reviewable amount of work that covers 77–86% of actual ingredient usage — a much better return than trying to algorithmically resolve all 14,942 unique strings at once. This is also a legitimate "understand your own data" exercise rather than something to fully automate.
3. **Defer the long tail** (~13,000+ strings covering only ~14% of usage) rather than building bespoke fuzzy-matching logic to chase diminishing returns. The planned USDA FoodData Central mapping (Phase 1 Step 7) already needs to match ingredient strings against an external food database — it's a more natural place to resolve rare/unusual raw strings than a standalone normalization layer built now.

## Explicitly rejected approaches

- **Naive substring/keyword grouping** (e.g. merge every string containing `"chicken"`) — confirmed unsafe in Step 4: it would merge genuinely different ingredients that share a word (`"chicken breast"` vs. `"chicken broth"`).
- **Full automated fuzzy-matching/clustering across all 14,942 strings** — not ruled out forever, but not justified yet: the concentration data shows a much cheaper approach (curate the head) captures most of the value first.

## Implementation (Step 6 — `build_ingredient_mapping.py`)

- `ingredients_normalized` column added to the processed dataset: each recipe's `ingredients_p` list with safe modifier-stripping applied per-item. Kept alongside `ingredients_p` (not replacing it) — the raw form is still needed as the join key back to the original data.
- `ingredient_mapping_draft.csv` generated in `data-pipeline/processed/` (gitignored — it's a working artifact, not a finished dataset): the top 1,000 raw ingredient strings by frequency, each with an automated `canonical_name` guess and a `reviewed` boolean defaulting to `False` for every row.
- **This mapping is explicitly a draft, not a finished result.** Spot-checking the top of the real output confirms the Step 5 finding directly: `garlic` (18,087 mentions) and `garlic cloves` (25,748 mentions) remain two separate rows, as do `egg` (17,304) and `eggs` (33,761) — both cases the automated pass can't resolve (plural handling and unit-word stripping beyond the safe modifier list were both explicitly deferred, not silently solved). Turning this into a real canonical mapping needs a human to fill in `canonical_name` correctly and flip `reviewed=True` — that review has not happened yet.
