# serbeval — todo

Rationale for every decision: [DECISIONS.md](../DECISIONS.md). Current state: [HANDOFF.md](../HANDOFF.md).

## Next — Aleksa Gordić's feedback on the LinkedIn post (2026-10-16)

- [x] Nemotron 3 Ultra + 4 more open-weights models on the board (30 total); Nemotron 3 Ultra 76%
- [x] Reasoning off/low/high comparison (results/reasoning-compare.png): no model gains >2 pts; Nemotron drops to 65% at high
- [x] Open-weights-only chart (results/leaderboard-open.png); licenses from HF tags. Add Mistral Large 4 once its weights ship (announced late Oct)
- [x] v1.1 errata (rule-based), then v1.2: every orthography gold checked against the text of Pravopis 2010 (351 items, published GitHub + HF); GPT-6 Sol 99%, DeepSeek V4 Pro 95%
- [x] v2 pilot, format A (30 passages, per-edit scoring, 4 models, $0.06): Opus 20/22, GPT-6 Sol 18/22; 5 source-confirmed frontier errors → format A passes
- [x] Replied to Aleksa on LinkedIn
- [x] Follow-up for Aleksa: open-weights + reasoning charts posted

## Next — serbeval v2 (plan: tasks/v2-plan.md)

- [ ] Draft first 50 format-A passages (5–7 sentences, 4–6 errors, ~30% Cyrillic, ~25% clean); every gold cites Pravopis 2010 tačka/page
- [ ] Error inventory = usage-vs-norm traps (ekspres/kontakt/džez apart, vikend-kuća, na brzinu, bilo gde, usput/uz put, naučnofantastični, hteo – ne hteo, greška) + over-correction traps (do kasno, nijedan, ni s kim)
- [ ] Maintainer writes ≥ half of the passages (Claude-written text may favour Opus); verify all in the HTML sheet
- [ ] Automatic rečnik lookup for each gold (OCR of Pravopis 2010 stays local, never committed)
- [ ] Panel-based selection + 20% random slice; then v2 board on 30 models (~$2–3), chart, post

## Open — lm-evaluation-harness PR

- [ ] Sign the CLA on EleutherAI/lm-evaluation-harness#4400 (CLAassistant comment)
- [ ] Watch for maintainer review / CI approval; address comments in the fork branch `add-serbeval`
- [ ] PR reads the HF dataset, now v1.2 (351 items): update any 355-item / v1 numbers in the PR text

## Open — maintainer

- [ ] **Revoke keys**: Kie, and the OpenRouter keys pasted in chat (2026-10-12 and 2026-10-16; the latter expires 2026-10-17 12:02 CEST)
- [ ] Visually check the OCR'd Pravopis pages the golds cite (str. 87, 280, 311–312, 349, 497, 502)
- [ ] Delete local branch `backup/before-coauthor-rewrite` once happy with the rewritten history
- [ ] Judge the remaining review-queue items: standard-0003 („da se ponesu“), idiomi-b-0008 (luk jeo), cloze-ud-0027 (date in parentheses)

## Open — small fixes

- [ ] Re-send items that got empty provider responses in the preliminary run (qwen3-235b, gemma-4-31b)
- [ ] Miner: skip blanks adjacent to brackets/digits (cloze-ud-0027 confused GPT)

## Done 2026-10-08 → 16 — official set, publication, PR

- [x] Verification: `serbeval verify` (sheet + offline HTML, `--disputed`); maintainer checked 36 disputed items (33 ok/fixed, 1 unsure, 2 dropped)
- [x] Official set v1: 355 items (63 human, 214 consensus, 78 derived), `*_official` tasks, MANIFEST.json
- [x] Official leaderboard: 25 models via OpenRouter, all in parallel (38–98%, five at 98%); chart `results/leaderboard.png`
- [x] Published: GitHub public (2026-10-12), Hugging Face `djolex999/serbeval` (2026-10-13), LinkedIn post (2026-10-16)
- [x] History rewritten to drop the Claude co-author trailer; `attribution` emptied in ~/.claude/settings.json
- [x] PR EleutherAI/lm-evaluation-harness#4400: 17 `serbeval_*` tasks, self-contained utils.py, 25,603 responses re-scored identically

## Done 2026-10-07/08 — difficulty work and first leaderboard

- [x] Probe set, srb_pravopis (source-checked), srb_correction (cue-free): Opus at ceiling on all
- [x] openrouter-chat adapter + scripts; preliminary 12-model leaderboard (36–94%)

## Done (condensed — details in DECISIONS.md and git log)

- [x] v0.1–v0.3: schema, validate, MCQ tasks, generate/selfcheck, review, stats, report, cyrillic pair metric
- [x] cloze format; `mine` (UD, 453), `synth` (srLex, 519); `check` (language QA, 0.012% FP)
- [x] `unparsed` metric, human `baseline` (29/30), `balance` (position bias fixed)
- [x] licensing: code MIT, data split CC BY / CC BY-SA (data/LICENSE)
