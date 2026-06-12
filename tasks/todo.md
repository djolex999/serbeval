# serbeval — active task list

Full plan: [docs/superpowers/plans/2026-06-13-serbeval-v0.1.md](../docs/superpowers/plans/2026-06-13-serbeval-v0.1.md)

## v0.1
- [ ] 1. Scaffolding (git, venv, pyproject, README, DECISIONS.md)
- [ ] 2. EvalItem schema (pydantic, TDD)
- [ ] 3. Dataset IO + `serbeval validate` CLI
- [ ] 4. Seed datasets: srb_grammar (~50), srb_idioms (~30) — multi-agent authored + adversarially verified, all `verified: false`
- [ ] 5. lm-eval task YAMLs (generate_until + regex filter)
- [ ] 6. `serbeval generate` candidate generation (mock-tested; live run needs API key)
- [ ] 7. Run docs + results/ layout
- [ ] 8. pytest + mypy + ruff green

## v0.2
- [ ] 9. Self-consistency filter `serbeval selfcheck` (mock-tested)
- [ ] 10. srb_cyrillic_agreement (formal harness task if clean, else post-processing script)
- [ ] 11. Haiku smoke run — BLOCKED: no API key on machine → documented TODO
- [ ] 12. CONTRIBUTING.md + issue templates
- [ ] 13. Final checks + HANDOFF.md
