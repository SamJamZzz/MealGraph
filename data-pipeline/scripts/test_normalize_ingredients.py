"""
Unit tests for normalize_ingredients.py.

Run with: python -m unittest data-pipeline/scripts/test_normalize_ingredients.py
(from the repo root, with the venv activated)
"""
import unittest

from normalize_ingredients import (
    comma_pattern_rate,
    cumulative_coverage,
    normalize_ingredient,
    vocabulary_reduction,
)


class NormalizeIngredientTests(unittest.TestCase):
    def test_strips_known_modifier_words(self):
        self.assertEqual(normalize_ingredient("chopped onion"), "onion")
        self.assertEqual(normalize_ingredient("fresh minced garlic"), "garlic")

    def test_lowercases(self):
        self.assertEqual(normalize_ingredient("Salt"), "salt")

    def test_leaves_identity_words_untouched(self):
        # "breast" and "broth" are not modifier words -- stripping them
        # would conflate genuinely different ingredients.
        self.assertEqual(normalize_ingredient("chicken breast"), "chicken breast")
        self.assertEqual(normalize_ingredient("chicken broth"), "chicken broth")

    def test_no_modifiers_present_is_unchanged(self):
        self.assertEqual(normalize_ingredient("olive oil"), "olive oil")


class VocabularyReductionTests(unittest.TestCase):
    def test_merges_strings_that_differ_only_by_modifier(self):
        strings = ["chopped onion", "onion", "fresh onion"]
        result = vocabulary_reduction(strings)
        self.assertEqual(result["raw_unique_strings"], 3)
        self.assertEqual(result["normalized_unique_strings"], 1)

    def test_does_not_merge_genuinely_different_ingredients(self):
        strings = ["chicken breast", "chicken broth"]
        result = vocabulary_reduction(strings)
        self.assertEqual(result["normalized_unique_strings"], 2)


class CumulativeCoverageTests(unittest.TestCase):
    def test_top_n_coverage(self):
        # "salt" x3, "pepper" x2, "sugar" x1 -- total 6 mentions
        strings = ["salt", "salt", "salt", "pepper", "pepper", "sugar"]
        result = cumulative_coverage(strings, [1, 2, 3])
        self.assertAlmostEqual(result[1], 50.0)  # "salt" alone = 3/6
        self.assertAlmostEqual(result[2], 83.33, places=1)  # + "pepper" = 5/6
        self.assertAlmostEqual(result[3], 100.0)  # + "sugar" = 6/6


class CommaPatternRateTests(unittest.TestCase):
    def test_detects_commas(self):
        strings = ["lemon, juice of", "salt", "pepper"]
        self.assertAlmostEqual(comma_pattern_rate(strings), 33.333, places=2)


if __name__ == "__main__":
    unittest.main()
