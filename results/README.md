# results/

Eval outputs live here. Raw per-sample model logs (`results/**/raw/`) are gitignored; commit only
the summary JSON that lm-eval writes at the top level of each `--output_path` run.

## Status

⚠️ **No real numbers yet.** The benchmark items are all `verified: false` (awaiting a human pass),
and this dev machine has no `ANTHROPIC_API_KEY`, so no eval has been run. The commands below are the
exact ones to run once a key is available and the seed items are verified.

All commands run from the **repo root** (the task YAMLs use root-relative `data_files`):

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

## Pipeline validation (no API key needed)

The end-to-end harness wiring has been validated against lm-eval 0.4.12 with the built-in dummy
model — this confirms all three task configs load, prompts build, the regex filters run, and both
metrics aggregate (including the custom `pair_agreement`). It does **not** produce meaningful scores
(the dummy model answers `"lol"` to everything):

```bash
lm_eval --model dummy \
  --tasks srb_grammar,srb_idioms,srb_cyrillic_agreement \
  --include_path lm_eval_tasks --output_path results/_smoke_dummy
```

Observed (expected) output: `exact_match = 0` on every task, and `pair_agreement = 1.0` on
`srb_cyrillic_agreement` — both scripts are wrong identically, which is perfect agreement. Delete
`results/_smoke_dummy/` afterward; it holds no real numbers.

## Smoke run (cheap — do this first)

Validates that the whole pipeline produces real numbers, using the cheapest model:

```bash
lm_eval \
  --model anthropic-chat \
  --model_args model=claude-haiku-4-5 \
  --tasks srb_grammar,srb_idioms,srb_cyrillic_agreement \
  --include_path lm_eval_tasks \
  --output_path results/haiku-4-5 \
  --log_samples \
  --apply_chat_template
```

Expected artifacts (note: lm-eval appends a `<model_name_sanitized>` directory below
`--output_path`):
- `results/haiku-4-5/claude-haiku-4-5/results_*.json` — aggregate scores (`exact_match` per task;
  `pair_agreement` additionally for `srb_cyrillic_agreement`)
- sample logs next to it (gitignored)

Then summarize everything committed under `results/` with:

```bash
serbeval report            # markdown table to stdout; add --out results/SUMMARY.md to write a file
```

## Full model matrix (TODO — run after smoke run is green)

Same invocation, swapping `--model_args model=` and `--output_path`. The harness adapter is
`anthropic-chat` for all Claude models on lm-eval 0.4.12.

| Model | `model=` arg | `--output_path` | Status |
| --- | --- | --- | --- |
| Claude Haiku 4.5 | `claude-haiku-4-5` | `results/haiku-4-5` | TODO (smoke target) |
| Claude Sonnet 4.6 | `claude-sonnet-4-6` | `results/sonnet-4-6` | TODO |
| Claude Opus 4.8 | `claude-opus-4-8` | `results/opus-4-8` | TODO |

```bash
# Example (Sonnet):
lm_eval --model anthropic-chat --model_args model=claude-sonnet-4-6 \
  --tasks srb_grammar,srb_idioms,srb_cyrillic_agreement \
  --include_path lm_eval_tasks --output_path results/sonnet-4-6 \
  --log_samples --apply_chat_template
```

Non-Anthropic models can reuse the same tasks via lm-eval's `openai-chat-completions` or
`local-chat-completions` adapters — the task configs are model-agnostic.

---

## The validation run

One run answers five questions. Do the three prep steps first; they cost nothing and
without them the numbers are ambiguous.

### 0. Human baseline — the control that makes everything else readable

```bash
serbeval baseline --new -n 30 --out baseline.txt   # fill in the ODGOVOR: lines
serbeval baseline --score baseline.txt
```

A low model score has two explanations — the model is weak, or the items are broken — and
the numbers cannot separate them. A native speaker can. **If a native speaker does not
score near 100%, stop: fix the items before comparing any models.** Twenty minutes, and
every item the human misses is a verification target, not a human error.

### 1. Pick models with a known spread

Not three similar models. A floor, a ceiling, and one outside the family:

```bash
for m in claude-haiku-4-5 claude-opus-5; do
  lm_eval --model anthropic-chat --model_args model=$m \
    --tasks srb_grammar,srb_idioms,srb_cyrillic_agreement,srb_grammar_cloze,srb_grammar_cloze_mined,srb_grammar_cloze_synth \
    --include_path lm_eval_tasks --output_path results/$m --log_samples
done
```

The non-Anthropic model is not a formality: a benchmark that only ranks one family is
suspect, and the Cyrillic effect plausibly depends on the tokenizer, so an outside model
is what turns that result from interesting into defensible.

`--log_samples` is required — without it `report` cannot compute intervals or breakdowns.

### 2. Read it

```bash
serbeval report --results-dir results
```

| question | where to look |
| --- | --- |
| Does it discriminate at all? | spread vs CI — `report` states outright when it cannot rank |
| Is cloze harder than MCQ? | `srb_grammar` vs `srb_grammar_cloze` |
| How large is contamination? | `srb_grammar_cloze_mined` vs `..._synth`, same phenomenon |
| Script consistency | `pair_agreement` |
| **Are prompts even being read?** | `unparsed` — see below |

**Check `unparsed` before believing any accuracy.** A response we cannot read scores 0,
exactly like a wrong answer. At 5% that is noise; at 20% the accuracy numbers are
measuring your prompt, not the model's Serbian.

### 3. Let the models find your broken items

An item that **every** model fails is disproportionately a *broken item*, not a hard one —
and an item where the weaker model beats the stronger one is almost always wrong gold.
That turns the run into a verification accelerator: instead of checking 1102 items blind,
check the ~50 everyone missed.

### What each outcome means

- **spread inside the CI** → it does not discriminate. Do not add items; change difficulty.
- **cloze far below MCQ** → convert grammar to cloze and retire the whole distractor problem.
- **mined far above synth** → contamination confirmed; lean on the synthetic set.
- **pair_agreement below ~0.9** → that is the publishable finding.

Cost: ~1100 items x ~110 tokens is a few dollars across three models. Cheap enough that
there is no reason to defer it.
