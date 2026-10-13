# serbeval

A Serbian-language benchmark for LLMs, built on
[lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness) (pinned to `0.4.12`).

Most multilingual benchmarks test Serbian, if at all, with **translated** English tasks. serbeval
tests what translation cannot carry over: case government, verbal aspect, the aorist and
imperfect, sibilarization, numeral agreement (*dva nova stola*, *dvadeset jedan novi sto*), the
ijekavian jat reflex, pravopis (*kontakt osoba*, *naučnoistraživački*, *ne znajući*), č/ć, and
Cyrillic/Latin consistency.

> **Status: official set v1.** The numbers below come from the 355-item official set. 63 items
> are human-verified and the rest are backed by the agreement of four strong models or derived
> from verified items (see [Verification](#verification)). The larger mined and synthesised
> pools stay unverified and are not scored here.

## Leaderboard — official set v1 (2026-10-12/13)

22 models via OpenRouter, zero-shot, on the **official set**. It has 355 items:
- 63 human-verified;
- 214 confirmed by model consensus;
- 78 correction items derived from those.

Each item's status is in [data/official/MANIFEST.json](data/official/MANIFEST.json).
Open-weights models ran at full precision or at their native release precision, on a pinned
provider (often the model's own lab). The provider and the settings for each model are in
[results/LEADERBOARD.md](results/LEADERBOARD.md). Group score = mean task accuracy.

| # | Model | MCQ | Cloze | Pravopis | Probni | Ispravljanje | Prosek | max unparsed |
|---|---|---|---|---|---|---|---|---|
| 1 | anthropic_claude-opus-5.5 | 100% | 100% | 96% | 97% | 99% | **98%** | 0.00 |
| 2 | google_gemini-3.8-flash | 100% | 100% | 94% | 97% | 98% | **98%** | 0.00 |
| 3 | openai_gpt-5.6-sol | 100% | 100% | 95% | 95% | 98% | **98%** | 0.00 |
| 4 | anthropic_claude-sonnet-5.5 | 97% | 94% | 95% | 92% | 97% | **95%** | 0.00 |
| 5 | x-ai_grok-4.7 | 100% | 89% | 91% | 95% | 98% | **94%** | 0.00 |
| 6 | google_gemini-3.5-flash-lite | 100% | 100% | 91% | 87% | 94% | **94%** | 0.00 |
| 7 | openai_gpt-5.6-luna | 98% | 100% | 80% | 89% | 96% | **93%** | 0.00 |
| 8 | moonshotai_kimi-k3 | 95% | 100% | 85% | 85% | 92% | **91%** | 0.00 |
| 9 | z-ai_glm-5.3 | 97% | 94% | 83% | 85% | 93% | **90%** | 0.05 |
| 10 | deepseek_deepseek-v4.1-flash | 100% | 100% | 79% | 83% | 88% | **90%** | 0.00 |
| 11 | google_gemma-4-31b-it | 97% | 100% | 77% | 78% | 92% | **89%** | 0.00 |
| 12 | deepseek_deepseek-v3.2 | 97% | 89% | 87% | 76% | 86% | **87%** | 0.00 |
| 13 | mistralai_mistral-large-4-0 | 97% | 89% | 70% | 69% | 85% | **82%** | 0.00 |
| 14 | qwen_qwen3-235b-a22b-2507 | 88% | 100% | 71% | 67% | 80% | **81%** | 0.05 |
| 15 | openai_gpt-5-mini | 90% | 89% | 66% | 62% | 87% | **79%** | 0.00 |
| 16 | anthropic_claude-haiku-5.5 | 93% | 89% | 57% | 62% | 88% | **78%** | 0.00 |
| 17 | meta-llama_llama-3.3-70b-instruct | 88% | 94% | 57% | 52% | 75% | **73%** | 0.05 |
| 18 | google_gemma-3-12b-it | 78% | 89% | 49% | 43% | 75% | **67%** | 0.00 |
| 19 | qwen_qwen3.5-9b | 85% | 83% | 45% | 36% | 76% | **65%** | 0.00 |
| 20 | mistralai_mistral-nemo | 68% | 33% | 12% | 15% | 68% | **39%** | 0.00 |
| 21 | meta-llama_llama-3.1-8b-instruct | 47% | 50% | 22% | 20% | 53% | **39%** | 0.00 |
| 22 | cohere_command-a-plus | 73% | 33% | 18% | 28% | 37% | **38%** | 0.15 |

Caveat: the four consensus models (sonnet-5.5, gemini-3.5-flash-lite, gemma-4-31b,
deepseek-v3.2) are also ranked here, so a small selection bias toward them is possible. Items
they got wrong were human-checked, not dropped. The three top models (claude-opus-5.5,
gemini-3.8-flash, gpt-5.6-sol) were not among the four.

Details: [results/LEADERBOARD.md](results/LEADERBOARD.md), which also keeps the preliminary
1394-item run.

### What it shows

- **It separates models below the frontier**, from 38% to 98%, roughly in order of size and
  generation. The pravopis and probe groups spread the widest (12–95%).
- **It barely separates the frontier.** claude-opus-5.5, gemini-3.8-flash and gpt-5.6-sol all
  score 98%. Harder versions of the same checks did not change that: a 6-phenomenon probe, a
  source-checked pravopis set, and a cue-free correction format all left Opus at ceiling.
- **The frontier's remaining "errors" are contested norm, not ignorance.** Pravopis 2010
  hyphenates *foto-aparat* and *auto-put*, while Klajn and the 1993 Pravopis write them together.
  Items like that were dropped rather than pinned to one authority.
- **Recognising is easier than producing.** mistral-nemo scores 68% picking the right form from
  four choices but 33% writing it (cloze).
- **Cheap does not mean bad at Serbian.** gemini-3.5-flash-lite (94%) and gpt-5.6-luna (93%)
  beat claude-haiku-5.5 and gpt-5-mini by about 15 points, mostly on pravopis.

## Tasks

| Task | Items | What it tests |
| --- | --- | --- |
| `srb_grammar` | 50 MCQ | case government, aspect, agreement, clitics, comparison, standard usage |
| `srb_idioms` | 30 MCQ | meaning of Serbian idioms |
| `srb_cyrillic_agreement` | 15 pairs | the same question in Cyrillic and Latin; reports per-pair agreement |
| `srb_grammar_cloze` | 20 + 453 mined + 519 synthesised | produce the inflected form (fill-in-the-blank) |
| `srb_probe_*` | 6 × ~20 | jat, aorist/imperfect, sibilarization, numeral agreement, together/apart, polusloženice |
| `srb_pravopis_*` | 4 tasks, 82 | prefixoids, polusloženice, compound adjectives, together/apart |
| `srb_correction_*` | 3 × 30 | **no cue**: correct the one error in a sentence, or leave it alone if it has none |

MCQ items are A/B/C/D, scored as `generate_until` with letter extraction, so no logprobs are
needed and any chat API works. Gold positions are balanced: a test fails the build if they drift,
since an always-"A" model once scored 60–80%.

Cloze items give a cue in brackets and need the exact form:

```
Dopuni rečenicu pravilnim oblikom reči u zagradi.

Uprkos ____, krenuli smo na put.  (loše vreme)
```
→ `lošem vremenu`

Scoring folds case, outer punctuation and script, but **never Serbian diacritics** (`kuca` is
not `kuća`) or an intra-word hyphen (`kontakt-osoba` is not `kontakt osoba`). `answers` is a list,
so tolerated variants are all accepted. A model that repeats the whole sentence verbatim is still
scored on the form it put in the blank.

The correction tasks have no cue. The model sees `Ja to nikada nebih uradio.` or a correct
sentence, and must answer with the corrected sentence or the same sentence unchanged. Errors are
derived mechanically from verified items: spacing and hyphenation, and a č/ć swap that is only
used when it produces a non-word (checked against srLex). The `ispravno` task, made of clean
sentences, measures false alarms.

Every task reports **`unparsed`** next to accuracy. That keeps a refusal or a format slip from
looking like a Serbian error. Check it before believing any number.

## Verification

Gold answers come from three places: hand-written items, the srLex lexicon (only forms
**attested** in the corpus; srLex's generated forms include errors like *mačci* for *mački*), and
UD_Serbian-SET annotations. On top of that:

- **Blind human baseline:** a native speaker answered 30 items without seeing the gold and
  scored 29/30. The miss had the right gold.
- **Source check:** an independent pass checked the pravopis golds against Pravopis 2010, Klajn
  and Serbian language-advice sources. Items where the authorities disagree were dropped.
- **Disputed items, human-checked:** on a 250-item core set, the four strongest models agreed with
  the gold on 214 items. The maintainer checked the 36 where two or more disagreed: 4 golds
  changed, 3 gained an accepted variant, 2 items were dropped. Every gold error found so far sat
  where strong models disagreed.
- **Model consensus is not human verification.** The 214 consensus items are labelled that
  way. Four models can share a mistake, and the blind baseline is the independent control.

Tooling: `serbeval verify --new --html sheet.html` builds an offline page that shows the gold and
takes a keyboard mark per item. `--disputed results/openrouter` restricts it to contested items.
`serbeval verify --apply sheet.txt` writes the marks back to the data.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Run everything from the **repo root**, because the task YAMLs use root-relative paths.

## Running the eval

**Any model through OpenRouter** (what the leaderboard uses):

```bash
export OPENROUTER_API_KEY=...
scripts/openrouter_eval.sh google/gemma-3-12b-it quantizations=bf16
scripts/openrouter_eval.sh anthropic/claude-sonnet-5.5 reasoning=minimal
scripts/leaderboard.py                     # rebuild the table from results/openrouter/
```

The `openrouter-chat` adapter has these defaults:
- reasoning is off (`reasoning=none`); models that cannot disable it take `reasoning=minimal`;
- `provider=` and `quantizations=` pin the routing, with no fallback;
- it reads only `OPENROUTER_API_KEY`.

Run different models **in parallel**, one process each. Requests inside one run stay sequential.

**Anthropic directly:** lm-eval's stock adapter cannot run current Claude models, so use the
fixed one:

```bash
scripts/run_eval.py --model anthropic-chat-fixed --model_args model=claude-opus-5-5,thinking=omit,effort=low \
  --tasks srb_grammar,srb_probe,srb_pravopis,srb_correction --include_path lm_eval_tasks \
  --output_path results/opus --log_samples
```

**Local models through Ollama:** `scripts/local_eval.sh qwen3:8b`. These run free on your
machine, but the weights are quantized.

## Dataset tooling

```bash
serbeval validate data/srb_grammar/items.jsonl       # schema + integrity checks
serbeval generate --task srb_grammar --category enklitike -n 10   # author candidates via Claude
serbeval selfcheck --task srb_grammar                # 3x self-consistency filter on candidates
serbeval review --task srb_grammar                   # interactive human verification (y/n/s/q)
serbeval stats                                       # verification progress per task/category
serbeval report                                      # markdown table from results/*/results_*.json
serbeval verify --new --html sheet.html              # gold-verification page (see Verification)
serbeval probe --lexicon srLex_v1.3.gz               # synthesise the srLex half of the probe set
serbeval correction                                  # derive srb_correction from verified items
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

## Checking generated Serbian (`serbeval check`)

Separate tool, same lexicon. The benchmark asks *how good is this model at Serbian*; this
asks *what is wrong with this text*, which has no gold answer to compare against. Use it as
a quality gate on any Serbian your product generates.

```bash
serbeval check output.txt                  # uses data/forms.txt.gz
cat output.txt | serbeval check --ignore unknown-form
```

```
priprema.txt:3:17: missing-diacritics: „ucenici“ nije oblik u rečniku; verovatno „učenici“
priprema.txt:3:59: missing-diacritics: „ce“ nije oblik u rečniku; verovatno „će“
priprema.txt:4:9:  unknown-form: „dogadjaje“ nije poznat oblik — tipfeler ili izmišljena fleksija
priprema.txt: mixed-script-document: tekst meša pisma: 55 latiničnih i 1 ćiriličnih reči
priprema.txt: dialect-mixing: tekst meša ekavicu i ijekavicu: posledice, svetski, ume vs mjera
```

Four checks, all pure lexicon lookups — no model, no parser, no API key:

| kind | catches |
| --- | --- |
| `mixed-script-word` | a Cyrillic letter inside a Latin word — invisible to the reader, broken in the data |
| `mixed-script-document` | the whole text drifting between scripts |
| `missing-diacritics` | `ucenici` → `učenici`, `ce` → `će`; the most common way generated Serbian goes wrong |
| `unknown-form` | a form absent from the lexicon: a typo or an invented inflection |
| `dialect-mixing` | ekavian and ijekavian in one document (`mera` alongside `mjera`) |

**Measured noise**, on 8329 words of attested Serbian news:

| mode | false positives |
| --- | --- |
| all checks | 0.73% of words |
| `--ignore unknown-form` | **0.012%** — one word in 8329 |

Nearly all the noise is `unknown-form`, and it is srLex coverage rather than a logic
error — the lexicon genuinely lacks ordinary words like *omladine*, *hapšenja*, *biznisa*.
Treat that check as advisory and suppress it when you want a clean signal; the other three
are effectively silent on correct text.

It does **not** judge meaning. If the text states a wrong date, a lexicon has no opinion —
that needs a judge model and is a separate problem.

`data/forms.txt.gz` (1.45M forms) is built from srLex and committed, so this works out of
the box. Rebuild with `serbeval index --lexicon srLex_v1.3.gz`.

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

**Read this before quoting any number.** Small tasks have wide intervals: at 20–30 items the
95% CI on one task is roughly ±15 points. The leaderboard averages groups of tasks, so the
order of models far apart is solid, but neighbours a few points apart are not.

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

## License

The **code** is MIT ([LICENSE](LICENSE)). The **data is not**, and it is not uniform.
Hand-written items are CC BY 4.0. Everything derived from UD_Serbian-SET or srLex is
CC BY-SA 4.0, which is share-alike, so it cannot be relicensed. Each item carries its own
`license` field; the split and the required attributions are in [data/LICENSE](data/LICENSE).

## Author and citation

Djordje Markovic ([@djolex999](https://github.com/djolex999)). The official set is also on
Hugging Face: [djolex999/serbeval](https://huggingface.co/datasets/djolex999/serbeval).

```bibtex
@misc{serbeval2026,
  title  = {serbeval: a Serbian-language benchmark for large language models},
  author = {Markovic, Djordje},
  note   = {GitHub: @djolex999},
  year   = {2026},
  url    = {https://github.com/djolex999/serbeval}
}
```

## Project log

Design decisions: [DECISIONS.md](DECISIONS.md) · Progress: [devlog.md](devlog.md) ·
Handoff notes: [HANDOFF.md](HANDOFF.md)
