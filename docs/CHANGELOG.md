# Changelog

## 2026-11 — Full test set drafted (M3)

- 270 new cases: Hindi, Marathi, Tamil (3 of 10 romanized), Bengali, and Hinglish 006-010. 300 in all,
  drafted and awaiting native-speaker review. Not run yet.
- 60-case hidden set, encrypted with age (`cases/hidden.jsonl.age`).
- Checks now read Bengali and Tamil digits, lakh in Tamil and Bengali, more refusal phrases and
  honorifics in each language. Duplicate inputs are checked within a language.

## 2026-11 — Hinglish pilot

- 30 Hinglish cases (6 tasks × 5), drafted, awaiting native-speaker review.
- 6 ranked models on Cloudflare Workers AI: Llama 3.3 70B, Llama 4 Scout, Mistral Small 3.1, gpt-oss-20b,
  Qwen 3.8 27B, GLM-4.7 Flash. Judge: Gemma 4 26B (not ranked).
- Code checks, blind judge, bootstrap ranges, cost from measured neurons, leaderboard site.
- Not yet: Groq / Google / Sarvam / OpenRouter models (need keys), other languages, hidden set,
  judge calibration against people.
