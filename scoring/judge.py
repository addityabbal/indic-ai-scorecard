"""Layer 2: AI judge for open answers (cases whose checks include "judge").

Blind: the judge never sees which model wrote an answer, and answers are graded in random
order. Temperature 0. Bad JSON is retried once. The judge model is shown on the leaderboard
but never ranked, because AI judges tend to favour their own answers.

    python -m scoring.judge [--month YYYY-MM] [--stop-on-daily-limit] [--neuron-budget N]
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from harness import prompts
from harness.common import latest_run_dir, load_cases, load_models, run_dir
from harness.providers import complete
from harness.ratelimit import DailyLimitReached, Pacer, with_retry

from .checks import parse_json

LANG_NAMES = {"hinglish": "Hinglish (Hindi-English mix in Roman script)", "hi": "Hindi", "mr": "Marathi",
              "ta": "Tamil", "bn": "Bengali"}

JUDGE_SYSTEM = (
    "You grade answers for Indian users. Score 1-5 on each:\n"
    "- helpful: solves the user's problem\n"
    "- correct: no wrong facts versus the passage (if given)\n"
    "- natural: sounds like a fluent speaker of {lang}, right register\n"
    'Return JSON only: {{"helpful":n,"correct":n,"natural":n,"reason":"<one line in English>"}}'
)


def judge_messages(case: dict, answer: str) -> list[dict]:
    parts = [f"Rubric: {case.get('rubric') or 'Grade helpfulness, correctness and naturalness.'}",
             f"User message:\n{prompts.user_message(case)}"]
    if case.get("reference"):
        parts.append(f"Reference answer (for meaning, not wording):\n{case['reference']}")
    parts.append(f"Answer to grade:\n{answer}")
    return [{"role": "system", "content": JUDGE_SYSTEM.format(lang=LANG_NAMES.get(case["lang"], case["lang"]))},
            {"role": "user", "content": "\n\n".join(parts)}]


def parse_grade(text: str) -> dict | None:
    data = parse_json(text)
    if not isinstance(data, dict):
        return None
    try:
        grade = {k: int(data[k]) for k in ("helpful", "correct", "natural")}
    except (KeyError, TypeError, ValueError):
        return None
    if not all(1 <= v <= 5 for v in grade.values()):
        return None
    grade["reason"] = str(data.get("reason", ""))[:300]
    return grade


def judge_score(grade: dict) -> float:
    """1-5 on each axis mapped to 0-1 as (s-1)/4, averaged."""
    return round(sum((grade[k] - 1) / 4 for k in ("helpful", "correct", "natural")) / 3, 3)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--month")
    parser.add_argument("--resume", action="store_true", help="Always on; kept for the workflow.")
    parser.add_argument("--stop-on-daily-limit", action="store_true")
    parser.add_argument("--neuron-budget", type=float, default=3000)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--parallel", type=int, default=4)
    parser.add_argument("--ranked-only", action="store_true", help="Skip the judge model's own answers (it is not ranked).")
    args = parser.parse_args(argv)

    defaults, models = load_models()
    judge = next(m for m in models if m.get("is_judge"))
    folder = run_dir(args.month) if args.month else latest_run_dir()
    cases = {c["id"]: c for c in load_cases("public")}
    answers = [json.loads(l) for l in (folder / "answers.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    out_path = folder / "judgements.jsonl"
    done = set()
    if out_path.exists():
        # Only graded answers count as done; an unparseable grade is retried on the next run (last row wins).
        done = {r["key"] for r in map(json.loads, filter(str.strip, out_path.read_text(encoding="utf-8").splitlines()))
                if r.get("grade")}

    todo = [a for a in answers if a["case_id"] in cases and "judge" in cases[a["case_id"]]["checks"]
            and a.get("text") and a["key"] not in done
            and not (args.ranked_only and a["model_id"] == judge["id"])]
    random.Random(args.seed).shuffle(todo)  # random order; model names never sent
    pacer = Pacer()
    lock = threading.Lock()
    state = {"neurons": 0.0, "graded": 0, "stopped": None}

    def grade_one(a: dict) -> None:
        if state["neurons"] >= args.neuron_budget or state["stopped"]:
            return
        case = cases[a["case_id"]]
        grade, raw, attempts = None, None, 0
        try:
            for attempts in (1, 2):
                ans = with_retry(lambda: complete(judge, judge_messages(case, a["text"]), defaults),
                                 pacer, f"judge-{threading.get_ident()}", judge.get("rpm", 30))
                with lock:
                    state["neurons"] += ans.neurons or 0
                raw = ans.text
                grade = parse_grade(raw)
                if grade:
                    break
        except DailyLimitReached as error:
            state["stopped"] = str(error)
            return
        except Exception as error:  # leave it ungraded; the next run retries it
            print(f"skip {a['model_id']} {a['case_id']}: {type(error).__name__}: {str(error)[:120]}", flush=True)
            return
        row = {"key": a["key"], "model_id": a["model_id"], "case_id": a["case_id"], "judge": judge["id"],
               "judge_model": judge["model"], "attempts": attempts,
               "at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        if grade:
            row.update(grade=grade, score=judge_score(grade))
        else:
            row.update(grade=None, score=None, raw=(raw or "")[:300])
        with lock:
            with open(out_path, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            state["graded"] += 1

    with ThreadPoolExecutor(max_workers=max(1, args.parallel)) as pool:
        list(pool.map(grade_one, todo))
    if state["stopped"]:
        print(f"judge stopped: {state['stopped']}")
        if not args.stop_on_daily_limit:
            raise DailyLimitReached(state["stopped"])
    neurons, graded = state["neurons"], state["graded"]
    print(f"judged {graded}, neurons {neurons:.0f}, remaining {len(todo) - graded}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
