"""
Parses raw Food.com recipe data into a clean, typed DataFrame.

Nutrition column semantics (order, units, and the PDV->gram conversion
assumptions) are verified and documented in ../NUTRITION_COLUMNS.md.
"""
import ast
from pathlib import Path
from typing import Any

import pandas as pd


RAW_LIST_COLUMNS = ["tags", "steps", "ingredients"]
RAW_NUTRITION_COLUMN = "nutrition"

# Order of the raw `nutrition` list, per source documentation.
# Only `calories` is absolute; the rest are % daily value (PDV).
NUTRITION_FIELDS = [
    "calories",
    "total_fat_pdv",
    "sugar_pdv",
    "sodium_pdv",
    "protein_pdv",
    "saturated_fat_pdv",
    "carbohydrates_pdv",
]

# FDA reference daily values used to convert PDV -> grams/mg.
# Maps output column -> (source PDV column, daily value reference).
#
# protein_g and saturated_fat_g are EXACT: their daily value (50g / 20g)
# is identical under both the pre-2016 and 2016+ FDA label rules.
# sodium_mg uses the pre-2016 reference (2400mg vs 2300mg, ~4% spread).
# total_fat_g, carbohydrates_g, and sugar_g are ESTIMATES: their daily
# value reference differs meaningfully between label eras (fat: 65g vs
# 78g, carbs: 300g vs 275g) and Food.com's exact calculation method
# isn't published anywhere we could verify. Treat these three as
# approximate until ingredient-level USDA FoodData Central mapping
# (see MealGraph_Project_Context.md, Phase 1 Step 5) provides
# ground-truth nutrition.
DAILY_VALUES = {
    "protein_g": ("protein_pdv", 50),
    "saturated_fat_g": ("saturated_fat_pdv", 20),
    "sodium_mg": ("sodium_pdv", 2400),
    "total_fat_g": ("total_fat_pdv", 65),
    "carbohydrates_g": ("carbohydrates_pdv", 300),
    "sugar_g": ("sugar_pdv", 50),
}

ESTIMATED_GRAM_COLUMNS = {"total_fat_g", "carbohydrates_g", "sugar_g"}


def parse_list_string(value: Any, default: Any = None) -> Any:
    """
    Safely parse a string that looks like a Python literal list.

    Examples:
        "['onion', 'garlic']" -> ['onion', 'garlic']
        "[1.0, 2.0, 3.0]" -> [1.0, 2.0, 3.0]

    Returns `default` if parsing fails.
    """
    if default is None:
        default = []

    if isinstance(value, list):
        return value

    if pd.isna(value):
        return default

    if not isinstance(value, str):
        return default

    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return default


def expand_nutrition(nutrition_list: Any) -> pd.Series:
    """
    Expand a parsed nutrition list into named PDV/calorie fields.

    Returns NA for every field if the input isn't a list of the
    expected length, rather than guessing at a partial mapping.
    """
    if not isinstance(nutrition_list, list) or len(nutrition_list) != len(NUTRITION_FIELDS):
        return pd.Series({field: pd.NA for field in NUTRITION_FIELDS})

    return pd.Series(dict(zip(NUTRITION_FIELDS, nutrition_list)))


def compute_gram_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add gram/mg nutrition columns computed from the PDV columns.

    Requires df to already contain the *_pdv columns from
    `expand_nutrition`. See DAILY_VALUES for which conversions are
    exact vs. estimated.
    """
    df = df.copy()
    for gram_column, (pdv_column, daily_value) in DAILY_VALUES.items():
        df[gram_column] = (df[pdv_column] / 100) * daily_value
    return df


def process_recipes(input_path: Path | str) -> pd.DataFrame:
    """
    Load raw recipes CSV and return a DataFrame with parsed columns added.
    """
    df = pd.read_csv(input_path)

    for column in RAW_LIST_COLUMNS:
        df[f"{column}_p"] = df[column].apply(lambda x: parse_list_string(x, default=[]))

    nutrition_lists = df[RAW_NUTRITION_COLUMN].apply(
        lambda x: parse_list_string(x, default=None)
    )
    nutrition_fields = nutrition_lists.apply(expand_nutrition)
    df = pd.concat([df, nutrition_fields], axis=1)
    df = compute_gram_columns(df)

    return df


def validate_parsed_columns(df: pd.DataFrame) -> None:
    """
    Print basic validation information for parsed columns.
    """
    print("\n=== Parsed Column Validation ===")

    for column in ["tags_p", "steps_p", "ingredients_p"]:
        invalid_count = df[column].apply(lambda x: not isinstance(x, list)).sum()
        print(f"{column}: invalid non-list rows = {invalid_count}")

    nutrition_missing_count = df[NUTRITION_FIELDS].isna().any(axis=1).sum()
    print(f"nutrition fields: missing/malformed rows = {nutrition_missing_count}")


def print_sample_recipe(df: pd.DataFrame, row_index: int = 0) -> None:
    """
    Print one parsed recipe in a readable format.
    """
    row = df.iloc[row_index]

    print("\n=== Sample Parsed Recipe ===")
    print(f"Name: {row['name']}")
    print(f"Recipe ID: {row['id']}")
    print(f"Minutes: {row['minutes']}")
    print(f"Ingredient count: {row['n_ingredients']}")

    print("\nIngredients (parsed):")
    print(row["ingredients_p"])

    print("\nFirst 3 steps (parsed):")
    print(row["steps_p"][:3] if isinstance(row["steps_p"], list) else row["steps_p"])

    print("\nTags (first 10):")
    print(row["tags_p"][:10] if isinstance(row["tags_p"], list) else row["tags_p"])

    print("\nNutrition (PDV fields):")
    for field in NUTRITION_FIELDS:
        print(f"  {field}: {row[field]}")

    print("\nNutrition (gram/mg fields):")
    for gram_column in DAILY_VALUES:
        marker = " (estimate)" if gram_column in ESTIMATED_GRAM_COLUMNS else ""
        print(f"  {gram_column}: {row[gram_column]:.1f}{marker}")


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    input_path = base_dir.parent / "raw" / "RAW_recipes.csv"
    output_path = base_dir.parent / "processed" / "recipes_parsed.csv"

    df = process_recipes(input_path)

    print("Loaded dataframe shape:", df.shape)
    validate_parsed_columns(df)
    print_sample_recipe(df, row_index=0)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"\nSaved processed dataset to {output_path}")


if __name__ == "__main__":
    main()
