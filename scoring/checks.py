"""Layer 1: code checks. Each returns (passed: bool, detail: str). chrF is a score, reported only."""
from __future__ import annotations

import json
import re

SCRIPTS = {
    "deva": [(0x0900, 0x097F), (0xA8E0, 0xA8FF)],
    "taml": [(0x0B80, 0x0BFF)],
    "beng": [(0x0980, 0x09FF)],
    "latn": [(0x0041, 0x005A), (0x0061, 0x007A), (0x00C0, 0x024F)],
}
DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")

# "I don't know" phrases per language. Lowercased substring match.
REFUSAL = {
    "hinglish": [
        "pata nahi", "nahi pata", "nahin pata", "jaankari nahi", "jankari nahi", "nahi di gayi", "nahi diya",
        "nahi bataya", "mention nahi", "nahi likha", "passage mein nahi", "passage me nahi", "nahi hai is",
        "don't know", "do not know", "not mentioned", "not given", "not provided", "not available",
        "doesn't say", "does not say", "no information",
    ],
    "hi": ["पता नहीं", "नहीं पता", "जानकारी नहीं", "नहीं दी", "उल्लेख नहीं", "नहीं बताया", "नहीं लिखा", "उपलब्ध नहीं"],
    "mr": ["माहित नाही", "माहिती नाही", "उल्लेख नाही", "दिलेली नाही"],
    "ta": ["தெரியவில்லை", "தகவல் இல்லை", "குறிப்பிடப்படவில்லை"],
    "bn": ["জানি না", "তথ্য নেই", "উল্লেখ নেই", "বলা নেই"],
}


def _in(cp: int, ranges) -> bool:
    return any(lo <= cp <= hi for lo, hi in ranges)


def script_share(text: str, script: str) -> float | None:
    """Share of script letters (Latin, Devanagari, Tamil, Bengali) that are in the expected script."""
    counted = expected = 0
    for ch in text:
        cp = ord(ch)
        hit = next((name for name, ranges in SCRIPTS.items() if _in(cp, ranges)), None)
        if hit:
            counted += 1
            expected += hit == script
    return expected / counted if counted else None


def script_match(text: str, script: str, threshold: float = 0.8) -> tuple[bool, str]:
    share = script_share(text, script)
    if share is None:
        return False, "no letters"
    return share >= threshold, f"{share:.0%} in {script}"


NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
                "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "fifteen": 15, "twenty": 20, "thirty": 30,
                "hundred": 100}
UNIT_WORDS = {"लाख": "lakh", "करोड़": "crore", "करोड": "crore", "हज़ार": "hazaar", "हजार": "hazaar"}


def numbers(text: str) -> set[float]:
    """Digits (Latin or Devanagari, Indian commas) plus English number words like "three"."""
    out = {float(v) for w, v in NUMBER_WORDS.items() if re.search(r"\b" + w + r"\b", (text or "").lower())}
    for match in NUMBER.findall((text or "").translate(DEVANAGARI_DIGITS)):
        try:
            out.add(float(match.replace(",", "").rstrip(".")))
        except ValueError:
            pass
    return out


def derived(values: set[float]) -> set[float]:
    """Numbers one step of arithmetic away from the source (sum, difference, product of two),
    so correct working such as 2 x 30,000 = 60,000 is not called invented."""
    vals = sorted(values)
    out = set(vals)
    for i, a in enumerate(vals):
        for b in vals[i:]:
            out.update({a + b, abs(a - b), a * b})
    return out


def no_invented_numbers(answer: str, *sources: str) -> tuple[bool, str]:
    allowed = derived(set().union(*(numbers(s or "") for s in sources)))
    invented = sorted(n for n in numbers(answer) if n not in allowed)
    return (not invented), ("ok" if not invented else f"not in passage/question: {invented}")


def _norm(text: str) -> str:
    text = (text or "").translate(DEVANAGARI_DIGITS)
    for hindi, latin in UNIT_WORDS.items():
        text = text.replace(hindi, latin)
    return re.sub(r"[\s,]", "", text.lower())


def facts_present(answer: str, facts: list) -> tuple[bool, str]:
    """Each fact must appear. A fact may be a list of accepted forms, e.g. ["3", "three", "teen", "तीन"]."""
    text = _norm(answer)
    missing = [f for f in facts if not any(_norm(form) in text for form in (f if isinstance(f, list) else [f]))]
    return (not missing), ("ok" if not missing else f"missing: {missing}")


def parse_json(text: str):
    text = (text or "").strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fenced:
        text = fenced.group(1)
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


HONORIFICS = {"bhai", "bhaiya", "bhabhi", "aunty", "auntie", "uncle", "ji", "didi", "sir", "madam", "dada", "anna", "akka"}


def same_name(got: str, want: str) -> bool:
    """Case-insensitive name match that ignores a trailing honorific (Imran bhai, Lakshmi aunty)."""
    words = got.strip().lower().split()
    while len(words) > 1 and words[-1] in HONORIFICS:
        words.pop()
    return " ".join(words) == want.strip().lower()


def json_fields(answer: str, expected: dict) -> tuple[bool, str]:
    data = parse_json(answer)
    if not isinstance(data, dict):
        return False, "not valid JSON"
    wrong = []
    for field, want in expected.items():
        got = data.get(field)
        if isinstance(want, (int, float)):
            try:
                ok = got is not None and float(str(got).replace(",", "")) == float(want)
            except ValueError:
                ok = False
        else:
            ok = isinstance(got, str) and same_name(got, str(want))
        if not ok:
            wrong.append(f"{field}={got!r} (want {want!r})")
    return (not wrong), ("ok" if not wrong else "; ".join(wrong))


def label_match(answer: str, expected: str, labels: list[str]) -> tuple[bool, str]:
    text = (answer or "").lower()
    found = [label for label in labels if label.lower() in text]
    if found == [expected]:
        return True, "ok"
    return False, f"found {found or 'no label'}"


# A refusal counts in any script of the same language: a Hinglish user answered "मुझे नहीं पता"
# did get a refusal; the wrong script is caught separately by script_match.
SAME_LANGUAGE = {"hinglish": ["hi"], "hi": ["hinglish"]}


def refusal(answer: str, lang: str) -> tuple[bool, str]:
    text = (answer or "").lower()
    phrases = REFUSAL.get(lang, []) + REFUSAL["hinglish"][-8:]
    for other in SAME_LANGUAGE.get(lang, []):
        phrases += REFUSAL[other]
    hit = next((p for p in phrases if p.lower() in text), None)
    return (hit is not None), (f"found '{hit}'" if hit else "no don't-know phrase")


def chrf(answer: str, reference: str) -> float:
    from sacrebleu.metrics import CHRF

    return round(CHRF().sentence_score(answer or "", [reference]).score / 100, 3)


def run_checks(case: dict, answer: str) -> dict:
    """All code checks a case asks for. Returns {check: {"pass": bool|None, "detail": str, "score": float|None}}."""
    out = {}
    exp = case.get("expected") or {}
    for check in case["checks"]:
        if check == "judge":
            continue
        if check == "script_match":
            ok, detail = script_match(answer, case["script"])
        elif check == "json_fields":
            ok, detail = json_fields(answer, exp)
        elif check == "label_match":
            ok, detail = label_match(answer, exp["label"], exp["labels"])
        elif check == "facts_present":
            ok, detail = facts_present(answer, exp["facts"])
        elif check == "no_invented_numbers":
            ok, detail = no_invented_numbers(answer, case.get("context"), case.get("input"))
        elif check == "refusal":
            ok, detail = refusal(answer, case["lang"])
        elif check == "chrf":
            out["chrf"] = {"pass": None, "detail": "reported only", "score": chrf(answer, case["reference"])}
            continue
        else:
            raise ValueError(f"unknown check {check}")
        out[check] = {"pass": ok, "detail": detail, "score": 1.0 if ok else 0.0}
    return out
