# `nutrition` column — verified semantics

**Status:** verified against source documentation (2026-08-12). Supersedes the "must be verified" note in `MealGraph_Project_Context.md` §10/§19.

## Order and units

The `nutrition` field in `RAW_recipes.csv` is a 7-element list:

| Index | Field | Unit |
|---|---|---|
| 0 | calories | absolute (kcal) |
| 1 | total fat | PDV (% daily value) |
| 2 | sugar | PDV |
| 3 | sodium | PDV |
| 4 | protein | PDV |
| 5 | saturated fat | PDV |
| 6 | carbohydrates | PDV |

**Only index 0 (calories) is an absolute number.** Indices 1–6 are PDV — percentage of FDA daily reference value, not grams.

## Sanity check against local data

Row 2 of `RAW_recipes.csv` ("arriba baked winter squash mexican style"):
`nutrition = [51.5, 0.0, 13.0, 0.0, 2.0, 0.0, 4.0]`
→ 51.5 kcal, 0% fat DV, 13% sugar DV, 0% sodium DV, 2% protein DV, 0% sat-fat DV, 4% carb DV.
Consistent with a low-calorie side/appetizer-sized recipe — passes basic plausibility check.

## Implementation (Step 2 — `parse_recipes.py`)

Named PDV columns replace the raw `nutrition_p` list column: `calories`, `total_fat_pdv`, `sugar_pdv`, `sodium_pdv`, `protein_pdv`, `saturated_fat_pdv`, `carbohydrates_pdv`.

Gram/mg columns are additionally computed for user-facing display, since PDV percentages aren't directly meaningful to end users. Two FDA daily-value label eras exist (pre-2016 and 2016+) and Food.com's exact reference table isn't published, so the conversions are **not equally trustworthy**:

| Column | Daily value used | Confidence |
|---|---|---|
| `protein_g` | 50g | **Exact** — identical in both FDA label eras |
| `saturated_fat_g` | 20g | **Exact** — identical in both FDA label eras |
| `sodium_mg` | 2400mg (pre-2016) | High — only ~4% spread vs. the 2016+ value (2300mg) |
| `total_fat_g` | 65g (pre-2016) | **Estimate** — ~17% spread vs. the 2016+ value (78g) |
| `carbohydrates_g` | 300g (pre-2016) | **Estimate** — ~9% spread vs. the 2016+ value (275g) |
| `sugar_g` | 50g | **Estimate** — sugar had no official %DV before the 2016 rule; 50g is the commonly-assumed convention, not a verified fact |

The pre-2016 table was chosen as the default assumption since it matches the era this dataset was scraped in, but `total_fat_g`, `carbohydrates_g`, and `sugar_g` should be treated as approximations, not ground truth, anywhere they're surfaced. `DAILY_VALUES` and `ESTIMATED_GRAM_COLUMNS` in `parse_recipes.py` are the source of truth for which columns carry this caveat.

**Decision:** stayed on this dataset rather than switching, since the interaction/rating data (700K+ real user interactions) is the more valuable and harder-to-replace asset for the recommendation-system phases of this project. The real fix for nutrition precision is ingredient-level USDA FoodData Central mapping (`MealGraph_Project_Context.md`, Phase 1 Step 5), which gives exact gram values computed from actual ingredient quantities — not a back-solved percentage. These PDV-derived estimates are a placeholder until that phase.

## Sources

- [practicaldsc.org — Recipes and Ratings dataset docs](https://practicaldsc.org/final-project/datasets/recipes-and-ratings/) — direct quote: `'nutrition' — Nutrition information in the form [calories (#), total fat (PDV), sugar (PDV), sodium (PDV), protein (PDV), saturated fat (PDV), carbohydrates (PDV)]; PDV stands for "percentage of daily value"`
- [Kaggle — Food.com Recipes and Interactions](https://www.kaggle.com/datasets/shuyangli94/food-com-recipes-and-user-interactions) (original dataset page; traces to Majumder et al., "Generating Personalized Recipes from Historical User Preferences," EMNLP-IJCNLP 2019)
