# serbeval — project context

Serbian-language LLM eval benchmark on lm-evaluation-harness (pinned `0.4.12`).

## Stack
- Python 3.11+ (dev machine runs 3.13), venv at `.venv/`
- `lm-eval[api]==0.4.12` (the `[api]` extra is required for ANY API model), `anthropic`, `pydantic` v2; dev: pytest, mypy (strict), ruff
- Public: GitHub djolex999/serbeval, HF dataset djolex999/serbeval (official set only), lm-eval PR #4400. No PyPI. Every push/publish is the maintainer's call
- Code is MIT; data is CC BY 4.0 (hand-written) / CC BY-SA 4.0 (mined, synth, forms index) — see data/LICENSE

## Layout
- `src/serbeval/` — schema, IO/validation, lint, balance, mine, synth, check, triage, report, baseline, CLI;
  probe, correction, verify (+ verify_page), official;
  `lm_eval_anthropic.py` / `lm_eval_kie.py` / `lm_eval_openrouter.py` — model adapters (stock lm-eval ones break on current models)
- `data/official/` — official set v1 (355 items) + MANIFEST.json (per-item status); tasks `*_official`, tag `srb_official`
- `data/<task>/items.jsonl` — curated items; `candidates.jsonl` — generated, unmerged; `discarded.jsonl` — selfcheck rejects
- `data/srb_grammar_cloze/candidates.jsonl` (mined) and `candidates-synth.jsonl` (synth) — kept separate on purpose
- `lm_eval_tasks/` — harness task YAMLs + `utils.py` (`!function` helpers, custom pair-agreement metric)
- `results/` — eval outputs (raw model logs and `triage-*` gitignored)
- `scripts/run_eval.py` — lm_eval with the fixed adapters registered; `scripts/kie_triage.sh` — reseller triage
- `scripts/openrouter_eval.sh` — leaderboard runs; `leaderboard.py --official`, `leaderboard_chart.py` (conda python3, matplotlib), `build_hf_dataset.py`

## Conventions
- MCQ items: 4 choices, A/B/C/D, gold positions balanced (a test fails the build otherwise); `generate_until` + regex
- Cloze items: exact match on the produced form; case/punctuation/script folded, diacritics NEVER folded
- Every item has `verified: bool`; official-set items carry a status in MANIFEST: human / consensus / derived — never present consensus as human-verified
- Run lm_eval from repo root (relative `data_files` in YAMLs)
- In a git worktree, prefix commands with `PYTHONPATH=src` (the editable install points at the main checkout)
- Check `unparsed` before believing any accuracy
- Kie (reseller) runs are triage only — never reported; reportable numbers come from first-party APIs
  or OpenRouter with provider/quantization pinned for open models
- Run independent model evals in parallel processes, never queued
- No Claude attribution (Co-Authored-By etc.) in commits or PRs
- Commands: `pytest` · `mypy src` · `ruff check` — all must be green before "done"
  (chain them with `&&` before any commit/push)

## Key files
- DECISIONS.md — one-line log of every non-obvious choice (read this first)
- HANDOFF.md — what's done / stubbed / needs human eyes
