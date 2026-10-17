# HANDOFF

Why every non-obvious choice was made: [DECISIONS.md](DECISIONS.md). Task list: [tasks/todo.md](tasks/todo.md).
Leaderboard: [results/LEADERBOARD.md](results/LEADERBOARD.md). v2 plan: [tasks/v2-plan.md](tasks/v2-plan.md).

## Where we left off

Following Aleksa Gordić's LinkedIn feedback, the board now has 30 models (DeepSeek V4 Pro is the
best open-weights model, Nemotron 3 Ultra 77%), an open-weights-only chart and a reasoning
off/low/high comparison (thinking adds ≤2 points; Nemotron drops to 66% at high). The official set
went v1 → v1.1 → **v1.2 (351 items)**: every orthography gold was checked against the text of
Pravopis 2010 (OCR'd scan, kept local) and cites tačka/page; all runs were re-scored from saved
answers. Published on GitHub main (bd81733) and HF. The v2 pilot (format A, multi-error passages)
passed its bar: frontier 82–91% on error passages vs 97–99% on v1.2.

## In flight

- v2: nothing drafted yet beyond the 30 pilot passages (`data/v2_pilot/`, scorer `serbeval.passage`
  with free sites, runner `scripts/pilot_passage.py`).
- PR EleutherAI/lm-evaluation-harness#4400: waiting on CLA + maintainer; it reads the HF data, now v1.2.

## Blockers

- **CLA** on #4400: maintainer only.
- **OpenRouter key** (2026-10-16) expires 2026-10-17 12:02 CEST; ~$3.2 credit on the account. A v2
  board needs a new key.
- **Maintainer time**: v2 needs ~150 passages verified (~5 h) and half of them written by him.
- Pravopis OCR text lives only in the session scratchpad (`scratchpad/dl/p2010.txt`); a new session
  must re-download it (source noted in research_notes/) or work from the report.

## Next session: start here

1. Draft the first 50 format-A passages per `tasks/v2-plan.md` and the todo inventory; each gold
   cites Pravopis 2010; run the scorer self-check (gold exact, source 0 hits) on all of them.
2. Build the HTML verification sheet for them (reuse `serbeval verify` page).
3. After verification, pilot-size run on 4 models before the full 30-model board.

Working rules:
- Run models in parallel; pin provider/precision for open models; check `unparsed`/empties first.
- Norm decisions need a cited source (Pravopis 2010 tačka/page); never decide spelling from memory.
- Chain gates with `&&` before any commit or push; no Claude attribution.
