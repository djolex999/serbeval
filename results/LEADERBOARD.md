# serbeval leaderboard

## Official set v1.2 (runs 2026-10-12 to 17; re-scored 2026-10-17)

**351 items**, each with a verification status (`data/official/MANIFEST.json`):
- 61 human-verified (disputed items checked by the maintainer + blind-baseline items);
- 214 model-consensus;
- 76 correction items derived from those.

Errata: v1.1 changed 9 golds and dropped 3 items ([tasks/v1.1-izmene.md](../tasks/v1.1-izmene.md));
v1.2 re-checked them, and then all 120 orthography golds, against the text of Pravopis 2010
([reports/Provera srpske pravopisne norme.md](../reports/Provera%20srpske%20pravopisne%20norme.md)).
Every model was re-scored from its saved answers with `scripts/rescore_official.py`; no request
was re-sent. Under v1 the top five were all at 98%.

The run: 30 models through OpenRouter, zero-shot, all in parallel. Every request got an answer
(0 provider give-ups).

| # | Model | MCQ | Cloze | Pravopis | Probni | Ispravljanje | Prosek | max unparsed |
|---|---|---|---|---|---|---|---|---|
| 1 | openai_gpt-6-sol | 100% | 100% | 99% | 96% | 99% | **99%** | 0.00 |
| 2 | google_gemini-3.8-flash | 100% | 100% | 95% | 97% | 98% | **98%** | 0.00 |
| 3 | anthropic_claude-opus-5.5 | 100% | 100% | 95% | 96% | 99% | **98%** | 0.00 |
| 4 | openai_gpt-6.1-sol | 100% | 100% | 94% | 97% | 99% | **98%** | 0.00 |
| 5 | openai_gpt-5.6-sol | 100% | 100% | 92% | 97% | 98% | **97%** | 0.00 |
| 6 | deepseek_deepseek-v4-pro | 98% | 100% | 89% | 90% | 95% | **95%** | 0.00 |
| 7 | openai_gpt-6-luna | 100% | 100% | 83% | 96% | 94% | **94%** | 0.00 |
| 8 | anthropic_claude-sonnet-5.5 | 96% | 94% | 92% | 92% | 96% | **94%** | 0.00 |
| 9 | x-ai_grok-4.7 | 100% | 89% | 89% | 95% | 99% | **94%** | 0.00 |
| 10 | google_gemini-3.5-flash-lite | 100% | 100% | 88% | 87% | 95% | **94%** | 0.00 |
| 11 | openai_gpt-5.6-luna | 100% | 100% | 82% | 89% | 96% | **93%** | 0.00 |
| 12 | moonshotai_kimi-k3 | 96% | 100% | 86% | 85% | 92% | **92%** | 0.00 |
| 13 | deepseek_deepseek-v4.1-flash | 100% | 100% | 79% | 85% | 89% | **90%** | 0.00 |
| 14 | z-ai_glm-5.3 | 98% | 94% | 82% | 85% | 93% | **90%** | 0.05 |
| 15 | google_gemma-4-31b-it | 98% | 100% | 76% | 79% | 93% | **89%** | 0.00 |
| 16 | deepseek_deepseek-v3.2 | 98% | 89% | 88% | 76% | 87% | **88%** | 0.00 |
| 17 | minimax_minimax-m3 | 96% | 100% | 73% | 77% | 89% | **87%** | 0.00 |
| 18 | qwen_qwen3.6-27b | 96% | 89% | 76% | 60% | 94% | **83%** | 0.00 |
| 19 | mistralai_mistral-large-4-0 | 98% | 89% | 69% | 70% | 86% | **82%** | 0.00 |
| 20 | qwen_qwen3-235b-a22b-2507 | 88% | 100% | 72% | 67% | 80% | **81%** | 0.05 |
| 21 | openai_gpt-5-mini | 90% | 89% | 66% | 62% | 87% | **79%** | 0.00 |
| 22 | anthropic_claude-haiku-5.5 | 93% | 89% | 59% | 62% | 89% | **78%** | 0.00 |
| 23 | nvidia_nemotron-3-ultra-550b-a55b | 91% | 94% | 54% | 63% | 82% | **77%** | 0.00 |
| 24 | meta-llama_llama-3.3-70b-instruct | 88% | 94% | 57% | 52% | 75% | **73%** | 0.05 |
| 25 | google_gemma-3-12b-it | 79% | 89% | 49% | 44% | 75% | **67%** | 0.00 |
| 26 | qwen_qwen3.5-9b | 86% | 83% | 47% | 37% | 76% | **66%** | 0.00 |
| 27 | nvidia_nemotron-3.5-lightning | 81% | 39% | 12% | 14% | 54% | **40%** | 0.00 |
| 28 | mistralai_mistral-nemo | 69% | 33% | 12% | 15% | 68% | **39%** | 0.00 |
| 29 | meta-llama_llama-3.1-8b-instruct | 48% | 50% | 23% | 21% | 54% | **39%** | 0.00 |
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
| deepseek-v4-pro | 95% | 94% | **94%** | 89% / 98% |
| minimax-m3 | 87% | (excluded) | **86%** | 79% / 87% |
| qwen3.6-27b | 83% | not run | **83%** | 72% / 88% |
| nemotron-3-ultra-550b-a55b | 77% | 77% | **66%** | 46% / 59% |

(v1.2 numbers; under v1: 95/94/94, 87/–/87, 82/–/83, 76/78/65.)

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
