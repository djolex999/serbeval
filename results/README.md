# results/

Eval outputs live here. Raw per-sample model logs (`results/**/raw/`) are gitignored; commit only
the summary JSON that lm-eval writes at the top level of each `--output_path` run.

## Status

**Preliminary leaderboard: [LEADERBOARD.md](LEADERBOARD.md)** — 12 models via OpenRouter
(2026-10-08), rebuilt by `scripts/leaderboard.py`. Items are not yet human-verified, so the
numbers are not citable. Kie runs (`triage-*/`, gitignored) are triage only, never reported.

Run one model: `OPENROUTER_API_KEY=... scripts/openrouter_eval.sh <model> [model_args]`.
Run different models in parallel, one process each. The sections below date from before
any API key and are kept for the dummy-model pipeline check.

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

### 0b. Install the API extras — no API run works without them

*(Installed on the dev machine on 2026-10-07.)*

`lm-eval` needs its `[api]` extra (`tenacity`, `tiktoken`) for every API-backed model,
the stock `anthropic-chat` adapter included. Without it the run dies immediately with
`ModuleNotFoundError`. The `dummy` model never needed these, which is why no dummy-based
check caught it. `pyproject.toml` now declares `lm-eval[api]`; reinstall once:

```bash
.venv/bin/pip install -e ".[dev]"
```

### 0c. Optional, cheap: item triage through Kie (~$1-2, never reported)

Before spending on first-party runs, two strong models from different families can point
at broken items. An item every model misses is usually a broken item, not a hard one.

```bash
KIE_API_KEY=... scripts/kie_triage.sh smoke   # 3 items/task, under $0.10 — first
KIE_API_KEY=... scripts/kie_triage.sh full    # ~230 items, ~$1-2 expected, ~$5-6 worst
```

It runs `claude-opus-5-5` and `gpt-6-1-sol`, prints `unparsed` per task (near 0 means the
plumbing works), then `serbeval triage`: every missed item, unanimous misses first, with
the gold answer next to each model's answer.

Kie serves these models in two different formats, neither of which is lm-eval's
chat-completions default: Claude at `/claude/v1/messages` (Anthropic format; handled by
`anthropic-chat-fixed` with a `base_url`) and GPT at `/codex/v1/responses` (OpenAI
Responses format; handled by the new `kie-responses` adapter). Credentials come only from
`KIE_API_KEY` — a first-party Anthropic or OpenAI key is never sent to the reseller.

**Triage only.** Which model actually served and whether answers were cached cannot be
verified through a reseller. Output goes to `results/triage-kie/`, which is gitignored.

### 1a. Use the fixed adapter for current models

**lm-eval 0.4.12's stock `anthropic-chat` adapter cannot evaluate Claude Opus 5, Sonnet 5,
Opus 4.8 or Opus 4.7 at all.** It sends `temperature` on every request — removed on those
models, so the API answers 400 — and it reads every response block as `block["text"]`,
which raises KeyError on the thinking block those models return. Either way the run dies
before producing a result.

`scripts/run_eval.py` registers a fixed adapter (`anthropic-chat-fixed`) and then hands
over to lm_eval; every lm_eval flag works unchanged:

```bash
scripts/run_eval.py --model anthropic-chat-fixed \
  --model_args model=claude-opus-5 \
  --tasks srb_grammar --include_path lm_eval_tasks \
  --output_path results/opus-5 --log_samples
```

The stock adapter is left registered and untouched, so the two can be compared if a
result ever looks wrong — and a `pip install` cannot silently revert the fix.

Haiku 4.5, Sonnet 4.6 and Opus 4.6 still accept `temperature` and work with plain
`lm_eval --model anthropic-chat`.

**Claude Opus 5.5 cannot turn thinking off** — `thinking: {"type": "disabled"}` is a 400 at
every effort level (the same holds for the Fable/Mythos line). Run it as:

```bash
scripts/run_eval.py --model anthropic-chat-fixed \
  --model_args model=claude-opus-5-5,thinking=omit,effort=low \
  --tasks srb_grammar --include_path lm_eval_tasks \
  --output_path results/opus-5-5 --log_samples
```

Asking for the default `thinking=off` on it stops at startup with that exact command in
the error, instead of 400-ing on every request. With thinking on, `max_tokens` is raised to
at least 2048 automatically — the tasks' 24-32 token caps are sized for a bare answer.

Cost is therefore different in kind: thinking tokens bill as output ($20/M on Opus 5.5).
At `effort=low` on items this short expect roughly 100-500 thinking tokens each, i.e.
**~$3-12 for the full 1102 items** against under $1 for each non-thinking model. The
2048-token floor bounds the worst case at ~$45. Run the `--limit 10` smoke test first and
read the actual output-token usage before committing to the full set.

**Thinking is off by default** in the fixed adapter. These items want one letter or one
word form, and on Opus 5 thinking is on by default — at `max_gen_toks: 32` the model
would spend its budget reasoning and return nothing, scoring `unparsed` across the board.
To measure a model as it behaves in normal use instead, pass
`--model_args model=claude-opus-5,thinking=adaptive,effort=low` with a much larger
`--gen_kwargs max_gen_toks=1024`. Running both settings on the same items is itself
informative, and costs more: thinking tokens are billed as output.

One known consequence, shared with the stock adapter: `"\n\n".strip()` is empty, so the
tasks' `until: ["\n\n"]` is dropped (the API rejects whitespace-only stop sequences) and
generation runs to `max_tokens`. Harmless here — both extractors read only the leading
part of the response.

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
