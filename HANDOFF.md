# HANDOFF

Why every non-obvious choice was made: [DECISIONS.md](DECISIONS.md). Task list: [tasks/todo.md](tasks/todo.md).
Leaderboard: [results/LEADERBOARD.md](results/LEADERBOARD.md).

## Where we left off (2026-10-08)

**serbeval works as a benchmark, though not at the frontier.** A preliminary 12-model
leaderboard through OpenRouter spreads from 36% to 94%: sonnet-5.5 94, gemini-3.5-flash-lite 91,
deepseek-v3.2 87, gemma-4-31b 86 … llama-3.1-8b 39, mistral-nemo 36. Pravopis (13–92%) and the
probe set (14–92%) discriminate best. The cost was $1.21 for everything.

Opus 5.5, by contrast, is at ceiling on every format tried, through Kie triage. Three passes
showed it:
- a 6-phenomenon probe (`srb_probe_*`);
- a source-checked pravopis set (`srb_pravopis_*`, 82 items);
- a cue-free error-correction set (`srb_correction_*`, 90 items).

Its few "errors" fell on contested norm (Pravopis 2010 hyphenates foto-/auto-, Klajn writes
them together) or on item artifacts. Positioning: a benchmark for open, cheap and mid-tier
models, plus a documented ceiling for the frontier.

The goal (maintainer): own use, public adoption, and portfolio.

## In flight

- Nothing running. Per-sample logs of the leaderboard run are gitignored and sit in this
  worktree's `results/openrouter/`; the summary JSON and provider logs are committed.

## Blockers before publishing

- **Human verification.** 30 of ~1400 items are verified. A public leaderboard needs a
  verified "official" set (~200–300 items, weighted to pravopis + probe), then a re-run.
- **Keys to revoke.** The Kie key was pasted in a terminal and used in commands, and the
  OpenRouter key `serbeval` was pasted into chat. Revoke both.
- Empty provider responses slightly underscore qwen3-235b (up to 13% on srb_idioms) and
  gemma-4-31b; re-send those items.

## Next session: start here

1. Build the official set: pick ~250 items (all probe + pravopis + correction, a sample of
   MCQ/cloze), have the maintainer verify them with `serbeval review` or `serbeval baseline`,
   drop or fix whatever fails.
2. Re-run the 12 models on that set, all in PARALLEL, one process per model:
   `scripts/openrouter_eval.sh <model> [args]`, args per model in DECISIONS.md / LEADERBOARD.md.
   Then run `scripts/leaderboard.py`.
3. README with the table, a chart and the methodology. Then publish on GitHub (public) and
   Hugging Face Datasets, and consider a PR to lm-evaluation-harness.

Working rules that bit us:
- Run different models in parallel; only requests inside one run are sequential.
- Check `unparsed` before believing any accuracy.
- Kie numbers are triage only. Leaderboard numbers come from OpenRouter (provider logged,
  precision pinned) or first-party APIs.
- In a worktree, prefix commands with `PYTHONPATH=src`.
