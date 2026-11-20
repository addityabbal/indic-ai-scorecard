"""Shared loading helpers: config, cases, run folders."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "cases"
RESULTS = ROOT / "results"


def load_models() -> tuple[dict, list[dict]]:
    data = yaml.safe_load((ROOT / "config" / "models.yaml").read_text(encoding="utf-8"))
    return data["defaults"], data["models"]


def load_prices() -> dict:
    return yaml.safe_load((ROOT / "config" / "prices.yaml").read_text(encoding="utf-8"))


def load_cases(which: str = "public") -> list[dict]:
    """which: 'public', 'hidden', 'all', or a path to one .jsonl file."""
    if which.endswith(".jsonl"):
        files = [Path(which)]
    else:
        public = sorted(p for p in CASES.glob("*.jsonl") if p.name != "hidden.jsonl")
        hidden = [CASES / "hidden.jsonl"] if (CASES / "hidden.jsonl").exists() else []
        files = {"public": public, "hidden": hidden, "all": public + hidden}[which]
    cases = []
    for path in files:
        hidden_file = path.name == "hidden.jsonl"
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                case = json.loads(line)
                case["_hidden"] = hidden_file
                cases.append(case)
    return cases


def run_dir(month: str | None = None) -> Path:
    month = month or datetime.now(timezone.utc).strftime("%Y-%m")
    return RESULTS / month


def latest_run_dir() -> Path | None:
    runs = sorted(p for p in RESULTS.glob("20*-*") if p.is_dir())
    return runs[-1] if runs else None
