---
name: mealgraph-pipeline-step
description: Use when implementing the next Phase 1 data-pipeline step for MealGraph (an analysis or transform script under data-pipeline/scripts/). Encodes the project's established workflow so it doesn't need to be re-derived from CONTRIBUTING.md and prior examples each session.
---

# MealGraph data-pipeline step workflow

This is a Food.com recipe recommendation engine built deliberately, phase by
phase (see `MealGraph_Project_Context.md`, gitignored/local-only). Steps 1-3
(nutrition columns, pipeline tests, data-quality analysis) all followed the
same loop, written up in `/CONTRIBUTING.md`. Follow it directly rather than
re-deriving it:

verify assumption against a primary source -> implement -> test -> run
against the real dataset -> document findings -> review full diff with the
user -> user decides when/how to commit.

## Repo-specific conventions

- New analysis/transform logic goes in `data-pipeline/scripts/<name>.py`,
  shaped like `parse_recipes.py`: small pure functions returning data
  (not just printing), plus a `main()` that orchestrates and prints a
  report.
- Load recipe data via `process_recipes()` from `parse_recipes.py` --
  never re-read `RAW_recipes.csv` directly. (`inspect_recipes.py` was
  previously broken because it duplicated that logic instead of reusing it.)
- Tests go in `data-pipeline/scripts/test_<name>.py`, stdlib `unittest`
  only. No test framework dependency has been added -- don't add one
  (e.g. pytest) without surfacing it as an explicit decision first.
- Test pure functions against small synthetic fixtures, not the real
  231K-row CSV. Real-data validation happens by actually running the
  script once, separately from the test suite.
- `requirements.txt` only lists what committed code currently imports --
  don't pre-add a dependency for a phase that hasn't started yet.
- Findings that took real verification work (not just "the script ran")
  get written up in `data-pipeline/<TOPIC>.md`: claim, evidence, what
  still needs follow-up, sources if external. See `NUTRITION_COLUMNS.md`
  and `DATA_QUALITY.md` for the expected shape and tone -- professional,
  no reference to AI-assistance mechanics (this is a public portfolio repo).
- Update `MealGraph_Project_Context.md`'s "Current Project Status"
  section to track phase progress, but it's gitignored -- never include
  it in a commit.
- Flag genuine ambiguity (e.g. "does this field actually contain what
  the roadmap assumed," "which reference value applies here") instead
  of silently picking a default. This user explicitly wants guesses
  surfaced, not presented as fact.
- Before committing: show the full diff and a plain-English "what
  changed and why," and wait for explicit approval. This user sometimes
  runs the actual `git commit` themselves after approving in chat --
  don't be thrown by a rejected commit tool call, just verify real repo
  state with `git log`/`git status` afterward instead of assuming.
