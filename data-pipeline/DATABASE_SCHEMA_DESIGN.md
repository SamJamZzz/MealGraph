# Database schema design (Phase 1, Step 8)

**Status:** design only — no database is built yet. This is deliberately still Phase 1 output: Phase 5 (PostgreSQL implementation) comes after Phases 2–4 per the project's stated build order. This doc exists so that schema decisions are made once, thoughtfully, rather than improvised when Phase 5 starts.

This design departs from the original table sketch in `MealGraph_Project_Context.md` §12 in a few places, each justified by something concrete learned during Phase 1 — not a redesign for its own sake.

## Tables

```
recipes
  id                    PK, int (matches Food.com raw id)
  name                  text
  contributor_id        int
  submitted             date
  description           text, nullable            -- 2.15% of recipes have none (DATA_QUALITY.md)
  n_steps               int
  steps                 text[] or JSONB            -- ordered instruction list
  n_ingredients         int                        -- denormalized count, avoids a join for a near-universal read

  minutes                int
  minutes_suspect        bool                       -- flags outliers incl. the int32-overflow sentinel (DATA_QUALITY.md)

  calories                numeric
  total_fat_pdv, sugar_pdv, sodium_pdv,
  protein_pdv, saturated_fat_pdv,
  carbohydrates_pdv       numeric                   -- exact, as scraped (NUTRITION_COLUMNS.md)
  protein_g, saturated_fat_g, sodium_mg  numeric     -- EXACT gram/mg conversions
  total_fat_g, carbohydrates_g, sugar_g  numeric     -- ESTIMATED gram conversions
  nutrition_estimated     bool                       -- true while the three estimated fields are DV-based guesses,
                                                       -- not USDA-derived; flips false once Step 7 supplies ground truth
  calories_suspect        bool                       -- flags the calorie outlier from DATA_QUALITY.md

tags
  id            PK
  name          text, unique

recipe_tags
  recipe_id     FK -> recipes.id
  tag_id        FK -> tags.id
  PRIMARY KEY (recipe_id, tag_id)

canonical_ingredients
  id                      PK
  canonical_name          text, unique
  fdc_id                  int, nullable             -- USDA FoodData Central id, populated in Step 7
  fdc_match_confidence     numeric, nullable          -- 0-1; mapping "will not always be perfect" (roadmap)

ingredient_aliases
  raw_string               PK, text                  -- exact string as scraped from Food.com
  canonical_ingredient_id  FK -> canonical_ingredients.id
  reviewed                 bool                       -- carries forward ingredient_mapping_draft.csv's reviewed flag

recipe_ingredients
  recipe_id                 FK -> recipes.id
  canonical_ingredient_id   FK -> canonical_ingredients.id
  raw_text                  text                      -- original as-written string for this recipe
  PRIMARY KEY (recipe_id, canonical_ingredient_id)

users
  id            PK (matches Food.com raw user_id)

interactions
  id              PK
  user_id         FK -> users.id
  recipe_id       FK -> recipes.id
  rating          smallint
  review          text, nullable
  interacted_at   date
```

## Design decisions, and why

**Nutrition is embedded in `recipes`, not a separate `nutrition` table** (the roadmap's original sketch listed one). It's a strict 1:1 relationship — every recipe has exactly one nutrition profile — and nutrition is needed on almost every recipe read (list view, detail view, ranking). A separate table would just add a mandatory join with no normalization benefit. Column names carry straight over from the pipeline code (`_pdv`, `_g`, `_mg`) rather than being renamed for the schema.

**Data-quality flags are first-class columns, not silent cleanup.** `minutes_suspect`, `calories_suspect`, and `nutrition_estimated` preserve the actual scraped values and make their reliability visible, instead of nulling or deleting data at the database layer. Whether Phase 2's scoring logic excludes, caps, or median-imputes suspect values is a ranking-design decision, not a data-engineering one — the schema shouldn't make that call in advance.

**Ingredients are two-level: `canonical_ingredients` + `ingredient_aliases`.** This directly reflects the Step 5/6 finding that many raw strings map to few real ingredients, and that the mapping itself is a curated, reviewable asset — not a one-time throwaway transform. `reviewed` carries forward from `ingredient_mapping_draft.csv` so an incomplete curation pass is visible in the schema, not silently assumed complete. `recipe_ingredients` joins against the *canonical* ingredient, not the raw string — that's what actually makes pantry-matching (the core product feature) work against a normalized ingredient set instead of noisy raw text.

**Tags are normalized into `tags` + `recipe_tags`, not kept as an array.** Step 3 found that Food.com's tag vocabulary mixes generic category labels (`course`, `cuisine`, `dietary`) with actual content tags in one flat list (DATA_QUALITY.md). A normalized table doesn't fix that ambiguity by itself, but it's a better foundation for filtering/analytics than an unindexed array, and leaves room to add a `category` dimension later if the course/cuisine/dietary split ever gets resolved.

**No vector/embedding column yet.** Explicitly deferred — the roadmap already says to add pgvector "later when semantic retrieval becomes necessary" (Phase 9), and there's no retrieval feature yet that needs it.

## Open for Phase 5

- Exact PostgreSQL types (numeric precision, text vs. varchar, JSONB vs. array for `steps`).
- Indexing strategy — deferred until real query patterns exist from Phase 2/4.
- Whether `ingredient_aliases.raw_string` as a natural-language primary key is worth a surrogate key instead — low risk either way at this scale, revisit if it becomes awkward.
