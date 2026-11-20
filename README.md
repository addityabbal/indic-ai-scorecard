# Indic AI Scorecard

**Which AI model should you pick for an Indian-language feature, at what cost?**

An open, reproducible scorecard that tests AI models on the messy things real Indian users send:
code-mixed Hinglish, Hindi typed in English letters, WhatsApp-style questions about government
schemes and bills. Quality, cost per 1,000 answers and response time, side by side. Runs at ₹0 on
free tiers.

**Leaderboard:** https://scorecard.adityabal.com · **Method:** [docs/METHOD.md](docs/METHOD.md)

Status: **pilot published, full test set drafted.** The live leaderboard shows the 30-case Hinglish
pilot on 6 models from Cloudflare Workers AI. All 300 cases (Hindi, Marathi, Tamil, Bengali, Hinglish;
240 public + 60 encrypted hidden) are drafted and awaiting native-speaker review before the first full run.

## How it works

```
cases/*.jsonl ──► harness/run.py ──► results/<month>/answers.jsonl   (also the cache: runs resume)
                      │  same prompt, temperature 0, one OpenAI-compatible client per provider
                      ▼
               scoring/checks.py  (code checks)  ──┐
               scoring/judge.py   (blind AI judge) ─┼─► scoring/aggregate.py ──► results/latest.json ──► site/
               scoring/calibrate.py (judge vs people)┘
```

## Run it

```bash
python -m venv .venv
```

```bash
.venv/Scripts/python -m pip install -r requirements.txt
```

Set any provider keys you have (`GROQ_API_KEY`, `GEMINI_API_KEY`, `SARVAM_API_KEY`, `OPENROUTER_API_KEY`,
or `CF_API_TOKEN` + `CF_ACCOUNT_ID` for Workers AI). Models whose provider has no key are skipped.
From a laptop you can use Workers AI with your own `wrangler login` instead: run `npx wrangler dev` in
`tools/ai-proxy` and set `AI_PROXY_URL=http://127.0.0.1:8798`.

```bash
.venv/Scripts/python -m harness.run --models enabled --cases public --neuron-budget 4000
```

```bash
.venv/Scripts/python -m scoring.judge && .venv/Scripts/python -m scoring.aggregate
```

Tests and case validation:

```bash
.venv/Scripts/python -m pytest -q
```

```bash
.venv/Scripts/python tools/validate_cases.py
```

Bring your own key for paid models: add the model to `config/models.yaml` with its provider and run
`python -m harness.run --models <id>`.

## Site

```bash
.venv/Scripts/python tools/prepare_site.py
```

```bash
npx wrangler deploy
```

## Staying at ₹0

Never add a card to Groq, Google AI Studio, OpenRouter or Cloudflare (over a limit they return errors,
not bills). Workers AI's 10,000 free neurons a day are shared with other demos on the account, so every
run has a neuron budget. Keep the repo public for free Actions minutes. Keys live only in GitHub Secrets.
Never send the hidden set to a provider whose free tier trains on prompts.

## Licence

Test cases in `cases/` are CC BY 4.0. Contributions welcome: see [CONTRIBUTING.md](CONTRIBUTING.md).
