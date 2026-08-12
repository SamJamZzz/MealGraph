"""
Unit tests for analyze_ingredients.py.

Run with: python -m unittest data-pipeline/scripts/test_analyze_ingredients.py
(from the repo root, with the venv activated)
"""
import unittest

import pandas as pd

from analyze_ingredients import (
    flatten_ingredients,
    length_distribution,
    quantity_pattern_rate,
    variant_count,
    vocabulary_size,
    word_membership_rate,
)


class FlattenIngredientsTests(unittest.TestCase):
    def test_flattens_lists_of_lists(self):
        column = pd.Series([["egg", "flour"], ["milk"]])
        self.assertEqual(flatten_ingredients(column), ["egg", "flour", "milk"])


class LengthDistributionTests(unittest.TestCase):
    def test_word_counts(self):
        result = length_distribution(["egg", "all-purpose flour", "chicken breast halves"])
        self.assertEqual(result["min_words"], 1)
        self.assertEqual(result["max_words"], 3)


class QuantityPatternRateTests(unittest.TestCase):
    def test_detects_digits_and_fractions(self):
        strings = ["2 eggs", "salt", "½ cup sugar", "pepper"]
        self.assertEqual(quantity_pattern_rate(strings), 50.0)

    def test_zero_when_no_quantities_present(self):
        strings = ["salt", "pepper", "flour"]
        self.assertEqual(quantity_pattern_rate(strings), 0.0)


class WordMembershipRateTests(unittest.TestCase):
    def test_detects_vocabulary_words(self):
        strings = ["chopped onion", "salt", "minced garlic"]
        rate = word_membership_rate(strings, {"chopped", "minced"})
        self.assertAlmostEqual(rate, 66.667, places=2)


class VocabularySizeTests(unittest.TestCase):
    def test_counts_total_and_unique(self):
        result = vocabulary_size(["salt", "salt", "pepper"])
        self.assertEqual(result["total_ingredient_mentions"], 3)
        self.assertEqual(result["unique_ingredient_strings"], 2)


class VariantCountTests(unittest.TestCase):
    def test_counts_distinct_matches_case_insensitive(self):
        strings = ["garlic", "garlic cloves", "Garlic", "minced garlic", "onion"]
        # "garlic" and "Garlic" case-fold to the same variant; "garlic
        # cloves" and "minced garlic" are two more distinct variants
        self.assertEqual(variant_count(strings, "garlic"), 3)


if __name__ == "__main__":
    unittest.main()
