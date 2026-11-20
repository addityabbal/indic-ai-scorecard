"""The same system prompt for every model, and how a case becomes a user message."""
import hashlib
import json

SYSTEM = (
    "You are a helpful assistant for users in India.\n"
    "Reply in the same language and script the user wrote in.\n"
    "If the answer is not in the given passage, say you don't know.\n"
    "When asked for JSON, return only valid JSON."
)


def user_message(case: dict) -> str:
    parts = []
    if case.get("context"):
        parts.append(f"Passage:\n{case['context']}")
    parts.append(case["input"])
    if case.get("instruction"):
        parts.append(case["instruction"])
    return "\n\n".join(parts)


def messages(case: dict) -> list[dict]:
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user_message(case)}]


def prompt_hash(case: dict) -> str:
    return hashlib.sha256(json.dumps(messages(case), ensure_ascii=False).encode()).hexdigest()[:16]
