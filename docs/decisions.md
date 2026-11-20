# Decisions

Date, decision, reason. Newest first.

| Date | Decision | Reason |
| --- | --- | --- |
| 2026-11-20 | Start with a 30-case Hinglish pilot on Workers AI models only. | No Groq, Google, Sarvam or OpenRouter keys yet; Workers AI works through the existing Cloudflare login. Plan milestone M1. |
| 2026-11-20 | Pilot judge = Gemma 4 26B on Workers AI, not ranked. Plan's judge (large open model on Groq) once a key exists. | A judge is needed now; Gemma is cheap in neurons and multilingual. Judges favour their own answers, so it is never ranked. |
| 2026-11-20 | max_tokens 1,500 instead of 600. | Several current models (Gemma 4, gpt-oss, GLM, Qwen 3.8) spend hidden reasoning tokens first; at 600 Gemma returned empty answers. Three answers still hit 1,500 and are scored 0 as "gave no answer". |
| 2026-11-20 | An empty answer scores 0 and goes to the failure gallery. | Running out of tokens before answering is a real product failure, not a missing data point. |
| 2026-11-20 | "Same script" is checked on free-text replies only. | JSON and intent labels are Latin by design; checking them would penalise every non-Latin language. |
| 2026-11-20 | Workers AI cost = measured neurons × $0.011 / 1,000. | Exact billing basis, returned with every call; no estimate needed. |
| 2026-11-20 | Neuron budget on every run (4,500 answers, 2,300 judge on the pilot day). | The 10,000 free neurons a day are shared with the portfolio's other live demos. Qwen 3.8 used 2,500 on its own because it reasons at length. |
| 2026-11-20 | Models run in parallel (one thread per model). | Free-tier latency is spiky (Llama 4 Scout took 30–40 s per answer); a sequential pilot would take over an hour. |
| 2026-11-20 | Ranked pilot models: Llama 3.3 70B, Llama 4 Scout, Mistral Small 3.1, gpt-oss-20b, Qwen 3.8 27B, GLM-4.7 Flash. | Five makers available on Workers AI. Qwen3 30B and Llama 3.1 8B fp8 were deprecated the same day. |
| 2026-11-20 | Leaderboard served as a Worker with static assets at scorecard.adityabal.com, not Pages. | Wrangler now routes Pages commands into Workers and project creation failed; static assets on Workers are the same free hosting. |
| 2026-11-20 | Cost shown in US$ until a rupee rate is set in prices.yaml. | No verified exchange rate; better no rupee figure than a wrong one. |
