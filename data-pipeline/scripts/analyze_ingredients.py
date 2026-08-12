"""
Analyzes the raw shape of ingredient strings in the Food.com dataset,
to inform ingredient normalization design (Phase 1, Step 5).

See MealGraph_Project_Context.md, Phase 1 Step 4.
"""
import re
from pathlib import Path

import pandas as pd

from parse_recipes import process_recipes

QUANTITY_PATTERN = re.compile(r"[0-9½¼¾⅓⅔]")

UNIT_WORDS = {
    "cup", "cups", "tsp", "tbsp", "teaspoon", "teaspoons", "tablespoon",
    "tablespoons", "oz", "ounce", "ounces", "lb", "lbs", "pound", "pounds",
    "gram", "grams", "g", "kg", "ml", "liter", "litre", "clove", "cloves",
    "slice", "slices", "can", "cans", "package", "packages", "pinch",
    "dash", "quart", "quarts", "pint", "pints", "gallon", "gallons",
}

MODIFIER_WORDS = {
    "chopped", "minced", "diced", "sliced", "grated", "shredded", "fresh",
    "dried", "ground", "boneless", "skinless", "cooked", "raw", "large",
    "small", "medium", "melted", "softened", "peeled", "crushed", "beaten",
    "packed", "finely", "coarsely", "thinly",
}

VARIANT_SPRAWL_KEYWORDS = ["garlic", "onion", "chicken", "salt", "flour", "sugar", "pepper"]


def flatten_ingredients(ingredients_column: pd.Series) -> list[str]:
    """Flatten the per-recipe ingredient lists into one list of strings."""
    flattened = []
    for ingredients in ingredients_column:
        flattened.extend(ingredients)
    return flattened


def length_distribution(ingredient_strings: list[str]) -> dict:
    """Word-count distribution across all ingredient strings."""
    word_counts = pd.Series([len(s.split()) for s in ingredient_strings])
    return {
        "min_words": int(word_counts.min()),
        "p50_words": float(word_counts.median()),
        "p99_words": float(word_counts.quantile(0.99)),
        "max_words": int(word_counts.max()),
    }


def quantity_pattern_rate(ingredient_strings: list[str]) -> float:
    """Percent of ingredient strings containing a digit or a fraction glyph."""
    matches = sum(1 for s in ingredient_strings if QUANTITY_PATTERN.search(s))
    return round(matches / len(ingredient_strings) * 100, 3)


def word_membership_rate(ingredient_strings: list[str], vocabulary: set) -> float:
    """Percent of ingredient strings containing at least one word from `vocabulary`."""
    matches = 0
    for s in ingredient_strings:
        words = set(s.lower().split())
        if words & vocabulary:
            matches += 1
    return round(matches / len(ingredient_strings) * 100, 3)


def vocabulary_size(ingredient_strings: list[str]) -> dict:
    """Total vs. unique ingredient string counts."""
    return {
        "total_ingredient_mentions": len(ingredient_strings),
        "unique_ingredient_strings": len(set(ingredient_strings)),
    }


def variant_count(ingredient_strings: list[str], keyword: str) -> int:
    """
    Number of distinct ingredient strings containing `keyword` as a
    substring. Case-folded for the dedup: "Garlic" and "garlic" are the
    same variant for this purpose, not two different ones.
    """
    return len({s.lower() for s in ingredient_strings if keyword in s.lower()})


def print_report(df: pd.DataFrame) -> None:
    ingredient_strings = flatten_ingredients(df["ingredients_p"])

    print("\n=== Sample raw ingredient strings (first recipe) ===")
    print(df["ingredients_p"].iloc[0])

    print("\n=== Ingredient String Length (words) ===")
    for key, value in length_distribution(ingredient_strings).items():
        print(f"{key}: {value}")

    print("\n=== Embedded Quantity Pattern ===")
    print(f"strings containing a digit/fraction glyph: {quantity_pattern_rate(ingredient_strings)}%")

    print("\n=== Embedded Unit Words ===")
    print(f"strings containing a unit word: {word_membership_rate(ingredient_strings, UNIT_WORDS)}%")

    print("\n=== Embedded Preparation Modifiers ===")
    print(f"strings containing a modifier word: {word_membership_rate(ingredient_strings, MODIFIER_WORDS)}%")

    print("\n=== Vocabulary Size ===")
    for key, value in vocabulary_size(ingredient_strings).items():
        print(f"{key}: {value}")

    print("\n=== Variant Sprawl (example keywords) ===")
    for keyword in VARIANT_SPRAWL_KEYWORDS:
        print(f"'{keyword}': {variant_count(ingredient_strings, keyword)} distinct strings")


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    recipes_path = base_dir.parent / "raw" / "RAW_recipes.csv"

    df = process_recipes(recipes_path)
    print_report(df)


if __name__ == "__main__":
    main()
