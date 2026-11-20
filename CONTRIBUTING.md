# Contributing

The scorecard is only as good as its test cases. Native speakers of Indian languages are the most
valuable contributors.

## Propose or review cases

1. Open an issue titled `case: <language> <task>` with the user message as a real person would type it
   (typos, slang and mixed script are welcome), the passage if any, and the right answer.
2. Or edit `cases/<lang>.jsonl` directly in a pull request. Each line follows `cases/schema.json`.
   `tools/validate_cases.py` runs on every PR and fails on schema errors or duplicates.
3. Reviewing a drafted case: fix anything unnatural, then set `"reviewed_by"` to your handle. Reviewers
   are credited on the site.

Rules: write from scratch or from public government pages; never copy from other benchmarks; no real
people's personal details.

## Add a language

Add `cases/<code>.jsonl` with 10 cases for each of the 6 tasks, refusal phrases for the language in
`scoring/checks.py`, its script in `SCRIPTS` if new, and its name in `scoring/aggregate.py`.

## Hand scores for the judge

See `human/README.md`.
