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

## Needs maintainer (see HANDOFF.md)
- [ ] Human-verify seed items → flip `verified: true`
- [ ] Live haiku-4-5 smoke run + full model matrix (needs ANTHROPIC_API_KEY)
- [ ] Expand thin `glagolski-vid` category (only 4 items survived verification)
