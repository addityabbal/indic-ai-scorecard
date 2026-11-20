"""Judge vs people: how often the AI judge lands within 1 point of a human score.

Hand scores go in human/scores.csv:  key,rater,helpful,correct,natural
(key = the answer key from results/<month>/answers.jsonl; see human/README.md).
Writes results/<month>/calibration.json. Below 70% agreement, a language's judged scores
are shown as "low confidence" on the leaderboard.

    python -m scoring.calibrate [--month YYYY-MM]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict

from harness.common import ROOT, latest_run_dir, load_cases, run_dir

AXES = ("helpful", "correct", "natural")
THRESHOLD = 0.70


def agreement(pairs: list[tuple[int, int]]) -> float | None:
    return round(sum(abs(h - j) <= 1 for h, j in pairs) / len(pairs), 3) if pairs else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--month")
    args = parser.parse_args(argv)
    folder = run_dir(args.month) if args.month else latest_run_dir()
    human_path = ROOT / "human" / "scores.csv"
    rows = list(csv.DictReader(open(human_path, newline="", encoding="utf-8"))) if human_path.exists() else []
    judged = {}
    path = folder / "judgements.jsonl"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            j = json.loads(line)
            if j.get("grade"):
                judged[j["key"]] = j
    lang_of = {c["id"]: c["lang"] for c in load_cases("public")}

    pairs = defaultdict(list)
    for r in rows:
        j = judged.get(r["key"])
        if not j:
            continue
        lang = lang_of.get(j["case_id"], "?")
        for axis in AXES:
            if r.get(axis):
                pairs[lang].append((int(r[axis]), int(j["grade"][axis])))
    result = {
        "status": "calibrated" if pairs else "not yet calibrated",
        "threshold": THRESHOLD,
        "human_scores": len(rows),
        "by_lang": {lang: {"pairs": len(p), "within_1": agreement(p), "low_confidence": agreement(p) < THRESHOLD}
                    for lang, p in pairs.items()},
    }
    if not pairs:
        result["note"] = "Human scores for the judge are not collected yet (target: 60 answers)."
    (folder / "calibration.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    print(json.dumps(result, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
