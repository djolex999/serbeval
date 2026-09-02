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
