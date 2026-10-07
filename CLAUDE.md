# serbeval — project context

Serbian-language LLM eval benchmark on lm-evaluation-harness (pinned `0.4.12`).

## Stack
- Python 3.11+ (dev machine runs 3.13), venv at `.venv/`
- `lm-eval[api]==0.4.12` (the `[api]` extra is required for ANY API model), `anthropic`, `pydantic` v2; dev: pytest, mypy (strict), ruff
- No HF Hub pushes, no PyPI publish — local only; publishing is the maintainer's call
- Code is MIT; data is CC BY 4.0 (hand-written) / CC BY-SA 4.0 (mined, synth, forms index) — see data/LICENSE

## Layout
- `src/serbeval/` — schema, IO/validation, lint, balance, mine, synth, check, triage, report, baseline, CLI;
  `lm_eval_anthropic.py` / `lm_eval_kie.py` — model adapters (stock lm-eval ones break on current models)
- `data/<task>/items.jsonl` — curated items; `candidates.jsonl` — generated, unmerged; `discarded.jsonl` — selfcheck rejects
- `data/srb_grammar_cloze/candidates.jsonl` (mined) and `candidates-synth.jsonl` (synth) — kept separate on purpose
- `lm_eval_tasks/` — harness task YAMLs + `utils.py` (`!function` helpers, custom pair-agreement metric)
- `results/` — eval outputs (raw model logs and `triage-*` gitignored)
- `scripts/run_eval.py` — lm_eval with the fixed adapters registered; `scripts/kie_triage.sh` — reseller triage

## Conventions
- MCQ items: 4 choices, A/B/C/D, gold positions balanced (a test fails the build otherwise); `generate_until` + regex
- Cloze items: exact match on the produced form; case/punctuation/script folded, diacritics NEVER folded
- Every item has `verified: bool`; nothing publishable until human-verified
- Run lm_eval from repo root (relative `data_files` in YAMLs)
- In a git worktree, prefix commands with `PYTHONPATH=src` (the editable install points at the main checkout)
- Check `unparsed` before believing any accuracy
- Kie (reseller) runs are triage only — never reported; reportable numbers come from first-party APIs
- Commands: `pytest` · `mypy src` · `ruff check` — all must be green before "done"

## Key files
- DECISIONS.md — one-line log of every non-obvious choice (read this first)
- HANDOFF.md — what's done / stubbed / needs human eyes

<!-- VIR:START -->
<!-- vir-last-updated: 2026-10-06 -->

## Distilled Knowledge (from Vir)

### Patterns
- pattern/autonomous-test-driven-scaffolding-under-uncertainty (conf 0.92) — autonomous-test-driven-scaffolding-under-uncertainty
- pattern/code-complete-gates-green (conf 0.88) — code-complete-gates-green

### Gotchas
- gotcha/position-bias-blocks-serbeval (conf 0.82) — position-bias-blocks-serbeval

### Decisions
- decision/single-device-database-vulnerability (conf 0.92) — single-device-database-vulnerability
- decision/serbeval-anthropic-adapter-fixed (conf 0.80) — serbeval-anthropic-adapter-fixed

<!-- VIR:END -->
