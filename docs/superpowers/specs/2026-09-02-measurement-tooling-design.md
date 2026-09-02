# serbeval — measurement tooling + difficulty schema

Date: 2026-09-02 · Status: approved, implementing

## Problem

serbeval has 110 items across three tasks and **no way to tell whether the benchmark
discriminates between models**. Three concrete gaps:

1. **No statistical honesty.** 50 grammar items give a ~±14pp 95% CI on accuracy. Per-category
   (`glagolski-vid`, n=4) there is no usable estimate at all. Nothing in the repo says so, so a
   future results table would imply precision it does not have.
2. **No distractor quality signal.** Several seed items have distractors that stack two errors
   (`o olovkom` = wrong preposition *and* wrong case). Nobody would produce those, so the item
   tests "can the model parse Serbian" rather than "does it know the norm". Some items may be
   effectively 2-way MCQ (chance 50%, not 25%).
3. **`srb_cyrillic_agreement` cannot answer its own question.** Its 15 pairs are uniformly easy
   by design (see DECISIONS 2026-06-14). The interesting finding — *does the script gap widen as
   the base question gets harder?* — is unmeasurable without difficulty metadata.

## Non-goals for this round

Rewriting distractors, expanding the cyrillic set, replacing saturated idioms. Those are dataset
work and should be driven by lint output, not by taste. This round builds the instruments.

## Design

### 1. `difficulty` on `EvalItem`

```python
Difficulty = Literal["easy", "medium", "hard"]
difficulty: Difficulty | None = None
```

Optional with a `None` default, so all 110 existing items validate unchanged (backward
compatible; no data migration in this round).

New pair-integrity rule in `data.py`: **both members of a script pair must share a difficulty.**
Otherwise a gap-by-tier breakdown mixes tiers within a pair and the number means nothing.

For `srb_cyrillic_agreement`, `difficulty` describes the **base fact**, not the script. That is
what makes "script gap by tier" a coherent measurement.

### 2. `serbeval lint <path>` — advisory

Deterministic, no model calls. **Always exits 0.** `serbeval validate` and CI are untouched and
stay green. Separation of concerns: `validate` = is the data well-formed, `lint` = is the data good.

Per distractor, compared against gold:

- normalized Levenshtein distance and token-level diff
- classification: `minimal-pair` (one error dimension — good) / `weak` (two-plus stacked errors) /
  `dead` (unrelated to gold, trivially eliminable)

Item-level flags:

- **`near-miss-count < 2`** — effectively a 2-way MCQ; real chance level is 50%
- **structural gold leak** — gold is the structural odd-one-out (uniquely longest/shortest, or the
  only choice differing on a surface feature), so it is guessable without Serbian

Output: ranked worst-first, with gold and each distractor labelled and a one-line reason.

**Stated limitation:** edit distance cannot judge *semantic* plausibility. A distractor that is a
clean minimal pair but means something absurd will pass. Documented, not faked. An LLM-backed
plausibility pass is deliberately deferred — the repo already carries two implemented-but-never-run
LLM commands, and a third would be speculative until a key exists.

### 3. `serbeval report <results-dir>...`

Parses lm-eval output (`results_*.json`, and `samples_*.jsonl` when `--log_samples` was used),
one directory per model.

- per task, per model: accuracy + **Wilson score interval** (correct for small n and proportions
  near 0/1, unlike the normal approximation)
- cross-model spread
- **explicit verdict when CI overlap means the item count cannot rank the models** — this is the
  headline output, not a footnote
- warns on any task/category with n < 10 ("no usable estimate")
- for `srb_cyrillic_agreement`: joins samples back to items to split accuracy by script, reports
  the script gap and `pair_agreement`, broken out by difficulty tier when tiers are present

### 4. Verification

`report` is built and tested against **real lm-eval output** produced by the built-in `dummy`
model, which needs no API key. Unit tests cover Wilson bounds against known values, the CI-overlap
verdict, and the script-gap join. `lint` is unit-tested on hand-built items with known-good and
known-weak distractors.

`pytest` · `mypy src` · `ruff check` must all stay green.

## Files

| File | Change |
| --- | --- |
| `src/serbeval/schema.py` | add `Difficulty` + `difficulty` field |
| `src/serbeval/data.py` | pair difficulty-consistency rule |
| `src/serbeval/lint.py` | new |
| `src/serbeval/report.py` | new |
| `src/serbeval/cli.py` | `lint` + `report` subcommands |
| `tests/test_lint.py`, `tests/test_report.py` | new |
| `README.md`, `DECISIONS.md` | document both commands + the CI caveat |
