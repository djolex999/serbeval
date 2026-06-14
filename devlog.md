# devlog

## 2026-06-13 — v0.1 autonomous build start
- Empty repo; scope reconstructed from execution brief (see DECISIONS.md).
- git init, venv, pinned lm-eval==0.4.12 + anthropic + pydantic + dev tools.
- No Anthropic credentials on machine → API-touching features mock-tested only; live runs documented as TODOs.
- Plan: docs/superpowers/plans/2026-06-13-serbeval-v0.1.md; checklist: tasks/todo.md.

## 2026-06-14 — v0.1 + v0.2 complete
- Shipped: schema, dataset IO/validation, generate + selfcheck (Claude-backed, mock-tested), CLI (validate/generate/selfcheck), 3 lm-eval tasks, tested Latin→Cyrillic transliterator.
- Seed data via multi-agent workflow: 50 srb_grammar + 30 srb_idioms (all verified:false), 20 dropped→discarded.jsonl. srb_cyrillic_agreement: 15 factual pairs (30 items).
- First seed workflow run died (fable-5[1m] model stalls + a null bug); hardened script + re-ran on opus-4-8[1m] via resume.
- srb_cyrillic_agreement is a FORMAL harness task (custom pair_agreement metric) — 0.4.12 supports it cleanly.
- Smoke run: validated full pipeline with lm-eval `dummy` model (no API key for live haiku). Both metrics aggregate.
- Gates green: 50 tests, mypy src strict, ruff. CONTRIBUTING + issue templates + HANDOFF.md written.
- Outstanding (maintainer): human-verify items, live model runs, expand thin glagolski-vid (4 items).
