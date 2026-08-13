# data-pipeline/scripts

Phase 1 (Data Engineering) pipeline and analysis scripts, in dependency/build order. Each `test_<name>.py` sits next to the module it tests (stdlib `unittest`, run via `python -m unittest test_<name>` from this directory).

| Step | Script | Purpose | Depends on |
|---|---|---|---|
| — | `parse_recipes.py` | Core parsing: raw CSV → typed DataFrame with named nutrition columns (PDV + gram/mg). The base module everything else builds on. | — |
| — | `inspect_recipes.py` | Ad hoc exploration of the parsed dataset. | `parse_recipes` |
| 3 | `analyze_quality.py` | Missing values, duplicates, outliers, ingredient/tag frequency, recipe popularity. → `DATA_QUALITY.md` | `parse_recipes` |
| 4 | `analyze_ingredients.py` | Measures raw ingredient string shape (length, embedded quantities/units/modifiers, vocabulary size, variant sprawl). → `INGREDIENT_REPRESENTATION.md` | `parse_recipes` |
| 5 | `normalize_ingredients.py` | Validates the normalization approach: safe modifier-stripping impact, usage concentration, comma-pattern check. → `INGREDIENT_NORMALIZATION_DESIGN.md` | `parse_recipes`, `analyze_ingredients` |
| 6 | `build_ingredient_mapping.py` | Implements normalization: adds `ingredients_normalized`, generates the draft canonical-ingredient mapping for human curation. | `parse_recipes`, `analyze_ingredients`, `normalize_ingredients` |
| 7 | `map_to_usda.py` | Investigates FoodData Central match quality for the curated ingredient list. → `USDA_MAPPING.md` | `parse_recipes`, requires `FDC_API_KEY` in `.env` |

Run any script directly, e.g. `python parse_recipes.py`, from this directory (with the project `.venv` activated). Findings docs live one level up in `data-pipeline/`, not here — this directory is code, not conclusions.
