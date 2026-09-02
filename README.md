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
| `srb_grammar_cloze` | `data/srb_grammar_cloze/items.jsonl` | Same grammar competence as `srb_grammar` but **fill-in-the-blank**: the model must produce the form, not pick it | prototype, 20 items, `verified: false` |

MCQ items are 4-way multiple choice (A/B/C/D), evaluated as `generate_until` with regex letter
extraction — no logprobs required, so any chat API works.

`srb_grammar_cloze` is an experiment in a different direction:

```
Dopuni rečenicu pravilnim oblikom reči u zagradi.

Uprkos ____, krenuli smo na put.  (loše vreme)
```
→ `lošem vremenu`

Cloze removes the three weaknesses MCQ has here at once: no 25% chance floor, no distractors to
get wrong, and no structural giveaway for a model to pattern-match. `answers` is a list, so
genuinely contested norms (ijekavian doublets, tolerated variants) list every accepted form
rather than forcing one reading and dropping the item. Scoring folds case and punctuation but
**never Serbian diacritics** — `kuca` is not `kuća`.

**Open question this exists to answer:** is cloze actually harder than the MCQ set? That needs a
live model run; the `dummy` model only proves the pipeline works.

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

## Mining items from an annotated corpus

```bash
serbeval mine --conllu path/to/corpus.conllu          # -> data/<task>/candidates.jsonl
```

Reads any morphologically annotated CoNLL-U corpus and builds cloze items from
**prepositional case government**: a preposition whose annotation fixes its noun's case,
with the noun blanked and its lemma given as the cue.

    Obojica su izbačeni iz ____.  (tim, jednina)   ->  tima

This exists to stop a model authoring the exam it will sit. The sentence is attested text and
the gold form is what a linguist tagged, so a human spot-checks a sample instead of verifying
every gold answer.

Which prepositions qualify is **computed from the corpus, never hardcoded** — a preposition is
used only if it governs one case in ≥95% of its attestations. That excludes `u` and `na`, which
take locative or accusative depending on whether the verb expresses motion; the preposition
alone cannot determine the answer there. It also means the same thresholds work on a different
corpus.

Every cue states grammatical number, singular included: after `zbog`, genitive singular `želje`
and genitive plural `želja` are both grammatical, so a bare lemma would leave two defensible
answers.

**Two honest caveats.** (1) Mining does *not* solve contamination — a published treebank's
sentences are on the public web and likely in training data. Point the miner at recently
published text you tag yourself to get around that; the pipeline is corpus-agnostic by design.
(2) Licensing is inherited: items mined from a CC BY-SA corpus carry `CC-BY-SA-4.0`, not the
`CC-BY-4.0` the hand-written items use.

Shipped: `data/srb_grammar_cloze/candidates.jsonl`, 453 items mined from
[UD_Serbian-SET](https://github.com/UniversalDependencies/UD_Serbian-SET) (CC BY-SA 4.0;
Samardžić, Miletić, Ljubešić). Unverified — candidates, not items.

## Synthesising items (the contamination answer)

```bash
serbeval synth --lexicon srLex_v1.3.gz     # -> data/<task>/candidates-synth.jsonl
```

Mining takes attested sentences, which for any published corpus are already on the web and
plausibly in training data. Synthesis writes the sentence itself, so it demonstrably never
existed before — while the gold form still comes from a lexicon rather than a tagger or a
model, so nothing is guessed.

    frame:    "Otvorio je vrata ____."   (requires instrumental)
    lexicon:  ključ -> ključem

Three things follow. **Verification collapses**: a frame that is grammatical for one lemma
of its class is grammatical for all of them, so you check ~24 frames instead of 519 items.
**Scale is free.** And the exam is no longer written by the kind of system sitting it.

Because the frames are authored, the required case is guaranteed by construction rather than
inferred — which is why, unlike `mine`, this can use `u` and `na`. Those take locative or
accusative depending on whether the verb expresses motion, so mining had to skip them; here
the frame supplies the verb, and that contrast is the deliberate `hard` tier:

    Ostali smo u ____ do večeri.   (šuma)     ->  šumi     [rest, locative]
    Ušli smo u ____ i seli.        (bašta)    ->  baštu    [motion, accusative]

Frames declare a **semantic role**, not a category, and only lemmas of that role are
substituted. A single "things" class produced grammatical nonsense — *Knjiga je ostala na
olovci*, *Otvorio je vrata stolicama* — because what you rest a book ON and what you open a
door WITH are different sets. Hence `OBJECT` / `SURFACE` / `TOOL`.

Get srLex from [CLARIN.SI](https://www.clarin.si/repository/xmlui/handle/11356/1233)
(CC BY-SA 4.0, ~54 MB gzipped). It is not vendored here.

Shipped: `data/srb_grammar_cloze/candidates-synth.jsonl`, 519 items. Kept separate from the
mined candidates on purpose — see below.

### The measurement this enables

The same phenomenon now exists in two forms: **mined** (attested, memorisable) and
**synthetic** (novel, not memorisable). The accuracy gap between them estimates the
contamination effect — which is a finding in its own right, not just hygiene.

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
