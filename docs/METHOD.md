# Method

**Question this answers:** which model should a builder pick for an Indian-language feature, at what cost?

## Test set

**300 cases = 6 tasks × 5 language variants × 10 cases**, all drafted (M3):

| Language | Script | Public | Hidden |
| --- | --- | --- | --- |
| Hinglish | Roman | 48 | 12 |
| Hindi | Devanagari | 48 | 12 |
| Marathi | Devanagari | 48 | 12 |
| Tamil | Tamil script, 3 of 10 per task romanized | 48 | 12 |
| Bengali | Bengali | 48 | 12 |

The same 10 real-world scenarios per task run in every language, so languages can be compared.
Passages are in English, as most official scheme pages are; questions and expected replies are in
the user's language. Cases were drafted by Claude (`author: draft-claude`) and are **not yet reviewed**
by native speakers (`reviewed_by: null`); review is the next step. Only the 30-case Hinglish pilot
(cases 001-005 per task) has been run so far. Passages are written from scratch from public scheme
facts (PM-Kisan, PM Surya Ghar, PM-JAY, Sukanya Samriddhi, Ujjwala), never copied from other
benchmarks. Public cases are licensed CC BY 4.0.

| Task | What it copies | Scored by |
| --- | --- | --- |
| support | A WhatsApp-style support message | judge + same script |
| passage_qa | A scheme question with the scheme passage | key facts present + no invented numbers + same script + judge |
| extract | A shopkeeper's ledger note → JSON | JSON fields match exactly |
| intent | A message → one label from a list | label match |
| simplify | A legal-style notice → simple language | judge + same script; chrF vs a reference is reported only |
| refuse | A question the passage can't answer | a "don't know" phrase + no invented numbers + same script |

After reading every flagged answer in the first run, five checker rules were corrected because they
failed correct replies:

1. "No invented numbers" accepts numbers one step of arithmetic from the passage or question (a sum,
   difference or product of two, e.g. 2 × 30,000 = 60,000). Trade-off: an invented number equal to such
   a sum would slip through.
2. Number words count as numbers ("three instalments" allows "3 kist").
3. Hindi unit words match their Roman forms ("5 लाख" = "5 lakh").
4. JSON name fields ignore a trailing honorific ("Sunita Bhabhi" = "Sunita").
5. A Hinglish user answered "मुझे नहीं पता" did get a refusal; the wrong script is caught by the
   script check, not the refusal check.

One test case was also wrong: hinglish-passage_qa-001 required the per-instalment amount the question
didn't ask for. A fact can now list accepted forms (3 / three / teen / तीन).

"Same script" applies to free-text replies only (not JSON or labels): at least 80% of letters must be in
the user's script (Latin, Devanagari, Tamil or Bengali Unicode ranges).

## Prompt

Every model gets the same system prompt (`harness/prompts.py`), temperature 0. The user message is the
passage (if any), the user's text, and the task instruction written in the user's language.
`max_tokens` is 1,500 rather than the planned 600, because several current models spend hidden
reasoning tokens before answering; with 600 they returned empty answers.

## Scoring

1. **Code checks** (`scoring/checks.py`), each pass = 1, fail = 0.
2. **AI judge** (`scoring/judge.py`) for support, passage_qa and simplify: 1–5 on helpful, correct and
   natural, mapped to (s−1)/4 and averaged. Blind (no model names) and in random order, temperature 0,
   one retry on bad JSON. The judge model is shown but never ranked.
3. **Roll-up** (`scoring/aggregate.py`): case score = mean of its checks (judge counts as one check);
   model score = mean over tasks of the mean over cases, so every task weighs the same; 95% range by
   bootstrap (1,000 resamples within each task). Overlapping ranges are ties.

**Pilot judge:** Gemma 4 26B on Workers AI, because no Groq key is set yet. The plan's judge is a large
open model on Groq; switch `is_judge` in `config/models.yaml` when the key exists.

**Judge vs people** (`scoring/calibrate.py`): hand-score 60 answers in `human/scores.csv`; the share of
scores within 1 point of the judge is published per language. Below 70%, that language's judged
scores are flagged low confidence. *Not done yet.*

## Cost and speed

- Workers AI: cost per answer = neurons the call used × $0.011 / 1,000 neurons (measured, from the API
  response). Other providers: list price per million tokens in `config/prices.yaml` (null until checked).
- Shown as US$ per 1,000 answers. Rupees appear once `usd_inr` is set in `config/prices.yaml`.
- Speed: median and 90th-percentile seconds to the full answer, **measured on free tiers**.

## Contamination

Cases 006 and 010 of every task and language (60 cases, 20%) are the hidden set. They live only in
`cases/hidden.jsonl.age`, encrypted with age to the public key in `config/age-recipient.txt`
(`tools/hidden_set.py`). The monthly workflow decrypts them with the `AGE_KEY` secret, sends them only to
providers whose free tier does not train on prompts (`public_cases_only` models skip them), writes their
answers to a git-ignored file and deletes the plaintext before committing. `tools/validate_cases.py`
fails if a hidden case id appears in any committed result. The leaderboard flags models that score much
higher on public cases than hidden ones.

## Limits

- 5 cases per task in the pilot: ranges are wide. Read ties, not ranks.
- Unreviewed cases may contain unnatural Hinglish; review is the next step.
- Free-tier latency is not paid-tier latency.
- Workers AI models change: two planned models (Qwen3 30B, Llama 3.1 8B fp8) were deprecated on 2026-11-20,
  the day the pilot ran. Each run records the exact model id it called.
