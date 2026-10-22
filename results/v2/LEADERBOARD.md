# serbeval v2 — first run (2026-10-22)

Chart: `results/v2/leaderboard-v2.png` (`python3 scripts/leaderboard_chart.py --v2`).

76 verified passages (data/v2/evaluation.json), 218 required error sites, 18 clean passages; format A (correct the whole passage, no cue). Routing as in the official v1 runs; one request per passage, reasoning off where the model allows it. Scorer: serbeval.passage (per-edit; case, punctuation and script folded). Reproduce: `PYTHONPATH=src python scripts/pilot_passage.py report v2 all`.

## How much harder? Two numbers, not one

"Passages fully correct" is all-or-nothing over ~4 errors per passage, so it falls faster than
per-error accuracy (a model fixing 89% of errors gets all 4 in a passage only ~63% of the time).
The like-for-like comparison with v1.2 is **errors fixed**: frontier models make roughly 5–10×
more mistakes on v2 (Opus 2% → 11%, GPT-6 Sol 1% → 14%). The errors were deliberately placed
where common usage diverges from Pravopis 2010, so v2 measures adherence to the norm in exactly
those spots, not general Serbian ability.

| Model | v1.2 (items correct) | v2: errors fixed | v2: passages fully correct |
|---|---|---|---|
| Claude Opus 5.5 | 98% | 89% | **74%** |
| GPT-6 Sol | 99% | 86% | **72%** |
| DeepSeek V4 Pro | 95% | 75% | **61%** |
| DeepSeek V4.1 Flash | 90% | 72% | **55%** |
| DeepSeek V3.2 | 88% | 75% | **50%** |
| GLM-5.3 | 90% | 69% | **50%** |
| Kimi K3 | 92% | 70% | **49%** |
| Qwen3.6 27B | 83% | 58% | **41%** |
| Qwen3 235B | 81% | 59% | **38%** |
| Gemma 3 12B | 67% | 46% | **34%** |
| Llama 3.3 70B | 73% | 56% | **30%** |
| Nemotron 3 Ultra | 77% | 53% | **30%** |
| Gemma 4 31B | 89% | 63% | **29%** |
| MiniMax M3 | 87% | 40% | **28%** |
| Qwen3.5 9B | 66% | 54% | **28%** |
| Mistral Nemo | 39% | 38% | **21%** |
| Llama 3.1 8B | 39% | 37% | **13%** |
| Nemotron 3.5 Lightning | 40% | 25% | **13%** |

## Full v2 table

| Model | Passage exact | Error passages exact | Clean left intact | Errors fixed (recall) | Precision | False alarms | Unparsed |
|---|---|---|---|---|---|---|---|
| anthropic/claude-opus-5.5 | 56/76 | 43/58 | 13/18 | 89% (193/218) | 96% | 7 | 0 |
| openai/gpt-6-sol | 55/76 | 38/58 | 17/18 | 86% (188/218) | 99% | 1 | 0 |
| deepseek/deepseek-v4-pro | 46/76 | 28/58 | 18/18 | 75% (163/218) | 99% | 1 | 0 |
| deepseek/deepseek-v4.1-flash | 42/76 | 24/58 | 18/18 | 72% (157/218) | 100% | 0 | 0 |
| z-ai/glm-5.3 | 38/76 | 22/58 | 16/18 | 69% (150/218) | 97% | 5 | 0 |
| deepseek/deepseek-v3.2 | 38/76 | 24/58 | 14/18 | 75% (164/218) | 90% | 19 | 0 |
| moonshotai/kimi-k3 | 37/76 | 25/58 | 12/18 | 70% (153/218) | 95% | 8 | 0 |
| qwen/qwen3.6-27b | 31/76 | 15/58 | 16/18 | 58% (126/218) | 95% | 7 | 0 |
| qwen/qwen3-235b-a22b-2507 | 29/76 | 17/58 | 12/18 | 59% (128/218) | 91% | 13 | 0 |
| google/gemma-3-12b-it | 26/76 | 10/58 | 16/18 | 46% (101/218) | 93% | 8 | 0 |
| nvidia/nemotron-3-ultra-550b-a55b | 23/76 | 13/58 | 10/18 | 53% (116/218) | 80% | 29 | 0 |
| meta-llama/llama-3.3-70b-instruct | 23/76 | 10/58 | 13/18 | 56% (121/218) | 75% | 40 | 0 |
| google/gemma-4-31b-it | 22/76 | 11/58 | 11/18 | 63% (137/218) | 91% | 13 | 0 |
| qwen/qwen3.5-9b | 21/76 | 9/58 | 12/18 | 54% (118/218) | 87% | 17 | 0 |
| minimax/minimax-m3 | 21/76 | 5/58 | 16/18 | 40% (88/218) | 88% | 12 | 1 |
| mistralai/mistral-nemo | 16/76 | 4/58 | 12/18 | 38% (82/218) | 66% | 42 | 1 |
| nvidia/nemotron-3.5-lightning | 10/76 | 2/58 | 8/18 | 25% (55/218) | 49% | 58 | 1 |
| meta-llama/llama-3.1-8b-instruct | 10/76 | 4/58 | 6/18 | 37% (80/218) | 52% | 75 | 13 |
| cohere/command-a-plus | 9/76 | 1/58 | 8/18 | 22% (48/218) | 37% | 82 | 21 |

**Read before citing:**
- **Frontier is no longer at ceiling.** Opus 5.5 and GPT-6 Sol: 74% / 72% exact passages (v1.2: 98–99%). Their remaining errors are mostly usage over norm: hyphenated *kontakt-*, *ekspres-*, *džez-*, *hteo-ne hteo*, joined *nabrzinu*, *do viđenja*, *austro-ugarski*.
- **Command A+ is unreliable**: its API returned 9 empty answers even after a re-send (21 unparsed).
- **Qwen3 235B** was re-run pinned to Parasail: DeepInfra returned broken English word lists on 2026-10-22.
- **Gold fixes found by this run** (no source text changed): see DECISIONS.md 2026-10-22.
- Passages were written partly by Claude, partly taken from official texts; Opus may be favoured on the handwritten half.
