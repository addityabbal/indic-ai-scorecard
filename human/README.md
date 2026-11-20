# Hand scores (judge calibration)

Score answers yourself so we can measure how far to trust the AI judge.

1. Open the leaderboard's Answer explorer, or `results/<month>/answers.jsonl`.
2. For an answer to a support, passage_qa or simplify case, add a row to `scores.csv`:
   `key,rater,helpful,correct,natural,notes` — `key` is the answer's `key` field; scores are 1–5.
   Score before looking at the judge's grade.
3. Run `python -m scoring.calibrate`, then `python -m scoring.aggregate`.

Target: 60 answers across languages, at least 15 per language.
