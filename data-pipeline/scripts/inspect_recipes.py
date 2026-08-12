"""
Exploratory script for eyeballing the parsed recipe dataset.

Uses parse_recipes.process_recipes() rather than re-reading the raw
CSV directly, so it always reflects the current parsing/nutrition
logic instead of drifting out of sync with it.
"""
from pathlib import Path

from parse_recipes import process_recipes

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR.parent / "raw" / "RAW_recipes.csv"

df = process_recipes(DATA_PATH)

print(df.shape)
print(df.columns.tolist())
print(df.head())

print("\nSample nutrition (row 2):")
print(df[["calories", "protein_pdv", "protein_g", "saturated_fat_pdv", "saturated_fat_g"]].iloc[2])
