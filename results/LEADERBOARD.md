# serbeval leaderboard

## Official set v1.1 (runs 2026-10-12 to 17; v1.1 re-score 2026-10-17)

**352 items**, each with a verification status (`data/official/MANIFEST.json`):
- 61 human-verified (disputed items checked by the maintainer + blind-baseline items);
- 214 model-consensus;
- 77 correction items derived from those.

v1.1 errata: 9 golds changed, 3 items dropped ([tasks/v1.1-izmene.md](../tasks/v1.1-izmene.md)).
Every model was re-scored from its saved answers with `scripts/rescore_official.py`; no request
was re-sent. Under v1 the top five were all at 98%.

The run: 30 models through OpenRouter, zero-shot, all in parallel. Every request got an answer
(0 provider give-ups).

| # | Model | MCQ | Cloze | Pravopis | Probni | Ispravljanje | Prosek | max unparsed |
|---|---|---|---|---|---|---|---|---|
| 1 | anthropic_claude-opus-5.5 | 100% | 100% | 99% | 99% | 100% | **100%** | 0.00 |
| 2 | openai_gpt-6.1-sol | 100% | 100% | 98% | 99% | 100% | **99%** | 0.00 |
| 3 | google_gemini-3.8-flash | 100% | 100% | 98% | 98% | 99% | **99%** | 0.00 |
| 4 | openai_gpt-6-sol | 100% | 100% | 97% | 97% | 100% | **99%** | 0.00 |
| 5 | openai_gpt-5.6-sol | 100% | 100% | 96% | 98% | 99% | **99%** | 0.00 |
| 6 | deepseek_deepseek-v4-pro | 98% | 100% | 93% | 93% | 94% | **96%** | 0.00 |
| 7 | openai_gpt-6-luna | 100% | 100% | 87% | 97% | 94% | **96%** | 0.00 |
| 8 | google_gemini-3.5-flash-lite | 100% | 100% | 92% | 88% | 97% | **95%** | 0.00 |
| 9 | x-ai_grok-4.7 | 100% | 89% | 89% | 96% | 100% | **95%** | 0.00 |
| 10 | anthropic_claude-sonnet-5.5 | 96% | 94% | 93% | 93% | 95% | **95%** | 0.00 |
| 11 | openai_gpt-5.6-luna | 100% | 100% | 84% | 91% | 95% | **94%** | 0.00 |
| 12 | moonshotai_kimi-k3 | 96% | 100% | 87% | 85% | 91% | **92%** | 0.00 |
| 13 | z-ai_glm-5.3 | 98% | 94% | 84% | 86% | 94% | **91%** | 0.05 |
| 14 | deepseek_deepseek-v4.1-flash | 100% | 100% | 82% | 85% | 88% | **91%** | 0.00 |
| 15 | google_gemma-4-31b-it | 98% | 100% | 76% | 80% | 92% | **89%** | 0.00 |
| 16 | deepseek_deepseek-v3.2 | 98% | 89% | 89% | 76% | 88% | **88%** | 0.00 |
| 17 | minimax_minimax-m3 | 96% | 100% | 74% | 79% | 88% | **87%** | 0.00 |
| 18 | qwen_qwen3.6-27b | 96% | 89% | 74% | 61% | 93% | **83%** | 0.00 |
| 19 | mistralai_mistral-large-4-0 | 98% | 89% | 70% | 69% | 85% | **82%** | 0.00 |
| 20 | qwen_qwen3-235b-a22b-2507 | 88% | 100% | 74% | 68% | 82% | **82%** | 0.05 |
| 21 | openai_gpt-5-mini | 90% | 89% | 67% | 63% | 88% | **79%** | 0.00 |
| 22 | anthropic_claude-haiku-5.5 | 93% | 89% | 60% | 62% | 89% | **79%** | 0.00 |
| 23 | nvidia_nemotron-3-ultra-550b-a55b | 91% | 94% | 54% | 64% | 80% | **77%** | 0.00 |
| 24 | meta-llama_llama-3.3-70b-instruct | 88% | 94% | 58% | 53% | 77% | **74%** | 0.05 |
| 25 | google_gemma-3-12b-it | 79% | 89% | 50% | 44% | 77% | **68%** | 0.00 |
| 26 | qwen_qwen3.5-9b | 86% | 83% | 46% | 37% | 75% | **66%** | 0.00 |
| 27 | nvidia_nemotron-3.5-lightning | 81% | 39% | 12% | 14% | 53% | **40%** | 0.00 |
| 28 | meta-llama_llama-3.1-8b-instruct | 48% | 50% | 23% | 21% | 55% | **39%** | 0.00 |
| 29 | mistralai_mistral-nemo | 69% | 33% | 12% | 15% | 67% | **39%** | 0.00 |
| 30 | cohere_command-a-plus | 74% | 33% | 19% | 28% | 37% | **38%** | 0.15 |

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
- **Five open-weights models ran on 2026-10-16**, after a suggestion to cover more open
  models: nemotron-3-ultra-550b-a55b (DeepInfra, fp4, its NVFP4 release), nemotron-3.5-lightning
  (DeepInfra, bf16), deepseek-v4-pro (StreamLake, fp8), qwen3.6-27b (Alibaba) and minimax-m3
  (MiniMax). Reasoning off; 0 empty answers, 0 unparsed. Total cost $0.04.
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

## Reasoning on vs off (2026-10-16/17)

Open-weights models rerun with thinking on, same provider and precision: `reasoning=low`
(`results/official-reasoning/`) and `reasoning=high` (`results/official-reasoning-high/`, token
floor 16384). Chart: `results/reasoning-compare.png`. The board above stays at reasoning off
for every model that allows it.

| Model | off | low | high | high: Pravopis / Ispravljanje |
|---|---|---|---|---|
| deepseek-v4-pro | 96% | 96% | **96%** | 91% / 99% |
| minimax-m3 | 87% | (excluded) | **87%** | 81% / 88% |
| qwen3.6-27b | 83% | not run | **84%** | 73% / 87% |
| nemotron-3-ultra-550b-a55b | 77% | 78% | **66%** | 46% / 58% |

(v1.1 numbers; under v1: 95/94/94, 87/–/87, 82/–/83, 76/78/65.)

High-run integrity: 355/355 answers per model, at most 2 empty, no provider give-ups.
Cost $1.5 for the four models.

- **Thinking does not buy Serbian.** No model gains more than 2 points at any effort.
- **Nemotron 3 Ultra gets worse at high** (77 → 66): it "corrects" sentences that were already
  right and introduces errors (*ućionici*, *spomenpark*, *niskim* for *ni s kim*).

Reasoning=low detail:

| Model | MCQ | Cloze | Pravopis | Probni | Ispravljanje | Prosek off → low |
|---|---|---|---|---|---|---|
| deepseek-v4-pro | 98% | 94% | 93% | 92% | 95% | 95% → **94%** |
| nemotron-3-ultra-550b-a55b | 95% | 83% | 68% | 74% | 69% | 76% → **78%** |
| minimax-m3 (see note) | 95% | 83% | 80% | 81% | 88% | 87% → *86%* |

- Thinking barely moves the average. For Nemotron it trades: pravopis rises 54 → 68, but
  correction falls 81 → 69.
- **minimax-m3 is not comparable**: 17 of 355 answers came back empty, some because the
  thinking used the whole 2048-token budget (`finish_reason: length`).
- qwen3.6-27b was not run at low (budget); it ran at high.
- Before this run the adapter sent the `\n\n` stop sequence with reasoning on; replies that
  open with a blank line after the thinking came back empty (21 of 68 in a DeepSeek smoke
  test, 0 of 21 when replayed without it). The adapter no longer sends stop sequences when
  reasoning is on.

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
