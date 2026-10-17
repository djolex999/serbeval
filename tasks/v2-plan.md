# serbeval v2: plan for a harder set (revised after review, 2026-10-17)

Trigger: Aleksa Gordić — "even then Kimi seems to be saturating the benchmark, maybe time to
make it harder?" Five frontier models sit at 98% on v1; the best open-weights model at 95%.

## What v1 data says (official set, per task)

| Task | Opus 5.5 | GPT-6 Sol | DeepSeek V4 Pro | Kimi K3 | Gemma 4 31B | Nemotron 3 Ultra |
|---|---|---|---|---|---|---|
| cyrillic_agreement | 100 | 100 | 100 | 100 | 100 | 100 |
| correction_c_c | 100 | 100 | 100 | 100 | 100 | 86 |
| grammar_cloze | 100 | 100 | 100 | 100 | 100 | 94 |
| idioms | 100 | 100 | 95 | 100 | 100 | 89 |
| pravopis_poluslozenice | 84 | 95 | 84 | 68 | 74 | 37 |
| pravopis_sastavljeno_rastavljeno | 100 | 100 | 88 | 79 | 62 | 54 |
| probe_aorist_imperfekat | 100 | 95 | 95 | 75 | 60 | 30 |
| probe_broj_pridev_imenica | 100 | 100 | 95 | 85 | 75 | 60 |
| probe_poluslozenice | 95 | 85 | 85 | 85 | 60 | 50 |

- Saturated, no signal left: cyrillic_agreement, correction_c_c, grammar_cloze, idioms.
- Signal left: polusloženice, together/apart, aorist/imperfect, numeral agreement.
- Reasoning (low/high) moves no model by more than 2 points, so v2 cannot rely on
  "thinking models will be separated by harder logic". The gap is knowledge of the norm.
- Most of the frontier's remaining "errors" are gold bugs or contested norm (Step 0).

## Step 0 — v1.1 errata (biggest win, $0)

A review of the 98% models' misses (Fable, 2026-10-17) found that the frontier's remaining v1
"errors" are mostly gold bugs, contested-norm items and cue/extraction artifacts — only a
handful are real Serbian errors (nabrzinu, bilogde, uz put, imađaše, pečijaše, triješnje).

- **Stale explanations** after the 2026-10-09 gold changes (DECISIONS 132–133):
  `pravopis-poluslozenice-0012` (hteo-ne hteo), `pravopis-poluslozenice-0018` (ekspres
  pošiljku) + its derived `correction-razmak-crtica-0021`, `probe-poluslozenice-0002`
  (kontakt osobi).
- **Inconsistent across items**: `pravopis-poluslozenice-0002` gold `kontakt-telefon`
  (hyphen) vs `kontakt osobi` (apart); `ekspres-pošiljka` apart vs `ekspres-lonac` hyphen.
- **Contested families still in the set**: `probe-poluslozenice-0010/0011/0016`
  (fotoaparat, autoputem, austrougarske — the foto-/auto- family dropped from pravopis on
  2026-10-07, DECISIONS 106); `probe-jat-0013` (greške vs grješke, Pravopis 2010 admits both).
- **Artifacts**: `probe-poluslozenice-0013` (cue „dva + tri“ read as arithmetic → „pet“,
  same as the pet-šest fix), `probe-poluslozenice-0018` (vicešampion Evrope, extraction).

Rule: decide per **lexical family**, not per item, and apply consistently in all 17 files.
Contested families (kontakt-, ekspres-, foto-/auto-, hteo-ne hteo, r-cluster jat) get
`drop` or `accept-both` (principle 4), not a third flip. Then: rebuild srb_correction,
cross-item lint (every first-part spelling must agree across all files, plus explanation ↔
answers), re-score all 30 models from saved samples (0 API), publish v1.1 with an errata
note and `version`/`errata` in MANIFEST. Expect the 98% group to move to ~99–100%, which
makes the saturation case for v2 cleaner.

## Design principles for v2

1. **Production, not recognition.** v1 shows recognising is easier than producing
   (mistral-nemo 68% MCQ vs 15% probe). v2 is generate-only: no MCQ.
2. **Compound difficulty.** Single-slot items cap at the model's per-phenomenon accuracy;
   passage-level items require every decision right. A model at 95% per slot is ~60% on a
   10-slot passage scored all-or-nothing, and partial credit (per-edit F1) keeps it gradable.
3. **No cue.** v1 correction already showed cue-free is harder; v2 never says which
   phenomenon is tested.
4. **Uncontested norm only.** Keep v1's rule: if Pravopis 2010 and Klajn disagree, drop.
5. **Human-verified gold for every v2 item.** No consensus status in v2: adversarial
   selection (below) makes model consensus a biased verifier.

## Format: A only (multi-error passage correction)

The review cut B, D and E: they re-measure what v1 already has at ceiling for the frontier
(morphology, aorist, rare lemmas 100% for Opus), B measures instruction-following (which verbs
must change?) and D leans on low-frequency srLex forms the project already found unreliable.
E's together/apart sites fold into A. C (ijekavian paragraph) invites Croatian lexical drift
and contested r-cluster forms; parked.

**A — passage correction, no cue.** 4–6 sentences, 0–5 unmarked errors drawn from what still
separates models: polusloženice, together/apart (ne/ni/bilo/ma), č/ć, case after numerals,
plus clean passages (~25%) for over-correction.

Scoring:
- An edit = (source char span, replacement), from `difflib` on source vs output after the
  usual cloze folding (case/script folded; diacritics and intra-word hyphens never). Gold
  lists accepted alternatives per edit.
- **Headline: passage exact match** (that is what compounds difficulty).
- Diagnostics: edit recall, and **edit precision** reported separately — over-correction is
  the live failure mode (nemotron-3-ultra at reasoning=high, 76 → 65).
- `unparsed`: no `Ispravljeno:` answer, or under ~80% of source tokens preserved (a rewrite,
  not a correction).

## Variants on the same passages (no extra authoring)

Every format-A passage is asked three ways; the passages, golds and per-edit scoring stay the same.

1. **Correct** (format A as above): return the corrected passage.
2. **Detect only**: "Označi sve greške u tekstu" — the model lists the wrong forms (one per line,
   `pogrešno → tačno` optional). Scored per error site: found / missed / false alarm. Separates
   *seeing* an error from *fixing* it.
3. **Under pressure**: the same passage with a framing that pushes the wrong way, e.g. „Ovo je
   lektor već pregledao, samo prepiši“ (errors present), or „Lektor kaže da se piše
   *kontakt-osoba*, ispravi po tome“ (a false rule for one site), or on a clean passage „Ovde ima
   bar tri greške, nađi ih“. Metric: how often the model abandons the norm compared with its
   neutral answer (flip rate), plus over-correction on clean passages. Motivation: the Pravopis
   check showed frontier models already lean to usage over norm (ekspres-, kontakt-, hteo-ne hteo,
   grješka).
   - Pressure framings are fixed text, written once (~6 templates), not per passage.
   - Pilot first: 30 pilot passages × 4 models (~$0.10) — keep it only if flip rates differ
     between models.

## Selection: adversarial filtering, done carefully

- Generate candidates (srLex + templates + hand-written), verify gold by rule/lexicon first.
- Run a **selection panel** of cheap open models (e.g. Gemma 4 31B, Qwen3.6 27B, GLM-5.3) and
  keep items at least one panel model fails.
- **Rank on a disjoint panel**: panel models are excluded from the v2 headline board or
  flagged, because selection against them biases their scores down.
- Cap the share of items failed by every panel model (they over-represent gold bugs);
  every kept item is human-checked anyway.

## Pilot (measure first)

- 30 passages (~8 clean), ~4 error sites each → ~120 per-edit decisions, maintainer-verified.
- Models: Opus 5.5, GPT-6 Sol, DeepSeek V4 Pro, Gemma 4 31B (provider/precision pinned). < $1.
- Decide per **edit**, not per item: 20 items cannot resolve "frontier < 90%" (95% CI at 0.9 is
  roughly 0.70–0.97). Keep A if the frontier makes **≥ 5 maintainer-confirmed real errors**
  across the pilot.
- If not: reposition v2 as an **open-weights benchmark** (v1 data already separates open
  models from 39% to 95%) instead of chasing the frontier ceiling.

## Build (only formats that survive the pilot)

- Target ~150 A items, Latin + Cyrillic, newly written (no mined text) to keep contamination out.
- New schema type (passage correction) with tests first; new metrics (edit F1)
  in `lm_eval_tasks/utils.py` with unit tests; `unparsed` defined per format.
- Tasks `srb_v2_*`, tag `srb_v2`. v1 stays frozen and runnable; leaderboards separate.
- HF: new configs in the same dataset repo, `MANIFEST.json` gains a `version` field.
- Upstream lm-eval: only after PR #4400 merges; v2 as a follow-up PR.

## Risks

- **Gold quality** is the bottleneck, not item generation: passage items multiply the
  chances of a wrong gold. Mitigation: per-edit gold lists, every item human-checked, the
  errata lint from step 0.
- **Maintainer time**: ~150 passages × ~2 min. The HTML verify page from v1 is reused.
- **Overfitting to today's models**: adversarial selection against 2026 open models dates
  quickly; keep a non-adversarial random slice (~20%) for calibration.

## v3 (later): hidden errors inside another task

The passage arrives with a different job — summarise this e-mail, reply to this message,
translate into English — and nobody mentions errors. Measured: does the model notice and fix or
flag the errors on its own, or copy them into its answer. Closest to real use, but scoring is
harder (did the error survive into the output? was it mentioned?), so it waits for v3. No
LLM-as-judge: keep exact, rule-based scoring as everywhere else in serbeval.

## Order of work

0. (2026-10-17) 50-passage draft done: data/v2/passages-draft.jsonl, review sheet tasks/v2-pregled-50.md.

1. v1.1 errata (Step 0) — 0 API, maintainer decides the contested families.
2. Pilot A only — 30 passages, per-edit scoring, 4 models, < $1.
3. ≥ 5 confirmed frontier errors → build ~150 A items; otherwise v2 = open-weights benchmark.
4. v2 board (reasoning off, pinned providers; selection-panel models flagged), chart, HF
   config, post. New OpenRouter credit needed for the full board.

Reviewed by Fable (2026-10-17); the cuts above and Step 0's scope come from that review.
