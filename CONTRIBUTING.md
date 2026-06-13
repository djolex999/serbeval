# Contributing to serbeval

serbeval is a small, human-verifiable Serbian LLM benchmark. The bar for an item is high: every
item must have exactly one defensibly-correct answer under standard Serbian norms. We would rather
have 40 airtight items than 400 dubious ones.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Before any commit: `pytest` · `mypy src` · `ruff check` must all be green.

## The item schema

See [README.md](README.md#item-schema). Every item is a 4-way MCQ with A/B/C/D labels. Key fields:

- `answer_index` (0–3) — index of the single correct choice
- `script` — `"latin"` or `"cyrillic"`; the text must actually be in that script (A/B/C/D labels
  stay Latin in both)
- `pair_id` — only for `srb_cyrillic_agreement`; the same question in both scripts shares one id
- `verified` — **`false` until a native speaker has signed off.** Never flip to `true` in the same
  PR that adds the item.

## Authoring rules

1. **Standard Serbian, ekavian, by the book.** Norms follow *Pravopis srpskoga jezika* (Matica
   srpska) and standard normative grammar. Avoid contested points where normativists disagree.
2. **Exactly one correct answer.** If a second option is even arguably acceptable (including
   ijekavian doublets or norm-tolerated colloquial variants), the item is broken.
3. **Distractors must be real mistakes** native speakers actually make — plausible but unambiguously
   wrong. No throwaway nonsense options.
4. **Self-contained questions.** No external context required. Vary the framing (correct-sentence
   choice, fill-the-blank `____`, "in which sentence is X correct").
5. **`explanation`** — 1–2 sentences in Serbian saying *why* the gold answer is correct.
6. **No script as the trick** outside `srb_cyrillic_agreement`. Don't offer a correct ijekavian form
   as a "wrong" answer.

## Workflow for new items

### Hand-authored

1. Add JSON lines to `data/<task>/items.jsonl` with `verified: false`,
   `source: "handwritten-<you>"`.
2. `serbeval validate data/<task>/items.jsonl` — must pass.
3. Open a PR using the **New item** template. A native-speaker reviewer flips `verified: true` on
   approval.

### Model-assisted

1. `serbeval generate --task <task> --category <cat> -n <N>` writes to
   `data/<task>/candidates.jsonl` (never directly to `items.jsonl`).
2. `serbeval selfcheck --task <task>` re-answers each candidate 3× and keeps only those whose runs
   unanimously agree with the gold label; rejects go to `discarded.jsonl`.
3. A human reviews survivors, moves good ones into `items.jsonl` (still `verified: false`), and the
   PR review does the final verification.

**Self-consistency is a pre-filter, not verification.** A model agreeing with itself three times
does not make an answer correct.

## Reporting bad items

Found an item with a wrong gold answer, an ambiguous question, or a defensible second answer? Open
an issue with the **Bad item** template — include the item `id` and the norm reference.

## PR checklist

- [ ] `pytest`, `mypy src`, `ruff check` all green
- [ ] `serbeval validate` passes on every changed dataset file
- [ ] New items are `verified: false`
- [ ] `source` set correctly
- [ ] Any non-obvious choice logged in `DECISIONS.md`
