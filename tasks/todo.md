# serbeval — todo

Rationale for every decision: [DECISIONS.md](../DECISIONS.md). Current state: [HANDOFF.md](../HANDOFF.md).

## Next — official verified set + public leaderboard (agreed 2026-10-08)

- [x] Select ~250 items for the official set (all probe + pravopis + correction, sample of MCQ/cloze)
- [x] Maintainer checked the 36 DISPUTED items (2026-10-09): 33 verified, 1 unsure, 2 dropped; other 214 = model consensus
- [x] Official set v1 (355) built; 22 models run in parallel; official leaderboard in README
- [ ] Re-send items that got empty provider responses (qwen3-235b, gemma-4-31b)
- [ ] README: leaderboard table + chart + methodology (srLex-attested gold, contested norm, unparsed)
- [x] Published: GitHub public (2026-10-12), Hugging Face djolex999/serbeval (2026-10-13)
- [ ] Optional: PR to lm-evaluation-harness
- [ ] Optional: Opus 5.5 via OpenRouter (~$3-10, mandatory thinking) as the reportable ceiling

## Done 2026-10-07/08 — difficulty work and first leaderboard

- [x] Probe set (6 phenomena), srb_pravopis (82, source-checked), srb_correction (90, cue-free): Opus at ceiling on all
- [x] srLex: aorist attested, imperfect generated (hand-written); gold only from freq>0 forms
- [x] Hyphen-aware cloze scoring; slot read from a repeated sentence; request timeouts
- [x] openrouter-chat adapter + scripts; 12-model preliminary leaderboard (36-94%), $1.21

## Open — maintainer

- [ ] **Revoke keys** — Kie (terminal/logs) and OpenRouter `serbeval` (pasted in chat)
- [ ] Judge the remaining review-queue items: standard-0003 („da se ponesu“), idiomi-b-0008 (luk jeo), cloze-ud-0027 (date in parentheses)
- [ ] Verify more items: `serbeval review --task <task>` (30 / 1102 verified so far)
- [ ] First-party run for reportable numbers (needs ANTHROPIC_API_KEY; `pip install -e ".[dev]"` already done)

## Open — small fixes

- [ ] Miner: skip blanks adjacent to brackets/digits (cloze-ud-0027 confused GPT)
- [ ] Optional: re-send the 6 requests Kie never answered (listed by `serbeval triage`)

## Done (condensed — details in DECISIONS.md and git log)

- [x] v0.1–v0.3: schema, validate, 3 MCQ tasks, generate/selfcheck, review, stats, report, cyrillic pair metric
- [x] lint (distractor quality), Wilson-CI report with rankability verdict, difficulty tier
- [x] cloze format; `mine` (UD treebank, 453), `synth` (frames + srLex, 519); `check` (language QA, 0.012% FP)
- [x] `unparsed` metric, human `baseline`, `balance` (position bias 60%/80% always-A → ~26%)
- [x] adapters: `anthropic-chat-fixed` (temperature/thinking/string prompts/Opus 5.5), `kie-responses`; patient retry
- [x] licensing: code MIT, data split CC BY / CC BY-SA (data/LICENSE)
- [x] 2026-10-07: first real API runs (Kie) — smoke + full triage: Opus 230/230, GPT 220/224 → ceiling
- [x] 2026-10-07: human baseline 29/30 (97%); those 30 items marked verified
