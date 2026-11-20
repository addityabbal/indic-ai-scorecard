"""Send every case to every model and save each answer with tokens, neurons and seconds.

    python -m harness.run --models enabled --cases public
    python -m harness.run --models groq-llama-3.1-8b --cases cases/hinglish.jsonl --limit 3
    python -m harness.run --models enabled --cases all --resume --stop-on-daily-limit --neuron-budget 6000

Bring your own key (paid models): add the model to config/models.yaml with its provider,
export that provider's key, and run with --models <id>. Results are saved the same way.
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from . import prompts
from .cache import AnswerStore, key
from .common import load_cases, load_models, run_dir
from .providers import client, complete
from .ratelimit import DailyLimitReached, Pacer, with_retry


def pick_models(spec: str, models: list[dict], include_judge: bool = True) -> list[dict]:
    if spec == "enabled":
        chosen = [m for m in models if m.get("enabled")]
    elif spec == "all":
        chosen = list(models)
    else:
        wanted = set(spec.split(","))
        chosen = [m for m in models if m["id"] in wanted or m["model"] in wanted]
    if not include_judge:
        chosen = [m for m in chosen if not m.get("is_judge")]
    return chosen


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--models", default="enabled")
    parser.add_argument("--cases", default="public", help="public | hidden | all | path/to/file.jsonl")
    parser.add_argument("--limit", type=int, default=0, help="Only the first N cases (smoke test).")
    parser.add_argument("--month", help="Run folder YYYY-MM (default: this month).")
    parser.add_argument("--resume", action="store_true", help="Skip answers already saved (always on; kept for the workflow).")
    parser.add_argument("--stop-on-daily-limit", action="store_true")
    parser.add_argument("--parallel", type=int, default=4, help="Models called at the same time.")
    parser.add_argument("--neuron-budget", type=float, default=6000, help="Stop Workers AI calls after this many neurons in this run.")
    args = parser.parse_args(argv)

    defaults, models = load_models()
    chosen = pick_models(args.models, models, include_judge=True)
    cases = load_cases(args.cases)
    if args.limit:
        cases = cases[: args.limit]
    folder = run_dir(args.month)
    public_store = AnswerStore(folder / "answers.jsonl")
    hidden_store = AnswerStore(folder / "hidden_answers.local.jsonl")  # git-ignored
    pacer = Pacer()
    lock = threading.Lock()
    totals = {"neurons": 0.0, "called": 0, "skipped": 0}
    missing: set[str] = set()
    stops: list[str] = []

    def run_model(model: dict) -> None:
        for case in cases:
            if case["_hidden"] and model.get("public_cases_only"):
                continue
            store = hidden_store if case["_hidden"] else public_store
            k = key(model["id"], case["id"], prompts.prompt_hash(case))
            if store.has(k):
                with lock:
                    totals["skipped"] += 1
                continue
            if model["provider"] == "workers-ai" and totals["neurons"] >= args.neuron_budget:
                with lock:
                    stops.append(f"neuron budget {args.neuron_budget:.0f} reached")
                return
            err = None
            try:
                ans = with_retry(lambda: complete(model, prompts.messages(case), defaults), pacer, model["id"], model.get("rpm", 30))
            except DailyLimitReached as error:
                with lock:
                    stops.append(f"{model['id']}: {error}")
                if args.stop_on_daily_limit:
                    return
                raise
            except Exception as error:  # store failures too: a crash is a result
                ans, err = None, f"{type(error).__name__}: {str(error)[:300]}"
            row = {"key": k, "model_id": model["id"], "case_id": case["id"], "hidden": case["_hidden"],
                   "at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            if ans is None:
                row.update(text=None, error=err)
            else:
                row.update(text=ans.text, prompt_tokens=ans.prompt_tokens, completion_tokens=ans.completion_tokens,
                           neurons=ans.neurons, seconds=ans.seconds, model_called=ans.model_called,
                           finish_reason=ans.finish_reason)
            if case["_hidden"]:  # never keep hidden prompts or answer text in anything committed
                row.pop("text", None)
                row["text_local"] = ans.text if ans else None
            with lock:
                store.add(row)
                totals["called"] += 1
                totals["neurons"] += (ans.neurons or 0) if ans else 0
            status = ("ERR " + (err or ""))[:60] if ans is None else f"{ans.seconds:>5.1f}s {ans.completion_tokens:>4} tok"
            print(f"{model['id']:<20} {case['id']:<26} {status}", flush=True)

    runnable = []
    for model in chosen:
        if client(model["provider"]) is None:
            missing.add(model["provider"])
        else:
            runnable.append(model)
    with ThreadPoolExecutor(max_workers=max(1, args.parallel)) as pool:
        for future in [pool.submit(run_model, m) for m in runnable]:
            future.result()
    neurons_used, called, skipped = totals["neurons"], totals["called"], totals["skipped"]
    stopped = "; ".join(sorted(set(stops))) or None

    meta_path = folder / "run_meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {"runs": []}
    meta["runs"].append({
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "models": [m["id"] for m in chosen if m["provider"] not in missing],
        "missing_credentials": sorted(missing),
        "cases": args.cases,
        "called": called,
        "cached": skipped,
        "neurons": round(neurons_used, 1),
        "stopped": stopped,
    })
    meta_path.write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print(f"called {called}, cached {skipped}, neurons {neurons_used:.0f}" + (f", stopped: {stopped}" if stopped else "") +
          (f", no credentials for: {', '.join(sorted(missing))}" if missing else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
