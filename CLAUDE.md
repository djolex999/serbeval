# serbeval — project context

Serbian-language LLM eval benchmark on lm-evaluation-harness (pinned `0.4.12`).

## Stack
- Python 3.11+ (dev machine runs 3.13), venv at `.venv/`
- `lm-eval==0.4.12`, `anthropic`, `pydantic` v2; dev: pytest, mypy (strict), ruff
- No HF Hub pushes, no PyPI publish — local only; publishing is the maintainer's call

## Layout
- `src/serbeval/` — schema, dataset IO/validation, Claude tooling (generate, selfcheck), CLI
- `data/<task>/items.jsonl` — curated items; `candidates.jsonl` — generated, unmerged; `discarded.jsonl` — selfcheck rejects
- `lm_eval_tasks/` — harness task YAMLs + `utils.py` (`!function` helpers, custom pair-agreement metric)
- `results/` — eval outputs (raw model logs gitignored)

## Conventions
- All eval items: 4 choices, A/B/C/D labels, `generate_until` + regex extraction (no logprobs)
- Every item has `verified: bool`; nothing publishable until human-verified
- Run lm_eval from repo root (relative `data_files` in YAMLs)
- Commands: `pytest` · `mypy src` · `ruff check` — all must be green before "done"

## Key files
- DECISIONS.md — one-line log of every non-obvious choice (read this first)
- HANDOFF.md — what's done / stubbed / needs human eyes
