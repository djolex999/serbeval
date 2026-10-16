# serbeval leaderboard

## Official set v1 (2026-10-12)

**355 items**, each with a verification status (`data/official/MANIFEST.json`):
- 63 human-verified (33 disputed items checked by the maintainer + 30 blind-baseline items);
- 214 model-consensus;
- 78 correction items derived from those.

The run: 25 models through OpenRouter, zero-shot, all in parallel. Every request got an answer
(0 provider give-ups).

| # | Model | MCQ | Cloze | Pravopis | Probni | Ispravljanje | Prosek | max unparsed |
|---|---|---|---|---|---|---|---|---|
| 1 | anthropic_claude-opus-5.5 | 100% | 100% | 96% | 97% | 99% | **98%** | 0.00 |
| 2 | openai_gpt-6-sol | 98% | 100% | 97% | 96% | 98% | **98%** | 0.00 |
| 3 | google_gemini-3.8-flash | 100% | 100% | 94% | 97% | 98% | **98%** | 0.00 |
| 4 | openai_gpt-6.1-sol | 100% | 100% | 94% | 96% | 99% | **98%** | 0.00 |
| 5 | openai_gpt-5.6-sol | 100% | 100% | 95% | 95% | 98% | **98%** | 0.00 |
| 6 | anthropic_claude-sonnet-5.5 | 97% | 94% | 95% | 92% | 97% | **95%** | 0.00 |
| 7 | openai_gpt-6-luna | 100% | 100% | 85% | 96% | 93% | **95%** | 0.00 |
| 8 | x-ai_grok-4.7 | 100% | 89% | 91% | 95% | 98% | **94%** | 0.00 |
| 9 | google_gemini-3.5-flash-lite | 100% | 100% | 91% | 87% | 94% | **94%** | 0.00 |
| 10 | openai_gpt-5.6-luna | 98% | 100% | 80% | 89% | 96% | **93%** | 0.00 |
| 11 | moonshotai_kimi-k3 | 95% | 100% | 85% | 85% | 92% | **91%** | 0.00 |
| 12 | z-ai_glm-5.3 | 97% | 94% | 83% | 85% | 93% | **90%** | 0.05 |
| 13 | deepseek_deepseek-v4.1-flash | 100% | 100% | 79% | 83% | 88% | **90%** | 0.00 |
| 14 | google_gemma-4-31b-it | 97% | 100% | 77% | 78% | 92% | **89%** | 0.00 |
| 15 | deepseek_deepseek-v3.2 | 97% | 89% | 87% | 76% | 86% | **87%** | 0.00 |
| 16 | mistralai_mistral-large-4-0 | 97% | 89% | 70% | 69% | 85% | **82%** | 0.00 |
| 17 | qwen_qwen3-235b-a22b-2507 | 88% | 100% | 71% | 67% | 80% | **81%** | 0.05 |
| 18 | openai_gpt-5-mini | 90% | 89% | 66% | 62% | 87% | **79%** | 0.00 |
| 19 | anthropic_claude-haiku-5.5 | 93% | 89% | 57% | 62% | 88% | **78%** | 0.00 |
| 20 | meta-llama_llama-3.3-70b-instruct | 88% | 94% | 57% | 52% | 75% | **73%** | 0.05 |
| 21 | google_gemma-3-12b-it | 78% | 89% | 49% | 43% | 75% | **67%** | 0.00 |
| 22 | qwen_qwen3.5-9b | 85% | 83% | 45% | 36% | 76% | **65%** | 0.00 |
| 23 | mistralai_mistral-nemo | 68% | 33% | 12% | 15% | 68% | **39%** | 0.00 |
| 24 | meta-llama_llama-3.1-8b-instruct | 47% | 50% | 22% | 20% | 53% | **39%** | 0.00 |
| 25 | cohere_command-a-plus | 73% | 33% | 18% | 28% | 37% | **38%** | 0.15 |

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
- **The GPT-6 family ran on 2026-10-16**: gpt-6.1-sol (`reasoning=minimal`, mandatory, 0
  reasoning tokens in a spot check), gpt-6-sol and gpt-6-luna (reasoning off). It had been missed
  when the "newest per family" models were picked.
- **Nine newer models ran on 2026-10-13**: claude-opus-5.5, gpt-5.6-sol, gpt-5.6-luna,
  grok-4.7, mistral-large-4-0, deepseek-v4.1-flash, kimi-k3, glm-5.3 and command-a-plus. Each
  ran on its first-party provider or at native precision (kimi-k3 via Moonshot AI,
  deepseek-v4.1-flash via DeepSeek, glm-5.3 at fp8). Opus, grok-4.7 and glm-5.3 cannot disable
  reasoning and ran at `reasoning=minimal`. command-a-plus ran at `reasoning=low,stop=off`:
  with any stop sequence its API returns empty content (229/355 empty), which measured the
  API, not Serbian.
- **Two models ran a day later**, on the same set with the same settings: gemma-3-12b-it,
  after its only bf16 provider had rate-limited it (HTTP 429) for the whole first run, and
  gemini-3.8-flash, at \`reasoning=minimal\`, which used 0 reasoning tokens in a spot check.
- **Possible selection bias.** The four consensus models (sonnet-5.5, gemini-3.5-flash-lite,
  gemma-4-31b, deepseek-v3.2) are also ranked here. The top five (opus-5.5, gpt-6-sol, gemini-3.8-flash, gpt-6.1-sol, gpt-5.6-sol) are not among them. Items where they disagreed with the gold
  were human-checked, not removed, and only 3 of 250 core items left the set for any reason
  (1 unsure, 2 judged bad). The bias toward those four is small but not zero.
- **Opus now has an official number** (98%, through OpenRouter's first-party Anthropic
  route). The earlier ~97–100% came from reseller triage and was never reportable.

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
