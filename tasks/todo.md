# serbeval — todo

Rationale for every decision: [DECISIONS.md](../DECISIONS.md). Current state: [HANDOFF.md](../HANDOFF.md).

## Next — difficulty probe set (agreed 2026-10-07, start in a new session)

The benchmark is correct but too easy: Opus 5.5 230/230, GPT 6.1 Sol 98% on the Kie triage run.
Measure before building — only phenomena where models drop below ~90% get a full set.

- [ ] 6 phenomena x 20 items = 120:
  - [ ] ijekavian jat reflex (rijeka / rječnik, mlijeko / mlječni) — synth from srLex
  - [ ] aorist & imperfect (rekoh, bijaše, donesoše) — synth, check srLex has these verb forms first
  - [ ] sibilarization / palatalization (junak→junaci, ruka→ruci, Bog→Bože) — synth from srLex
  - [ ] numeral + adjective + noun agreement (dva nova stola, dvadeset i jedan novi sto) — synth
  - [ ] pravopis together/apart (ne znam / neznanje, nemoj) — hand-written
  - [ ] polusloženice with a hyphen (kontakt-osoba, spomen-ploča, radio-stanica) — hand-written; the maintainer AND GPT missed kontakt-osoba
- [ ] Run both models through Kie: `KIE_API_KEY=... scripts/kie_triage.sh` (budget: under $1; GPT ~40 min)
- [ ] Keep only phenomena below ~90%; maintainer verifies only those
- [ ] Then: synth with RARE lemmas (srLex frequency column); then adversarial filtering through two model families
- Don't: remove the number hint from cues (ambiguous, not harder); trick questions

## Open — maintainer

- [ ] **Rotate the Kie key** — pasted into a terminal, printed in run logs
- [ ] **Add a git remote** — every commit lives only on this disk; a private repo is fine
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
