# Ingredient representation findings

**Status:** generated from `analyze_ingredients.py` against the full dataset (231,637 recipes, 2,096,582 ingredient mentions) on 2026-08-12. Phase 1, Step 4.

## Correction to the roadmap's assumption

`MealGraph_Project_Context.md`'s Step 4/5 description illustrates normalization with examples like `"2 boneless skinless chicken breasts"` and `"1/2 tsp salt"` — implying the raw ingredient text mixes quantity, unit, and ingredient name together. **That's not what this dataset's `ingredients` field actually contains.**

Measured directly:
- Only **0.148%** of ingredient strings contain any digit or fraction glyph.
- Only **2.1%** contain a common unit word (cup, tsp, oz, clove, etc.).

Real entries look like: `['winter squash', 'mexican seasoning', 'mixed spice', 'honey', 'butter', 'olive oil', 'salt']` — bare ingredient names. Median length is 2 words, 99th percentile is 4 words.

**Implication:** normalization here is primarily a **name-canonicalization / deduplication problem** — collapsing many raw string variants into fewer real ingredients — not a quantity/unit-extraction problem. Step 5's design should start from that, not from the roadmap's illustrative (and, for this dataset, inaccurate) example.

## Scope of the normalization problem

- 2,096,582 total ingredient mentions across all recipes.
- Only **14,942 unique raw ingredient strings**. That's the actual target size for canonicalization.
- 9.87% of strings contain an embedded preparation-modifier word (chopped, minced, diced, fresh, ground, etc.) — real signal that could be split out as a separate field, but a minority of entries, not the norm.

## Variant sprawl — and a real trap to avoid

Counting distinct raw strings containing a given keyword:

| Keyword | Distinct strings |
|---|---|
| pepper | 440 |
| chicken | 372 |
| sugar | 345 |
| garlic | 212 |
| onion | 205 |
| flour | 168 |
| salt | 189 |

**These numbers mix two different phenomena, and treating them the same would produce wrong normalization:**
1. **True formatting duplicates of the same ingredient** — e.g. `"garlic"` vs. `"garlic cloves"` vs. `"minced garlic"` all mean garlic.
2. **Genuinely different ingredients that happen to share a word** — e.g. `"chicken breast"`, `"chicken broth"`, and `"chicken thigh"` all match `"chicken"` but are not interchangeable, and `"bell pepper"` (a vegetable) and `"black pepper"` (a spice) both match `"pepper"` but are unrelated foods.

A normalization approach based on naive substring/keyword overlap would silently merge case (2) into case (1) and produce incorrect ingredient groupings. Step 5's design needs a way to distinguish "same ingredient, different phrasing" from "different ingredient, shared word" — not just string similarity.

## Not yet answered (deferred to Step 5 design)

- How to reliably separate the ~10% of entries with embedded modifiers from the ~90% without, and whether that's worth doing before or after canonicalization.
- What method actually distinguishes formatting variants from genuinely different foods (e.g. head-word/last-word heuristics, a curated ingredient ontology, or matching against USDA FoodData Central search results directly, since ingredient-to-USDA mapping is Step 7 regardless).
