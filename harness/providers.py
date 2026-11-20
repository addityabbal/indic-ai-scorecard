"""One OpenAI-compatible client per provider. Returns text, tokens, neurons (Workers AI) and seconds."""
from __future__ import annotations

import os
import time
from dataclasses import dataclass

from openai import APIStatusError, OpenAI


@dataclass
class Answer:
    text: str
    prompt_tokens: int
    completion_tokens: int
    neurons: float | None
    seconds: float
    model_called: str
    finish_reason: str | None


class RateLimited(Exception):
    def __init__(self, retry_after: float | None, message: str):
        super().__init__(message)
        self.retry_after = retry_after


def _env(name: str) -> str:
    return os.environ.get(name, "").strip()


def provider_config(provider: str) -> dict | None:
    """base_url + api_key (+ headers) for a provider, or None when its key is missing."""
    if provider == "workers-ai":
        proxy = _env("AI_PROXY_URL")
        if proxy:
            return {"base_url": proxy.rstrip("/") + "/v1", "api_key": "local"}
        if _env("CF_API_TOKEN") and _env("CF_ACCOUNT_ID"):
            return {
                "base_url": f"https://api.cloudflare.com/client/v4/accounts/{_env('CF_ACCOUNT_ID')}/ai/v1",
                "api_key": _env("CF_API_TOKEN"),
            }
        return None
    keys = {
        "groq": ("GROQ_API_KEY", "https://api.groq.com/openai/v1"),
        "gemini": ("GEMINI_API_KEY", "https://generativelanguage.googleapis.com/v1beta/openai/"),
        "openrouter": ("OPENROUTER_API_KEY", "https://openrouter.ai/api/v1"),
        # Sarvam's chat endpoint is OpenAI-style but authenticates with its own header. Check its docs.
        "sarvam": ("SARVAM_API_KEY", "https://api.sarvam.ai/v1"),
    }
    if provider not in keys:
        raise ValueError(f"Unknown provider {provider}")
    env, base = keys[provider]
    key = _env(env)
    if not key:
        return None
    cfg = {"base_url": base, "api_key": key}
    if provider == "sarvam":
        cfg["default_headers"] = {"api-subscription-key": key}
    return cfg


_clients: dict[str, OpenAI] = {}


def client(provider: str) -> OpenAI | None:
    cfg = provider_config(provider)
    if cfg is None:
        return None
    if provider not in _clients:
        _clients[provider] = OpenAI(timeout=180, max_retries=0, **cfg)
    return _clients[provider]


def complete(model: dict, msgs: list[dict], defaults: dict) -> Answer:
    api = client(model["provider"])
    if api is None:
        raise RuntimeError(f"No credentials for provider {model['provider']}")
    extra = {}
    if model.get("reasoning_effort"):
        extra["reasoning_effort"] = model["reasoning_effort"]
    started = time.monotonic()
    try:
        resp = api.chat.completions.create(
            model=model["model"],
            messages=msgs,
            temperature=model.get("temperature", defaults["temperature"]),
            max_tokens=model.get("max_tokens", defaults["max_tokens"]),
            extra_body=extra or None,
        )
    except APIStatusError as error:
        if error.status_code == 429:
            retry = error.response.headers.get("retry-after")
            raise RateLimited(float(retry) if retry else None, str(error)) from error
        if error.status_code in (502, 503, 504):  # "capacity temporarily exceeded": wait and retry
            raise RateLimited(15.0, str(error)) from error
        raise
    seconds = time.monotonic() - started
    usage = resp.usage
    extra_usage = getattr(usage, "model_extra", None) or {}
    choice = resp.choices[0]
    return Answer(
        text=(choice.message.content or "").strip(),
        prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
        completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
        neurons=extra_usage.get("neurons"),
        seconds=round(seconds, 2),
        model_called=resp.model or model["model"],
        finish_reason=choice.finish_reason,
    )
