"""The run's answers file doubles as the cache: (model, case, prompt hash) -> answer.

A run that stops at a daily limit resumes next time without paying for any call twice.
Answers to hidden cases go to a separate, never-committed file (see docs/METHOD.md).
"""
from __future__ import annotations

import json
from pathlib import Path


def key(model_id: str, case_id: str, phash: str) -> str:
    return f"{model_id}|{case_id}|{phash}"


class AnswerStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.rows: dict[str, dict] = {}
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    row = json.loads(line)
                    self.rows[row["key"]] = row

    def has(self, k: str) -> bool:
        return k in self.rows

    def add(self, row: dict) -> None:
        self.rows[row["key"]] = row
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    def all(self) -> list[dict]:
        return list(self.rows.values())
