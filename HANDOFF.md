# HANDOFF

State of serbeval after the autonomous v0.1 + v0.2 build. Read [DECISIONS.md](DECISIONS.md) for the
one-line rationale behind every non-obvious choice.

## ⚠️ NEEDS YOUR EYES FIRST — seed item verification

**Nothing here is publishable until a native speaker verifies the items.** Every item carries
`verified: false`. They were authored by Claude agents and adversarially cross-checked by other
Claude agents (and the cyrillic set was transliterated deterministically), but a model verifying a
model is not human verification.

**v0.3 makes this a guided flow — run:**

```bash
./.venv/bin/serbeval review --task srb_cyrillic_agreement
```

(then `srb_idioms`, then `srb_grammar`). For each item you press `y` (correct → `verified: true`),
`n` (reject → moved to `discarded.jsonl` with your reason), `s` (skip), `q` (quit). Every decision
is saved immediately, so you can stop anytime. Cyrillic pairs are shown and decided together.
Track progress with `./.venv/bin/serbeval stats`.

The raw files, if you prefer editing by hand:

| File | Items | How made |
| --- | --- | --- |
| `data/srb_grammar/items.jsonl` | 50 | multi-agent authored + 2-lens adversarial verify |
| `data/srb_idioms/items.jsonl` | 30 | same |
| `data/srb_cyrillic_agreement/items.jsonl` | 30 (15 pairs) | hand-authored base + tested transliterator |

Suggested review order — quickest wins first:
1. **`srb_cyrillic_agreement`** (15 base facts). Easiest: just confirm each fact and that the
   Cyrillic reads naturally. These are deliberately easy/factual (see DECISIONS — the task measures
   script consistency, not difficulty).
2. **`srb_idioms`** (30). Confirm each idiom's gold meaning and that no distractor is also defensible.
3. **`srb_grammar`** (50). The hardest review — these are normative judgments. Watch for items where
   a second answer is arguably acceptable (ijekavian doublets, norm-tolerated variants).

The agents already *dropped* 20 items they couldn't make airtight — see
`data/srb_grammar/discarded.jsonl` and `data/srb_idioms/discarded.jsonl` (each row has the reasons).
Those rejection reasons are a good guide to the failure modes to watch for in the kept items.

## ✅ Done and verified green

- `pytest` (50 tests, incl. a `slow` lm-eval integration test), `mypy src` (strict), `ruff check .`
  — all green. Run all three before calling anything done.
- **Schema + validation** (`src/serbeval/`): `EvalItem` (pydantic v2), JSONL IO, integrity checks
  (unique ids/questions, script consistency, pair integrity). CLI: `serbeval validate <file>`.
- **Three lm-eval tasks** (`lm_eval_tasks/`), all `generate_until` + regex letter extraction:
  `srb_grammar`, `srb_idioms`, and `srb_cyrillic_agreement` (formal harness task with a custom
  `pair_agreement` metric — the harness supports it cleanly, so no post-processing fallback needed).
- **Pipeline validated end-to-end** against lm-eval 0.4.12 via the `dummy` model: both metrics
  aggregate, results JSON is written. See [results/README.md](results/README.md).
- **Transliterator** (`src/serbeval/translit.py`): tested, digraph-aware Latin→Cyrillic.
- **v0.3 verification tooling**: `serbeval review` (interactive human verification, pair-atomic,
  crash-safe), `serbeval stats` (progress per task/category), `serbeval report` (markdown table
  from lm-eval `results_*.json` — ready for the first live runs).

## 🟡 Stubbed / blocked on you

- **No live eval numbers.** This machine has no `ANTHROPIC_API_KEY`, so the brief's
  claude-haiku-4-5 smoke run is documented, not executed. Exact command + the full model matrix are
  in [results/README.md](results/README.md). The pipeline itself is proven (dummy run).
- **`serbeval generate` / `serbeval selfcheck`** are implemented and unit-tested with a mocked
  Anthropic client, but have never made a real API call. First live use: set the key and try
  `serbeval generate --task srb_grammar --category enklitike -n 5` then
  `serbeval selfcheck --task srb_grammar`. The brief's self-consistency pre-filter (re-answer 3×,
  discard disagreements, keep `verified: false`) is exactly `selfcheck`.

## Hard rules I kept (yours)

No HF Hub push, no PyPI publish, no upstream PRs. Everything is local; publishing is your call.

## Suggested next steps

1. Verify the seed items: `serbeval review --task <task>` (above).
2. Add `ANTHROPIC_API_KEY`, run the haiku smoke run, commit the summary JSON to `results/haiku-4-5/`.
3. Expand thin grammar categories — `glagolski-vid` ended up at only 4 items (the verifiers were
   strict on aspect): `serbeval generate --task srb_grammar --category glagolski-vid -n 8`, then
   `selfcheck`, then human-verify.
4. Run the full model matrix in [results/README.md](results/README.md).

## Repo map

```
src/serbeval/      schema.py · data.py · generate.py · selfcheck.py · translit.py · cli.py
lm_eval_tasks/     srb_grammar.yaml · srb_idioms.yaml · srb_cyrillic_agreement.yaml · utils.py
data/<task>/       items.jsonl (curated) · candidates.jsonl (generated) · discarded.jsonl (rejects)
scripts/           seed_workflow.js · ingest_seed.py · build_cyrillic_pairs.py (one-shot builders)
tests/             50 tests; the lm-eval integration test is marked `slow`
results/           README = run commands + model matrix (no real numbers yet)
docs/superpowers/plans/   the implementation plan this build followed
```
