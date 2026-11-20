"""Layer 3: roll-up. case -> task -> model, with bootstrap ranges, cost and latency.

Writes results/<month>/scores.json, results/<month>/explorer.json and results/latest.json
(what the site reads). The headline sentence is written from the data by code, never by AI.

    python -m scoring.aggregate [--month YYYY-MM]
"""
from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone

from harness.common import RESULTS, latest_run_dir, load_cases, load_models, load_prices, run_dir

from .checks import run_checks

TASK_LABELS = {
    "support": "Customer-support reply",
    "passage_qa": "Answer from a passage",
    "extract": "Pull data from a message",
    "intent": "Understand intent",
    "simplify": "Rewrite simply",
    "refuse": "Say \"I don't know\"",
}
LANG_LABELS = {"hinglish": "Hinglish", "hi": "Hindi", "mr": "Marathi", "ta": "Tamil", "bn": "Bengali"}
FAILURE_CHECKS = ["script_match", "no_invented_numbers", "json_fields", "refusal", "label_match", "facts_present"]
FAILURE_TEXT = {
    "script_match": "Replied in the wrong script",
    "no_invented_numbers": "Invented a number",
    "json_fields": "Broken or wrong JSON",
    "refusal": "Made up an answer instead of saying it doesn't know",
    "label_match": "Wrong intent label",
    "facts_present": "Missed the key fact",
}


def read_jsonl(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def case_score(checks: dict, judge: float | None, wants_judge: bool) -> float | None:
    parts = [c["score"] for name, c in checks.items() if name != "chrf" and c["score"] is not None]
    if wants_judge:
        if judge is None:
            return None  # not judged yet: leave the case out rather than score it on code checks alone
        parts.append(judge)
    return round(sum(parts) / len(parts), 4) if parts else None


def model_score(by_task: dict[str, list[float]]) -> float | None:
    means = [statistics.fmean(v) for v in by_task.values() if v]
    return round(statistics.fmean(means), 4) if means else None


def bootstrap(by_task: dict[str, list[float]], n: int = 1000, seed: int = 11) -> tuple[float, float] | None:
    """95% range: resample cases within each task, average tasks equally."""
    tasks = [v for v in by_task.values() if v]
    if not tasks:
        return None
    rng = random.Random(seed)
    stats = []
    for _ in range(n):
        means = [statistics.fmean(rng.choices(v, k=len(v))) for v in tasks]
        stats.append(statistics.fmean(means))
    stats.sort()
    return round(stats[int(0.025 * n)], 4), round(stats[int(0.975 * n) - 1], 4)


def cost_usd(row: dict, model: dict, prices: dict) -> float | None:
    if model["provider"] == "workers-ai" and row.get("neurons") is not None:
        return row["neurons"] * prices["workers_ai"]["usd_per_1000_neurons"] / 1000
    table = prices.get("tokens", {}).get(model["model"]) or prices.get("workers_ai", {}).get(model["model"])
    if not table or table.get("in") is None or table.get("out") is None:
        return None
    return (row.get("prompt_tokens", 0) * table["in"] + row.get("completion_tokens", 0) * table["out"]) / 1e6


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    values = sorted(values)
    return round(values[min(len(values) - 1, int(q * (len(values) - 1) + 0.5))], 2)


def build(folder) -> dict:
    defaults, models = load_models()
    model_by_id = {m["id"]: m for m in models}
    prices = load_prices()
    cases = {c["id"]: c for c in load_cases("public")}
    answers = [a for a in read_jsonl(folder / "answers.jsonl") if a["case_id"] in cases]
    judgements = {j["key"]: j for j in read_jsonl(folder / "judgements.jsonl")}
    calibration = json.loads((folder / "calibration.json").read_text(encoding="utf-8")) if (folder / "calibration.json").exists() else {}
    hidden_scores = json.loads((folder / "hidden_scores.json").read_text(encoding="utf-8")) if (folder / "hidden_scores.json").exists() else {}

    per_model: dict[str, dict] = defaultdict(lambda: {"by_task": defaultdict(list), "by_lang_task": defaultdict(lambda: defaultdict(list)),
                                                       "script": [], "costs": [], "seconds": [], "answers": 0, "errors": 0,
                                                       "pending_judge": 0})
    explorer = defaultdict(dict)
    failures = []
    for a in answers:
        case = cases[a["case_id"]]
        m = per_model[a["model_id"]]
        m["answers"] += 1
        model = model_by_id.get(a["model_id"], {"provider": "", "model": a.get("model_called", "")})
        if not (a.get("text") or "").strip():
            # No answer at all (API error, or every token spent on hidden reasoning): scores 0.
            m["errors"] += 1
            checks, score = {}, 0.0
            reason = a.get("error") or ("ran out of tokens before answering" if a.get("finish_reason") == "length" else "empty reply")
            failures.append({"model_id": a["model_id"], "case_id": a["case_id"], "check": "no_answer",
                             "what": "Gave no answer", "detail": reason})
        else:
            checks = run_checks(case, a["text"])
            j = judgements.get(a["key"])
            judge_value = j["score"] if j and j.get("score") is not None else None
            wants = "judge" in case["checks"]
            if wants and judge_value is None:
                m["pending_judge"] += 1
            score = case_score(checks, judge_value, wants)
            if "script_match" in checks:
                m["script"].append(1.0 if checks["script_match"]["pass"] else 0.0)
            c = cost_usd(a, model, prices)
            if c is not None:
                m["costs"].append(c)
            if a.get("seconds") is not None:
                m["seconds"].append(a["seconds"])
            for name in FAILURE_CHECKS:
                if name in checks and checks[name]["pass"] is False:
                    failures.append({"model_id": a["model_id"], "case_id": a["case_id"], "check": name,
                                     "what": FAILURE_TEXT[name], "detail": checks[name]["detail"]})
        if score is not None:
            m["by_task"][case["task"]].append(score)
            m["by_lang_task"][case["lang"]][case["task"]].append(score)
        j = judgements.get(a["key"])
        explorer[a["case_id"]][a["model_id"]] = {
            "text": a.get("text"), "error": a.get("error"), "score": score,
            "checks": {k: {"pass": v["pass"], "detail": v["detail"], "score": v["score"]} for k, v in checks.items()},
            "judge": ({"grade": j["grade"], "score": j["score"]} if j and j.get("grade") else None),
            "seconds": a.get("seconds"),
        }

    rows = []
    for mid, m in per_model.items():
        model = model_by_id.get(mid, {})
        overall = model_score(m["by_task"])
        if model.get("is_judge"):
            overall = None  # the judge's own open answers are not graded, so an overall score would mislead
        rows.append({
            "id": mid,
            "model": model.get("model"),
            "maker": model.get("maker"),
            "provider": model.get("provider"),
            "is_judge": bool(model.get("is_judge")),
            "score": overall,
            "range": None if model.get("is_judge") else bootstrap(m["by_task"]),
            "by_task": {t: round(statistics.fmean(v), 4) for t, v in m["by_task"].items() if v},
            "by_lang": {lang: model_score(tasks) for lang, tasks in m["by_lang_task"].items()},
            "script_match": round(statistics.fmean(m["script"]), 4) if m["script"] else None,
            "usd_per_1000": round(statistics.fmean(m["costs"]) * 1000, 4) if m["costs"] else None,
            "median_seconds": percentile(m["seconds"], 0.5),
            "p90_seconds": percentile(m["seconds"], 0.9),
            "answers": m["answers"],
            "errors": m["errors"],
            "pending_judge": m["pending_judge"],
            "hidden_gap": hidden_scores.get(mid, {}).get("gap"),
        })
    rows.sort(key=lambda r: (r["is_judge"], -(r["score"] or -1)))
    ranked = [r for r in rows if not r["is_judge"] and r["score"] is not None]
    for i, r in enumerate(ranked, 1):
        r["rank"] = i

    # Failure gallery: up to 10, spread across models and failure types.
    seen, gallery = set(), []
    for f in failures:
        k = (f["model_id"], f["check"])
        if k in seen:
            continue
        seen.add(k)
        case = cases[f["case_id"]]
        gallery.append({**f, "task": case["task"], "lang": case["lang"], "input": case["input"],
                        "context": case.get("context"), "answer": explorer[f["case_id"]][f["model_id"]]["text"]})
        if len(gallery) == 10:
            break

    answered_ids = {a["case_id"] for a in answers}
    langs = sorted({cases[i]["lang"] for i in answered_ids}) or sorted({c["lang"] for c in cases.values()})
    meta_path = folder / "run_meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    judge = next((m for m in models if m.get("is_judge")), None)
    return {
        "month": folder.name,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "headline": headline(ranked, langs),
        "cases": {"public": len(cases), "answered": len(answered_ids),
                  "by_lang": {l: sum(1 for i in answered_ids if cases[i]["lang"] == l) for l in langs},
                  "in_set_by_lang": {l: sum(1 for c in cases.values() if c["lang"] == l) for l in sorted({c["lang"] for c in cases.values()})},
                  "tasks": sorted({cases[i]["task"] for i in answered_ids}),
                  "reviewed": sum(1 for i in answered_ids if cases[i].get("reviewed_by"))},
        "languages": {l: LANG_LABELS.get(l, l) for l in langs},
        "tasks": TASK_LABELS,
        "judge": {"id": judge["id"], "model": judge["model"], "maker": judge.get("maker")} if judge else None,
        "calibration": calibration or {"status": "not yet calibrated", "note": "Human scores for the judge are not collected yet."},
        "prices_checked": prices.get("checked"),
        "usd_inr": prices.get("usd_inr"),
        "runs": meta.get("runs", []),
        "models": rows,
        "failures": gallery,
    }, explorer


def headline(ranked: list[dict], langs: list[str]) -> str:
    if not ranked:
        return "No results yet."
    best = ranked[0]
    lo_best = best["range"][0] if best["range"] else best["score"]
    tied = [r for r in ranked if r["range"] and r["range"][1] >= lo_best]
    priced = [r for r in tied if r["usd_per_1000"] is not None]
    lang_text = " and ".join(LANG_LABELS.get(l, l) for l in langs)
    text = f"Top {lang_text} quality: {best['id']} ({best['score']:.2f})."
    if priced:
        cheapest = min(priced, key=lambda r: r["usd_per_1000"])
        if cheapest["id"] != best["id"]:
            text += (f" Best quality per dollar: {cheapest['id']}, statistically tied with it at "
                     f"${cheapest['usd_per_1000']:.2f} per 1,000 answers.")
        else:
            text += f" It is also the cheapest of the models tied with it, at ${cheapest['usd_per_1000']:.2f} per 1,000 answers."
    return text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--month")
    args = parser.parse_args(argv)
    folder = run_dir(args.month) if args.month else latest_run_dir()
    scores, explorer = build(folder)
    (folder / "scores.json").write_text(json.dumps(scores, ensure_ascii=False, indent=1), encoding="utf-8")
    (folder / "explorer.json").write_text(json.dumps(explorer, ensure_ascii=False), encoding="utf-8")

    history = {}
    for past in sorted(p for p in RESULTS.glob("20*-*") if (p / "scores.json").exists()):
        data = json.loads((past / "scores.json").read_text(encoding="utf-8"))
        for r in data["models"]:
            history.setdefault(r["id"], []).append({"month": data["month"], "score": r["score"]})
    latest = {**scores, "history": history, "explorer_path": f"results/{folder.name}/explorer.json"}
    (RESULTS / "latest.json").write_text(json.dumps(latest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(scores["headline"])
    for r in scores["models"]:
        rng = f"{r['range'][0]:.2f}-{r['range'][1]:.2f}" if r["range"] else "-"
        cost = f"${r['usd_per_1000']:.3f}/1k" if r["usd_per_1000"] is not None else "n/a"
        print(f"{r.get('rank') or ('J' if r['is_judge'] else '-'):>2} {r['id']:<20} {r['score'] if r['score'] is not None else '-':<7} [{rng}] script {r['script_match']} {cost} {r['median_seconds']}s pending_judge={r['pending_judge']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
