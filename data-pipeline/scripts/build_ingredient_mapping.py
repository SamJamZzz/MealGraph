"""
Implements ingredient normalization (Phase 1, Step 6).

Applies the validated safe normalization from normalize_ingredients.py
across the full dataset, and generates a DRAFT canonical-mapping table
for the most frequent ingredients for human review. See
INGREDIENT_NORMALIZATION_DESIGN.md for why curation is targeted at the
head of the frequency distribution rather than attempted uniformly
across all 14,942 raw strings.
"""
from collections import Counter
from pathlib import Path

import pandas as pd

from analyze_ingredients import flatten_ingredients
from normalize_ingredients import normalize_ingredient
from parse_recipes import process_recipes


def add_normalized_ingredients(df: pd.DataFrame) -> pd.DataFrame:
    """Add an `ingredients_normalized` column: each recipe's ingredients_p, normalized."""
    df = df.copy()
    df["ingredients_normalized"] = df["ingredients_p"].apply(
        lambda ingredients: [normalize_ingredient(i) for i in ingredients]
    )
    return df


def build_draft_mapping(ingredient_strings: list, top_n: int = 1000) -> pd.DataFrame:
    """
    Draft canonical-mapping table for the top-N most frequent raw
    ingredient strings: raw string, frequency, and an automated
    normalized form as a starting guess for `canonical_name`.

    This is a STARTING POINT for human curation, not a finished
    mapping. `reviewed` defaults to False for every row -- the
    automated normalized form is frequently still not the true
    canonical ingredient name (safe stripping alone only reduced the
    vocabulary by 5.58%, see INGREDIENT_NORMALIZATION_DESIGN.md), so
    nothing here should be treated as ground truth until a human sets
    `reviewed=True` after checking `canonical_name`.
    """
    counts = Counter(ingredient_strings)
    top = counts.most_common(top_n)

    rows = [
        {
            "raw_string": raw,
            "frequency": freq,
            "canonical_name": normalize_ingredient(raw),
            "reviewed": False,
        }
        for raw, freq in top
    ]
    return pd.DataFrame(rows)


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    recipes_path = base_dir.parent / "raw" / "RAW_recipes.csv"
    processed_dir = base_dir.parent / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    df = process_recipes(recipes_path)
    df = add_normalized_ingredients(df)

    ingredient_strings = flatten_ingredients(df["ingredients_p"])
    mapping_df = build_draft_mapping(ingredient_strings, top_n=1000)

    mapping_path = processed_dir / "ingredient_mapping_draft.csv"
    mapping_df.to_csv(mapping_path, index=False)

    recipes_output_path = processed_dir / "recipes_parsed.csv"
    df.to_csv(recipes_output_path, index=False)

    print(f"Added ingredients_normalized column to {len(df)} recipes")
    print(f"Draft mapping for top {len(mapping_df)} ingredients saved to {mapping_path}")
    print(f"  {int(mapping_df['reviewed'].sum())} of {len(mapping_df)} entries reviewed (0 expected -- needs human curation)")
    print(f"Updated processed dataset saved to {recipes_output_path}")


if __name__ == "__main__":
    main()
