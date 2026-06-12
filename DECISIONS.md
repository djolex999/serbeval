# DECISIONS.md — one line per non-obvious choice

- 2026-06-13: Project dir was empty (no spec file); built v0.1 scope from the execution brief — srb_grammar + a second task before srb_cyrillic_agreement ("third task" in brief implies two v0.1 tasks). Chose **srb_idioms** as task #2: tests Serbian-specific lexical knowledge that doesn't transfer from English, pairs well with grammar.
- 2026-06-13: Pinned **lm-eval==0.4.12** (latest stable on PyPI today) as "the pinned harness version".
- 2026-06-13: No ANTHROPIC_API_KEY / `ant` profile / keychain credential on this machine → generate/selfcheck/smoke-run are fully implemented + mock-tested; live invocations left as exact documented commands (HANDOFF.md). Did NOT stop to ask, per autonomy rules.
- 2026-06-13: All tasks use `output_type: generate_until` + regex letter extraction (not `multiple_choice`/loglikelihood) because Anthropic chat APIs expose no logprobs.
- 2026-06-13: Seed items authored in-session via parallel author agents, then adversarially verified by independent verifier agents (gold uniquely correct, distractors plausible-but-wrong, natural Serbian); failures fixed or dropped. All items remain `verified: false` pending the maintainer's human pass.
- 2026-06-13: Seed srb_grammar/srb_idioms items use Latin script (dominant in digital Serbian); script-sensitivity is covered separately by srb_cyrillic_agreement's paired items.
- 2026-06-13: MCQ labels are A/B/C/D (not А/Б/В/Г) even in Cyrillic items — keeps the answer-extraction regex script-independent.
- 2026-06-13: Default model for generation/selfcheck CLIs is claude-opus-4-8 (quality of authored items matters most); smoke run targets claude-haiku-4-5 per the brief. Both configurable via --model.
- 2026-06-13: lm-eval loads datasets via HF `json` loader with relative `data_files` → commands must run from repo root (documented in README).
- 2026-06-13: selfcheck keep-rule: keep a candidate only if all 3 re-answers agree with each other AND with the gold label; rejects go to discarded.jsonl with a reason. Strictest reading of "discard disagreements".
