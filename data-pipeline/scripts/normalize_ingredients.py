"""
Ingredient name normalization -- design validation (Phase 1, Step 5).

Validates a deterministic, safe normalization approach: how much does
stripping known preparation-modifier words alone reduce the raw
ingredient vocabulary, and how concentrated is ingredient usage (does
a curated top-N approach make sense)?

See INGREDIENT_REPRESENTATION.md for why fuzzy/substring-based
grouping is unsafe, and INGREDIENT_NORMALIZATION_DESIGN.md for the
resulting design decision -- including why comma-based splitting and
plural stemming were considered and deliberately NOT implemented here.
"""
from collections import Counter
from pathlib import Path

import pandas as pd

from analyze_ingredients import MODIFIER_WORDS, flatten_ingredients
from parse_recipes import process_recipes


def normalize_ingredient(ingredient: str) -> str:
    """
    Deterministic, safe normalization: lowercase, strip known
    preparation-modifier words (which describe state, not identity --
    see MODIFIER_WORDS), collapse whitespace.

    Does NOT attempt plural stemming or comma-based splitting -- both
    were evaluated and deferred, see module docstring.
    """
    words = [w for w in ingredient.lower().split() if w not in MODIFIER_WORDS]
    return " ".join(words).strip()


def vocabulary_reduction(ingredient_strings: list) -> dict:
    """How much does safe normalization shrink the unique-string count?"""
    raw_unique = len(set(ingredient_strings))
    normalized_unique = len({normalize_ingredient(s) for s in ingredient_strings})
    return {
        "raw_unique_strings": raw_unique,
        "normalized_unique_strings": normalized_unique,
        "reduction_pct": round((1 - normalized_unique / raw_unique) * 100, 2),
    }


def cumulative_coverage(ingredient_strings: list, top_n_values: list) -> dict:
    """What fraction of total mentions do the top-N most frequent raw strings cover?"""
    counts = Counter(ingredient_strings)
    total = sum(counts.values())
    sorted_counts = counts.most_common()

    coverage = {}
    cumulative = 0
    idx = 0
    for n in sorted(top_n_values):
        while idx < n and idx < len(sorted_counts):
            cumulative += sorted_counts[idx][1]
            idx += 1
        coverage[n] = round(cumulative / total * 100, 2)
    return coverage


def comma_pattern_rate(ingredient_strings: list) -> float:
    """Percent of strings containing a comma (checked before designing around it)."""
    matches = sum(1 for s in ingredient_strings if "," in s)
    return round(matches / len(ingredient_strings) * 100, 3)


def print_report(df: pd.DataFrame) -> None:
    ingredient_strings = flatten_ingredients(df["ingredients_p"])

    print("\n=== Comma Pattern (checked before designing around it) ===")
    print(f"strings containing a comma: {comma_pattern_rate(ingredient_strings)}%")

    print("\n=== Vocabulary Reduction from Safe Normalization ===")
    for key, value in vocabulary_reduction(ingredient_strings).items():
        print(f"{key}: {value}")

    print("\n=== Cumulative Coverage by Top-N Raw Strings ===")
    for n, pct in cumulative_coverage(ingredient_strings, [50, 100, 500, 1000, 2000]).items():
        print(f"top {n} raw strings: {pct}% of all mentions")


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    recipes_path = base_dir.parent / "raw" / "RAW_recipes.csv"

    df = process_recipes(recipes_path)
    print_report(df)


if __name__ == "__main__":
    main()
