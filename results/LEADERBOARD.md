# serbeval leaderboard — PRELIMINARY (2026-10-08)

**Not for citation yet.** Only 30 of ~1400 items are human-verified, so these numbers show
how far apart models are, not final scores. They will be re-run on a verified set.

- 12 models through OpenRouter, zero-shot, the full suite (1394 items per model).
- Reasoning off where a model allows it. gemini-3.5-flash-lite, gpt-5-mini and
  claude-sonnet-5.5 do not, so they ran at `reasoning=minimal`, which used 0 reasoning
  tokens in spot checks.
- Open-weights models were restricted to full precision (bf16/fp16). qwen3-235b-2507
  and deepseek-v3.2 ran at fp8, their native release precision. The providers that
  served each run are in `results/openrouter/<model>.log`.
- `max unparsed` is the worst task's share of empty or unreadable responses. Empty
  responses came from provider failures, so those models are slightly underscored.
- Group score = mean of the task accuracies in the group. Prosek = mean of the five groups.
- For reference: Opus 5.5 scored ~97–100% on every group in triage runs through Kie.
  That is a reseller, so the number is not reportable.

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

Reproduce one row: `OPENROUTER_API_KEY=... scripts/openrouter_eval.sh <model> [model_args]`,
then `scripts/leaderboard.py`.
