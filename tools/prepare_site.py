"""Copy what the static site needs into site/data/: latest.json, the run's explorer.json and
the public cases. Run before `wrangler pages deploy site`.
"""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "site" / "data"


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    latest = json.loads((ROOT / "results" / "latest.json").read_text(encoding="utf-8"))
    shutil.copy(ROOT / "results" / "latest.json", DATA / "latest.json")
    shutil.copy(ROOT / latest["explorer_path"], DATA / "explorer.json")
    lines = []
    for path in sorted((ROOT / "cases").glob("*.jsonl")):
        if path.name.startswith("hidden"):
            continue
        lines += [l for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    (DATA / "cases.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"site/data ready: {len(lines)} public cases, month {latest['month']}")


if __name__ == "__main__":
    main()
