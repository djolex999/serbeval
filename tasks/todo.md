# serbeval — active task list

Full plan: [docs/superpowers/plans/2026-06-13-serbeval-v0.1.md](../docs/superpowers/plans/2026-06-13-serbeval-v0.1.md)
Status at end of autonomous build: [HANDOFF.md](../HANDOFF.md)

## v0.1 — DONE
- [x] 1. Scaffolding (git, venv, pyproject, README, DECISIONS.md)
- [x] 2. EvalItem schema (pydantic, TDD)
- [x] 3. Dataset IO + `serbeval validate` CLI
- [x] 4. Seed datasets: srb_grammar (50), srb_idioms (30) — multi-agent authored + adversarially verified, all `verified: false`
- [x] 5. lm-eval task YAMLs (generate_until + regex filter)
- [x] 6. `serbeval generate` candidate generation (mock-tested; live run needs API key)
- [x] 7. Run docs + results/ layout
- [x] 8. pytest + mypy + ruff green

## v0.2 — DONE
- [x] 9. Self-consistency filter `serbeval selfcheck` (mock-tested)
- [x] 10. srb_cyrillic_agreement — formal harness task (custom pair_agreement metric; 15 pairs)
- [x] 11. Smoke run — pipeline validated via lm-eval `dummy` model; live haiku command documented (no API key on machine)
- [x] 12. CONTRIBUTING.md + issue templates
- [x] 13. Final checks + HANDOFF.md

## v0.3 — human-verification tooling (in progress)
- [x] 14. `serbeval review` — interactive verification: y/n/s/q per item, pair-atomic for
      srb_cyrillic_agreement, saves after every decision, rejects → discarded.jsonl with reason
- [x] 15. `serbeval stats` — per-task verification progress + category/candidate/discard counts
- [x] 16. `serbeval report` — markdown summary table from lm-eval `results_*.json` under results/
- [x] 17. pytest + mypy + ruff green; adversarial review workflow (26 agents, 17 confirmed
      findings → all fixed: atomic saves, reject ordering, recursive report discovery, …); docs updated

## Needs maintainer (see HANDOFF.md)
- [ ] Human-verify seed items → flip `verified: true`
- [ ] Live haiku-4-5 smoke run + full model matrix (needs ANTHROPIC_API_KEY)
- [ ] Expand thin `glagolski-vid` category (only 4 items survived verification)

## v0.3 — measurement tooling — DONE (2026-09-02)
- [x] 14. `difficulty` tier on EvalItem + pair difficulty-consistency rule
- [x] 15. `serbeval lint` — advisory distractor quality report (never fails)
- [x] 16. `serbeval report` — Wilson CI, model spread, "cannot rank" verdict, script gap by tier
- [x] 17. Tag the 30 srb_cyrillic_agreement items `easy`
- [x] 18. pytest (96) + mypy + ruff green; report verified against real `dummy` lm-eval output

## v0.4 — dataset work, driven by lint output
- [ ] Rewrite distractors in `standard` (0.29), `kongruencija` (0.33), `komparacija` (0.40), `pravopis` (0.41) — 24 of 50 grammar items are effectively 2-way MCQ
- [ ] Expand `srb_cyrillic_agreement` to ~60 pairs across easy/medium/hard, so the script gap can be measured against difficulty
- [ ] Re-aim `srb_idioms` at rare/regional expressions, or drop the task
- [ ] Scale `srb_grammar` toward 300 items (needs ANTHROPIC_API_KEY for generate/selfcheck)

## Still needs maintainer
- [ ] Human-verify seed items → flip `verified: true`
- [ ] **Run the model matrix and check the benchmark discriminates at all** (needs ANTHROPIC_API_KEY).
      If haiku and opus land within ~10 points, more items will not help and the item difficulty
      is what needs changing. This gates all of v0.4.

## v0.4 — cloze prototype — DONE (2026-09-02)
- [x] 19. `ClozeItem` schema + cloze scoring (diacritic-strict exact match, multi-answer)
- [x] 20. 20 cloze items across padezi / brojevi / komparacija / glagolski-oblici
- [x] 21. `srb_grammar_cloze` lm-eval task; `serbeval validate` auto-detects cloze files
- [x] 22. 159 tests + mypy + ruff green; harness integration test on the new task

## The one experiment that decides everything (needs ANTHROPIC_API_KEY)
- [ ] Run haiku + opus + one non-Anthropic model on all four tasks with --log_samples
- [ ] `serbeval report --results-dir results` → is any spread larger than the CI?
- [ ] Compare `srb_grammar` vs `srb_grammar_cloze` accuracy. If cloze is materially harder,
      convert srb_grammar to cloze and retire the MCQ distractor problem entirely.

## v0.5 — corpus mining — DONE (2026-09-02)
- [x] 23. CoNLL-U reader (`serbeval.conllu`)
- [x] 24. `serbeval mine` — corpus-driven cloze generation, purity computed not hardcoded
- [x] 25. 453 candidates mined from UD_Serbian-SET, validate clean

## Next on mining
- [ ] Spot-check a random sample of the 453 (say 40) and merge the good ones into items.jsonl
- [ ] Second phenomenon: numeral + noun (paukal) — annotated in the treebank, same approach
- [ ] Contamination fix: tag recent Serbian news with a UD tagger, run the same miner over it
- [ ] Consider `u`/`na` as a deliberately HARD tier (needs the verb, not just the preposition)

## v0.6 — synthesis — DONE (2026-09-02)
- [x] 26. srLex reader (`serbeval.lexicon`) — paradigms, all variant forms per slot
- [x] 27. `serbeval synth` — 24 frames x semantic roles x srLex, 519 items, validate clean
- [x] 28. Motion-vs-rest hard tier (`u`/`na`), impossible to mine

## Next
- [ ] Human-check the 24 FRAMES (not the 519 items) — that is the whole verification cost now
- [ ] Run mined vs synthetic on the same models: the gap estimates contamination
- [ ] More frames: numerals/paukal, comparatives, verb forms
- [ ] Still open and still gating: does the benchmark separate models at all? (needs API key)

## v0.7 — output checker — DONE (2026-09-02)
- [x] 29. `serbeval check` — mixed script, diacritics, unknown forms, dialect mixing
- [x] 30. `serbeval index` + committed data/forms.txt.gz (1.45M forms, no download needed)
- [x] 31. False-positive rate measured on real Serbian: 0.012% in low-noise mode

## Usable today (no API key)
- [ ] Wire `serbeval check` into Pripremi.rs output as a quality gate
- [ ] Optional next tier: preposition-case government on free text (needs a tagger)

## v0.8 — validation-run prep — DONE (2026-09-02)
- [x] 32. `unparsed` metric on all six tasks — a response we cannot read != a wrong answer
- [x] 33. Task YAMLs for the mined and synthetic candidate sets (contamination comparison)
- [x] 34. `serbeval baseline --new / --score` — the human control

## The run itself (needs ANTHROPIC_API_KEY) — see results/README.md
- [ ] Answer 30 baseline items yourself FIRST. Below ~100% means fix items, not models.
- [ ] haiku + opus + one non-Anthropic model, all six tasks, --log_samples
- [ ] `serbeval report --results-dir results` — check `unparsed` before believing accuracy
- [ ] Pull the items every model failed; those are the verification queue

## v0.9 — working adapter — DONE (2026-09-02)
- [x] 35. `anthropic-chat-fixed` — drops `temperature`, reads text past thinking blocks
- [x] 36. `scripts/run_eval.py` wrapper; stock adapter left registered for comparison
- [x] 37. Verified end-to-end through the harness with the dummy model

## v0.10 — Opus 5.5 + missing API extras — DONE (2026-09-23)
- [x] 38. `lm-eval[api]` declared — without it no API model ran at all
- [x] 39. `thinking=omit` + fail-fast for models that cannot disable thinking (Opus 5.5)
- [x] 40. max_tokens floor of 2048 whenever thinking is on
- [ ] Maintainer: `.venv/bin/pip install -e ".[dev]"` to pull tenacity + tiktoken

## v0.11 — Kie triage, ready to run — DONE (2026-10-07)
- [x] 41. `lm-eval[api]` extras installed (tenacity, tiktoken)
- [x] 42. Adapter accepts string prompts — every documented command was broken without --apply_chat_template
- [x] 43. `kie-responses` adapter for gpt-6-1-sol (Responses format); Opus via anthropic-chat-fixed + base_url
- [x] 44. Key routing by destination; stream=false; e2e test of the real CLI against a mock Kie
- [x] 45. `serbeval triage` + scripts/kie_triage.sh (smoke / full, budget printed, confirm before full)
- [ ] Maintainer: `KIE_API_KEY=... scripts/kie_triage.sh smoke`, then `full`, then review the queue
- [x] 46. Position bias removed: gold letters balanced in all three MCQ sets; build-failing guard test
- [x] 47. First real API run (Kie smoke): both models 18/18 after fixing Bearer auth, 200-wrapped 401s, empty Content-Type, venv path, Cyrillic scoring, and run-killing retries
- [ ] Maintainer: `KIE_API_KEY=... scripts/kie_triage.sh full` (~230 items/model; Opus ~10 min, GPT ~1.5 h)
- [ ] Rotate the Kie key afterwards — it was pasted into the terminal and appears in run logs
