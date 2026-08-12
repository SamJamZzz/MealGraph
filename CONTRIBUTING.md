# Development workflow

This project follows the same loop for each unit of work, regardless of which phase it's in:

1. **Verify assumptions against a primary source before building on them.** If a data field, API contract, or library behavior isn't already confirmed, check it against documentation or the actual data before writing code that depends on it — don't assume a "commonly cited" answer is correct for this specific case.
2. **Document non-obvious findings near the code they govern**, not just in commit messages. See `data-pipeline/NUTRITION_COLUMNS.md` for an example: verified semantics, sources, and an explicit list of what's exact vs. estimated.
3. **Flag genuine ambiguity instead of picking a default silently.** If a design decision depends on an unverifiable assumption (e.g. which reference table a third-party dataset used), say so explicitly rather than presenting a guess as fact.
4. **Implement with tests before moving to the next unit of work**, not after several units have piled up.
5. **Validate against the full real dataset**, not just a synthetic fixture, before considering a change done — unit tests catch logic errors, but only a real run catches scale/format issues.
6. **Review the complete diff before committing.** Incidental findings (bugs, stale docs, dependency drift) get called out and fixed in the same pass rather than filed away for later.
7. **Keep internal working notes separate from public-facing documentation.** Planning/roadmap material stays local; committed docs describe verified state and decisions.

Dependencies are added in the commit that starts actually using them, not pre-declared for planned-but-unbuilt phases — see the comment at the top of `requirements.txt`.
