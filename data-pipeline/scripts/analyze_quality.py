"""
Data-quality analysis for the parsed Food.com recipe dataset.

Investigates: missing values, duplicate recipes/ingredients, outliers
in prep time / ingredient count / calories, ingredient and tag
frequency, and recipe popularity (from RAW_interactions.csv).

See MealGraph_Project_Context.md, Phase 1 Step 3.
"""
from collections import Counter
from pathlib import Path

import pandas as pd

from parse_recipes import process_recipes


def load_interactions(input_path: Path | str) -> pd.DataFrame:
    """Load the raw user-recipe interactions CSV."""
    return pd.read_csv(input_path)


def missing_value_report(df: pd.DataFrame) -> pd.DataFrame:
    """Per-column count and percentage of missing values."""
    missing_count = df.isna().sum()
    missing_pct = (missing_count / len(df) * 100).round(2)
    report = pd.DataFrame({"missing_count": missing_count, "missing_pct": missing_pct})
    return report[report["missing_count"] > 0].sort_values("missing_count", ascending=False)


LIST_TYPED_COLUMNS = ["tags_p", "steps_p", "ingredients_p"]


def duplicate_recipe_report(df: pd.DataFrame) -> dict:
    """
    Counts of exact duplicate rows, duplicate recipe IDs (should be
    zero -- `id` is expected to be a primary key), and duplicate
    recipe names (case-insensitive).

    Exact-duplicate-row detection excludes the parsed list-typed
    columns (LIST_TYPED_COLUMNS): pandas' `duplicated()` requires
    hashable values, and Python lists aren't hashable.
    """
    hashable_df = df.drop(columns=LIST_TYPED_COLUMNS, errors="ignore")
    return {
        "exact_duplicate_rows": int(hashable_df.duplicated().sum()),
        "duplicate_ids": int(df["id"].duplicated().sum()),
        "duplicate_names": int(df["name"].str.lower().str.strip().duplicated().sum()),
    }


def duplicate_ingredient_recipes(df: pd.DataFrame) -> int:
    """Number of recipes that list the same ingredient more than once."""

    def has_internal_duplicate(ingredients: list) -> bool:
        return len(ingredients) != len(set(ingredients))

    return int(df["ingredients_p"].apply(has_internal_duplicate).sum())


def outlier_report(series: pd.Series, iqr_multiplier: float = 3.0) -> dict:
    """
    Generic IQR-based outlier summary for a numeric series.

    Uses a wide multiplier (3.0, vs. the conventional 1.5) since this
    is meant to flag genuinely extreme values worth a human look, not
    every point outside a "typical" box-plot whisker. min/p50/p99/max
    are reported alongside so the threshold's effect stays visible
    rather than hidden behind a single flagged/not-flagged count.
    """
    clean = series.dropna()
    q1, q3 = clean.quantile(0.25), clean.quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - iqr_multiplier * iqr
    upper_bound = q3 + iqr_multiplier * iqr
    outliers = clean[(clean < lower_bound) | (clean > upper_bound)]

    return {
        "min": clean.min(),
        "p50": clean.median(),
        "p99": clean.quantile(0.99),
        "max": clean.max(),
        "outlier_count": int(len(outliers)),
        "outlier_pct": round(len(outliers) / len(clean) * 100, 3),
    }


def value_frequency(list_column: pd.Series, top_n: int = 25) -> pd.Series:
    """Top-N most frequent values across a column of lists (e.g. ingredients or tags)."""
    counts = Counter()
    for values in list_column:
        counts.update(values)
    return pd.Series(dict(counts.most_common(top_n)))


def popularity_report(recipes_df: pd.DataFrame, interactions_df: pd.DataFrame) -> dict:
    """Rating count/mean per recipe, and how many recipes have zero interactions."""
    per_recipe = interactions_df.groupby("recipe_id")["rating"].agg(["count", "mean"])
    recipe_ids = set(recipes_df["id"])
    interacted_ids = set(per_recipe.index)
    zero_interaction_count = len(recipe_ids - interacted_ids)

    return {
        "recipes_with_zero_interactions": zero_interaction_count,
        "recipes_with_zero_interactions_pct": round(
            zero_interaction_count / len(recipe_ids) * 100, 2
        ),
        "median_interactions_per_recipe": per_recipe["count"].median(),
        "mean_rating_overall": round(per_recipe["mean"].mean(), 2),
    }


def print_report(recipes_df: pd.DataFrame, interactions_df: pd.DataFrame) -> None:
    print("\n=== Missing Values ===")
    missing = missing_value_report(recipes_df)
    print(missing if not missing.empty else "None found.")

    print("\n=== Duplicates ===")
    for key, value in duplicate_recipe_report(recipes_df).items():
        print(f"{key}: {value}")
    print(f"recipes_with_internal_duplicate_ingredients: {duplicate_ingredient_recipes(recipes_df)}")

    print("\n=== Outliers (IQR, multiplier=3.0) ===")
    for column in ["minutes", "n_ingredients", "calories"]:
        print(f"\n{column}:")
        for key, value in outlier_report(recipes_df[column]).items():
            print(f"  {key}: {value}")

    print("\n=== Top 15 Ingredients ===")
    print(value_frequency(recipes_df["ingredients_p"], top_n=15))

    print("\n=== Top 15 Tags ===")
    print(value_frequency(recipes_df["tags_p"], top_n=15))

    print("\n=== Recipe Popularity ===")
    for key, value in popularity_report(recipes_df, interactions_df).items():
        print(f"{key}: {value}")


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    recipes_path = base_dir.parent / "raw" / "RAW_recipes.csv"
    interactions_path = base_dir.parent / "raw" / "RAW_interactions.csv"

    recipes_df = process_recipes(recipes_path)
    interactions_df = load_interactions(interactions_path)

    print_report(recipes_df, interactions_df)


if __name__ == "__main__":
    main()
