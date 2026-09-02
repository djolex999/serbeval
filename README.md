# serbeval

Serbian-language evaluation benchmark for LLMs, built on
[lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness) (pinned to `0.4.12`).

Most multilingual benchmarks barely touch Serbian, and none probe the things models actually get
wrong: case government, clitic placement, verbal aspect, paukal agreement, and Cyrillic/Latin
script consistency. serbeval is a small, hand-verifiable benchmark targeting exactly those.

## Tasks

| Task | Items | What it tests | Status |
| --- | --- | --- | --- |
| `srb_grammar` | `data/srb_grammar/items.jsonl` | Case government, verbal aspect, agreement (incl. paukal), clitic placement, comparison, orthography, standard usage | seed set, `verified: false` |
| `srb_idioms` | `data/srb_idioms/items.jsonl` | Meaning of Serbian idioms (lexical knowledge that doesn't transfer from English) | seed set, `verified: false` |
| `srb_cyrillic_agreement` | `data/srb_cyrillic_agreement/items.jsonl` | Same question asked in Cyrillic and Latin — measures per-pair answer agreement plus accuracy | seed set, `verified: false` |

All items are 4-way multiple choice (A/B/C/D), evaluated as `generate_until` with regex letter
extraction — no logprobs required, so any chat API works.

**⚠️ Verification status:** every item currently carries `verified: false`. Items were authored
and adversarially cross-checked by Claude agents, and candidates can additionally pass the
self-consistency filter (`serbeval selfcheck`), but **no results should be published before a
human verification pass** by a native speaker.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running the eval

Run from the **repo root** (dataset paths in the task YAMLs are root-relative):

```bash
export ANTHROPIC_API_KEY=sk-ant-...

lm_eval \
  --model anthropic-chat \
  --model_args model=claude-haiku-4-5 \
  --tasks srb_grammar,srb_idioms,srb_cyrillic_agreement \
  --include_path lm_eval_tasks \
  --output_path results/ \
  --log_samples
```

See [results/README.md](results/README.md) for the model matrix and exact per-model commands.

## Dataset tooling

```bash
serbeval validate data/srb_grammar/items.jsonl       # schema + integrity checks
serbeval generate --task srb_grammar --category enklitike -n 10   # author candidates via Claude
serbeval selfcheck --task srb_grammar                # 3x self-consistency filter on candidates
serbeval review --task srb_grammar                   # interactive human verification (y/n/s/q)
serbeval stats                                       # verification progress per task/category
serbeval report                                      # markdown table from results/*/results_*.json
```

`generate` writes to `data/<task>/candidates.jsonl`; `selfcheck` keeps only candidates whose three
independent re-answers all agree with the gold label (rejects go to `data/<task>/discarded.jsonl`).
Surviving candidates stay `verified: false` until a human merges them into `items.jsonl`.

## Item quality

```bash
serbeval lint data/srb_grammar/items.jsonl     # advisory distractor report, always exits 0
```

`lint` is advisory and never fails a build — `validate` asks whether the data is well-formed,
`lint` asks whether it is *good*. It classifies each distractor against the gold answer as a
**minimal pair** (one error dimension — a real trap), **weak** (two stacked errors), or **dead**,
and flags items with fewer than two real traps as `two-way-mcq`: on those, chance is 50%, not 25%.

It deliberately cannot judge semantic plausibility. A clean one-token edit that happens to mean
something absurd scores as a minimal pair; catching that needs morphological analysis of Serbian
case government, which is out of scope. Read the ranked output, don't trust the score alone.

## Reading results

```bash
serbeval report                          # scans results/ recursively
serbeval report --results-dir results --out results/SUMMARY.md
```

Prints a markdown metrics table for every run it finds. For runs logged with `--log_samples` it
then adds per-task accuracy with a **Wilson 95% confidence interval**, the cross-model spread,
and — the point of the command — an explicit line when the intervals overlap and the item count
therefore *cannot* rank the models. It also warns on any category with n < 10, and breaks the
cyrillic task down by script and difficulty tier. Without `--log_samples` you get the table and a
note saying why the intervals are missing, rather than numbers implying more precision than exists.

**Read this before quoting any number:** at the current sizes (50 / 30 / 30 items) the 95% CI on a
task accuracy is roughly ±14 points, and every individual `srb_grammar` category is under n=10.
The benchmark can currently detect catastrophic failure; it cannot rank comparable models.

## Item schema

```json
{
  "id": "srb-grammar-enklitike-0001",
  "task": "srb_grammar",
  "category": "enklitike",
  "question": "…",
  "choices": ["…", "…", "…", "…"],
  "answer_index": 2,
  "explanation": "…",
  "script": "latin",
  "difficulty": null,
  "pair_id": null,
  "source": "handwritten-claude",
  "verified": false,
  "license": "CC-BY-4.0"
}
```

## Project log

Design decisions: [DECISIONS.md](DECISIONS.md) · Progress: [devlog.md](devlog.md) ·
Handoff notes: [HANDOFF.md](HANDOFF.md)
