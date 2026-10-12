# serbeval leaderboard

## Official set v1 (2026-10-12)

**355 items**, each with a verification status (`data/official/MANIFEST.json`):
- 63 human-verified (33 disputed items checked by the maintainer + 30 blind-baseline items);
- 214 model-consensus;
- 78 correction items derived from those.

The run: 13 models through OpenRouter, zero-shot, all in parallel. Every request got an answer
(0 provider give-ups).

| # | Model | MCQ | Cloze | Pravopis | Probni | Ispravljanje | Prosek | max unparsed |
|---|---|---|---|---|---|---|---|---|
| 1 | google_gemini-3.8-flash | 100% | 100% | 94% | 97% | 98% | **98%** | 0.00 |
| 2 | anthropic_claude-sonnet-5.5 | 97% | 94% | 95% | 92% | 97% | **95%** | 0.00 |
| 3 | google_gemini-3.5-flash-lite | 100% | 100% | 91% | 87% | 94% | **94%** | 0.00 |
| 4 | google_gemma-4-31b-it | 97% | 100% | 77% | 78% | 92% | **89%** | 0.00 |
| 5 | deepseek_deepseek-v3.2 | 97% | 89% | 87% | 76% | 86% | **87%** | 0.00 |
| 6 | qwen_qwen3-235b-a22b-2507 | 88% | 100% | 71% | 67% | 80% | **81%** | 0.05 |
| 7 | openai_gpt-5-mini | 90% | 89% | 66% | 62% | 87% | **79%** | 0.00 |
| 8 | anthropic_claude-haiku-5.5 | 93% | 89% | 57% | 62% | 88% | **78%** | 0.00 |
| 9 | meta-llama_llama-3.3-70b-instruct | 88% | 94% | 57% | 52% | 75% | **73%** | 0.05 |
| 10 | google_gemma-3-12b-it | 78% | 89% | 49% | 43% | 75% | **67%** | 0.00 |
| 11 | qwen_qwen3.5-9b | 85% | 83% | 45% | 36% | 76% | **65%** | 0.00 |
| 12 | mistralai_mistral-nemo | 68% | 33% | 12% | 15% | 68% | **39%** | 0.00 |
| 13 | meta-llama_llama-3.1-8b-instruct | 47% | 50% | 22% | 20% | 53% | **39%** | 0.00 |

How it was run:
- Reasoning is off where a model allows it. gemini-3.5-flash-lite, gpt-5-mini and
  claude-sonnet-5.5 cannot turn it off, so they ran at `reasoning=minimal`, which used 0
  reasoning tokens in spot checks.
- Open-weights models were pinned to full precision (bf16/fp16). qwen3-235b-2507 and
  deepseek-v3.2 ran at fp8, their native release. The providers are in the logs under
  `results/official/`.
- Group score = mean task accuracy in the group. Prosek = mean of the five groups. The
  official Cloze group has only 18 items, so read it loosely.

**Read before citing:**
- **Two models ran a day later**, on the same set with the same settings: gemma-3-12b-it,
  after its only bf16 provider had rate-limited it (HTTP 429) for the whole first run, and
  gemini-3.8-flash, at \`reasoning=minimal\`, which used 0 reasoning tokens in a spot check.
- **Possible selection bias.** The four consensus models (sonnet-5.5, gemini-3.5-flash-lite,
  gemma-4-31b, deepseek-v3.2) are also ranked here. gemini-3.8-flash, the top model, is not one of them. Items where they disagreed with the gold
  were human-checked, not removed, and only 3 of 250 core items left the set for any reason
  (1 unsure, 2 judged bad). The bias toward those four is small but not zero.
- **No reportable Opus number.** Claude Opus 5.5 scored ~97–100% on every group in reseller
  triage runs, which are not reportable.

Reproduce:
```
TASKS=srb_official RESULTS=results/official scripts/openrouter_eval.sh <model> [args]
scripts/leaderboard.py results/official --official
```

## Preliminary full-suite run (2026-10-08)

This run used all 1394 items, mostly unverified, including mined and synthesised cloze. It is
kept for comparison. The official table above supersedes it.

| # | Model | MCQ | Cloze | Pravopis | Probni | Ispravljanje | Prosek | max unparsed |
|---|---|---|---|---|---|---|---|---|
| 1 | anthropic_claude-sonnet-5.5 | 97% | 96% | 92% | 92% | 96% | **94%** | 0.00 |
| 2 | google_gemini-3.5-flash-lite | 99% | 91% | 88% | 85% | 93% | **91%** | 0.00 |
| 3 | deepseek_deepseek-v3.2 | 92% | 93% | 82% | 76% | 90% | **87%** | 0.00 |
| 4 | google_gemma-4-31b-it | 92% | 93% | 74% | 78% | 92% | **86%** | 0.04 |
| 5 | qwen_qwen3-235b-a22b-2507 | 84% | 95% | 74% | 68% | 84% | **81%** | 0.13 |
| 6 | openai_gpt-5-mini | 90% | 88% | 63% | 67% | 88% | **79%** | 0.00 |
| 7 | anthropic_claude-haiku-5.5 | 89% | 81% | 58% | 58% | 90% | **75%** | 0.03 |
| 8 | meta-llama_llama-3.3-70b-instruct | 86% | 81% | 56% | 52% | 74% | **70%** | 0.00 |
| 9 | google_gemma-3-12b-it | 82% | 80% | 50% | 41% | 72% | **65%** | 0.00 |
| 10 | qwen_qwen3.5-9b | 86% | 61% | 45% | 37% | 78% | **61%** | 0.00 |
| 11 | meta-llama_llama-3.1-8b-instruct | 50% | 47% | 22% | 21% | 56% | **39%** | 0.00 |
| 12 | mistralai_mistral-nemo | 64% | 26% | 13% | 14% | 66% | **36%** | 0.00 |
