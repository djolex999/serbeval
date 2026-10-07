# HANDOFF

Why every non-obvious choice was made: [DECISIONS.md](DECISIONS.md). Task list: [tasks/todo.md](tasks/todo.md).

## Where we left off

**2026-10-07 probe result:** a 120-item difficulty probe (6 phenomena, cloze, `srb_probe_*`)
did NOT break the ceiling. Opus 5.5 on Kie: aorist/imperfect, numeral agreement, jat and
sibilarization all 100%; sastavljeno-rastavljeno 95% (the one miss, „doviđenja“, is contested);
polusloženice 90%. GPT leg stopped at 7/120 (Kie 500s, low credits). Pravopis is the only place
with any give — see tasks/todo.md for the decision that is now open. Results:
`results/triage-kie-probe/` in this worktree (gitignored).

Earlier context:

serbeval works end-to-end against real models for the first time, and it is **correct but too
easy**. On a Kie triage run (230 items per model) Opus 5.5 scored 230/230 and GPT 6.1 Sol 98% of
the items it answered; the maintainer's blind human baseline scored 29/30 (the one miss,
kontakt-osoba, had the right gold). So the items are sound and the pipeline runs — but the
benchmark cannot separate frontier models. Next is making it harder, measured before built.

## In flight

- Nothing running. The full Kie triage results are in `results/triage-kie/` **inside the
  worktree** `.claude/worktrees/serbeval-app-f49544/` (gitignored, not in the main checkout).
  `serbeval triage --results-dir <that path>` reproduces the review queue.
- `main` has an uncommitted change to `CLAUDE.md` (a Vir "Distilled Knowledge" block) that is
  the maintainer's, not part of this work.

## Blockers

- **Kie key must be rotated** — it was pasted into a terminal and printed in lm-eval's logs.
- **No git remote** — every commit exists only on this machine.
- First-party (reportable) numbers need an `ANTHROPIC_API_KEY`.

## Next session: start here

The difficulty probe set in [tasks/todo.md](tasks/todo.md): 6 candidate-hard phenomena × 20
items, run through both models on Kie (under $1), keep only phenomena where models drop below
~90%. Start by checking whether srLex carries aorist/imperfect forms — that decides how much
can be synthesised rather than hand-written.

Working rules that bit us this time:
- In a worktree, prefix every command with `PYTHONPATH=src` (the venv's editable install points
  at the main checkout).
- Kie: Bearer auth, one request at a time, triage only — never report its numbers.
- Check `unparsed` before believing any accuracy.
