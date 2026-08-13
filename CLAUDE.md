# MealGraph

Personalized meal and nutrition optimization engine, built on the Food.com Recipes and Interactions dataset (231,637 recipes, ~1.3M interactions). See `README.md` for the product overview.

## Current status

**Phase 1 (Data Engineering) is complete.** Phase 2 (deterministic recommendation baseline — pantry overlap, nutrition fit, prep-time scoring, built before any ML) is next.

## Where things live

- `README.md` — public project overview and setup instructions.
- `CONTRIBUTING.md` — the development workflow this project follows: verify assumptions against a source → implement → test → run against real data → document findings → review before commit.
- `data-pipeline/scripts/` — pipeline code. Start with `data-pipeline/scripts/README.md`, which indexes every script by phase step and dependency order.
- `data-pipeline/*.md` — findings docs, one per topic, each self-contained (claim, evidence, decision, sources): `NUTRITION_COLUMNS.md`, `DATA_QUALITY.md`, `INGREDIENT_REPRESENTATION.md`, `INGREDIENT_NORMALIZATION_DESIGN.md`, `DATABASE_SCHEMA_DESIGN.md`, `USDA_MAPPING.md`.
- `.claude/skills/mealgraph-pipeline-step/` — the workflow above, encoded as a skill so it doesn't need re-deriving each session. Scoped to data-pipeline analysis/transform work (Phase 1's pattern); Phase 2 is a different kind of task and doesn't have a skill yet.
- `MealGraph_Project_Context.md` — detailed phase-by-phase status and roadmap. **Local-only (gitignored)** — read it if present for full history, but don't expect it on a fresh clone.

## Quick facts

- Python 3.11, virtualenv at `.venv/`. Activate with `source .venv/bin/activate`.
- Tests are stdlib `unittest`, no test framework dependency. Run the full suite from `data-pipeline/scripts/`: `python -m unittest discover -p "test_*.py"`.
- `requirements.txt` only lists what committed code currently imports — dependencies get added in the commit that starts using them, not pre-declared for future phases.
- Raw and processed data files are gitignored (`data-pipeline/raw/`, `data-pipeline/processed/`) — regenerate via the scripts, don't expect them to be present in git.
- `map_to_usda.py` needs `FDC_API_KEY` in a local `.env` (gitignored, never commit it).
