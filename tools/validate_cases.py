"""Fails if any case breaks cases/schema.json, repeats an id or input, or misses data a check needs.
Also fails if a hidden case id ever appears in a committed results file.

    python tools/validate_cases.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
NEEDS = {
    "json_fields": lambda c: isinstance(c.get("expected"), dict) and c["expected"],
    "label_match": lambda c: (c.get("expected") or {}).get("label") in (c.get("expected") or {}).get("labels", []),
    "facts_present": lambda c: (c.get("expected") or {}).get("facts"),
    "chrf": lambda c: c.get("reference"),
    "judge": lambda c: c.get("rubric"),
    "refusal": lambda c: c.get("context"),
}


def main() -> int:
    validator = Draft202012Validator(json.loads((ROOT / "cases" / "schema.json").read_text(encoding="utf-8")))
    errors, ids, inputs = [], set(), set()
    files = sorted(p for p in (ROOT / "cases").glob("*.jsonl"))
    count = 0
    for path in files:
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            count += 1
            where = f"{path.name}:{n}"
            try:
                case = json.loads(line)
            except json.JSONDecodeError as error:
                errors.append(f"{where}: invalid JSON ({error})")
                continue
            for err in validator.iter_errors(case):
                errors.append(f"{where}: {err.message}")
            if case.get("id") in ids:
                errors.append(f"{where}: duplicate id {case.get('id')}")
            ids.add(case.get("id"))
            norm = " ".join(str(case.get("input", "")).lower().split())
            if norm in inputs:
                errors.append(f"{where}: duplicate input")
            inputs.add(norm)
            for check in case.get("checks", []):
                if check in NEEDS and not NEEDS[check](case):
                    errors.append(f"{where}: check '{check}' is missing the data it needs")

    hidden = ROOT / "cases" / "hidden.jsonl"
    if hidden.exists():
        hidden_ids = {json.loads(l)["id"] for l in hidden.read_text(encoding="utf-8").splitlines() if l.strip()}
        for path in (ROOT / "results").rglob("*.json*"):
            if path.name.endswith(".local.jsonl"):
                continue
            text = path.read_text(encoding="utf-8")
            leaked = [h for h in hidden_ids if h in text]
            if leaked:
                errors.append(f"{path}: hidden case ids in a committed file: {leaked[:3]}")

    for e in errors:
        print("ERROR", e)
    print(f"{count} cases in {len(files)} files, {len(errors)} problems")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
