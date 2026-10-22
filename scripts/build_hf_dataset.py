#!/usr/bin/env python
"""Assemble the Hugging Face dataset folder for the official set (build/hf_dataset/).

Only the official set is published there; every item carries a verification status in
MANIFEST.json. The unverified mined/synthesised pools stay on GitHub. One config per task,
because the three item shapes (MCQ, cloze, correction) have different columns.

    scripts/build_hf_dataset.py
    hf upload <user>/serbeval build/hf_dataset . --repo-type dataset
"""

import json
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OFFICIAL = ROOT / "data" / "official"
OUT = ROOT / "build" / "hf_dataset"

DESCRIPTIONS = {
    "srb_grammar": "MCQ: case government, aspect, agreement, clitics, standard usage",
    "srb_idioms": "MCQ: meaning of Serbian idioms",
    "srb_cyrillic_agreement": "MCQ: the same question in Cyrillic and Latin (pairs)",
    "srb_grammar_cloze": "cloze: produce the inflected form",
    "srb_probe_jat": "cloze: ijekavian jat reflex",
    "srb_probe_aorist_imperfekat": "cloze: aorist and imperfect",
    "srb_probe_sibilarizacija": "cloze: sibilarization / palatalization",
    "srb_probe_broj_pridev_imenica": "cloze: numeral + adjective + noun agreement",
    "srb_probe_sastavljeno_rastavljeno": "cloze: written together or apart",
    "srb_probe_poluslozenice": "cloze: hyphenated compounds",
    "srb_pravopis_prefiksoidi": "cloze: foreign prefixoids",
    "srb_pravopis_poluslozenice": "cloze: polusloženice",
    "srb_pravopis_slozeni_pridevi": "cloze: compound adjectives",
    "srb_pravopis_sastavljeno_rastavljeno": "cloze: together / apart",
    "srb_correction_razmak_crtica": "correction: one spacing/hyphen error, no cue",
    "srb_correction_c_c": "correction: one č/ć error, no cue",
    "srb_correction_ispravno": "correction: clean sentences (false-alarm check)",
}


def leaderboard_top() -> str:
    table = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "leaderboard.py"),
         str(ROOT / "results" / "official"), "--official"],
        capture_output=True, text=True, check=True,
    ).stdout.strip().splitlines()
    return "\n".join(table)


V2 = ROOT / "data" / "v2"
V2_CONFIG = "srb_v2_passages"


def build_v2(out: Path) -> tuple[int, int, int, str, int]:
    """Write the verified v2 evaluation set; return (passages, required sites, clean, table)."""
    sys.path.insert(0, str(ROOT / "src"))
    from serbeval.passage import parse_markup

    keep = set(json.loads((V2 / "evaluation.json").read_text(encoding="utf-8"))["included_ids"])
    rows, sites_total, clean = [], 0, 0
    for path in sorted(V2.glob("passages-*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if r["id"] not in keep:
                continue
            assert r["verified"], r["id"]
            p = parse_markup(r["markup"])
            sites = [{"wrong": s.wrong, "right": list(s.alternatives), "free": s.free} for s in p.sites]
            required = sum(not s["free"] for s in sites)
            sites_total += required
            clean += required == 0
            official = "-gov-" in r["id"]
            rows.append({
                "id": r["id"], "script": r["script"], "text": p.source, "gold": p.gold,
                "markup": r["markup"], "errors": required, "sites": sites,
                "pravopis_2010": [{"form": k, "citation": v}
                                  for k, v in r.get("pravopis_2010", {}).items()],
                "origin": "official text" if official else "handwritten",
                "provenance": r.get("source", "") if official else "handwritten for serbeval",
                "body": r.get("body", ""), "license": r["license"], "verified": True,
            })
    (out / "data" / f"{V2_CONFIG}.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    board = (ROOT / "results" / "v2" / "LEADERBOARD.md").read_text(encoding="utf-8").splitlines()
    blocks: list[list[str]] = []
    for prev, line in zip(["", *board], board, strict=False):
        if line.startswith("|"):
            if not prev.startswith("|"):
                blocks.append([])
            blocks[-1].append(line)
    table = "\n\n".join("\n".join(b) for b in blocks)
    return len(rows), sites_total, clean, table, sum(r["origin"] == "handwritten" for r in rows)


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "data").mkdir(parents=True)
    manifest = json.loads((OFFICIAL / "MANIFEST.json").read_text(encoding="utf-8"))
    shutil.copy(OFFICIAL / "MANIFEST.json", OUT / "MANIFEST.json")

    tasks = []
    sizes: dict[str, int] = {}
    for path in sorted(OFFICIAL.glob("*.jsonl")):
        shutil.copy(path, OUT / "data" / path.name)
        tasks.append(path.stem)
        sizes[path.stem] = sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line)

    licenses: Counter[str] = Counter()
    for path in OFFICIAL.glob("*.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line:
                licenses[json.loads(line)["license"]] += 1

    v2_n, v2_sites, v2_clean, v2_table, v2_hand = build_v2(OUT)
    configs = "\n".join(
        f"- config_name: {t}\n  data_files:\n  - split: test\n    path: data/{t}.jsonl"
        for t in [*tasks, V2_CONFIG]
    )
    rows = "\n".join(f"| `{t}` | {sizes[t]} | {DESCRIPTIONS.get(t, '')} |" for t in tasks)
    counts = manifest["counts"]
    card = f"""---
language:
- sr
license: cc-by-sa-4.0
pretty_name: serbeval
size_categories:
- n<1K
task_categories:
- question-answering
- text-generation
tags:
- serbian
- benchmark
- llm-evaluation
- grammar
- orthography
- lm-evaluation-harness
configs:
{configs}
---

# serbeval: a Serbian-language LLM benchmark (official set v1.2)

**Author:** Djordje Markovic ([@djolex999](https://github.com/djolex999))

**Code, task YAMLs, full leaderboard and methodology:** https://github.com/djolex999/serbeval

serbeval tests what translated benchmarks cannot carry over into Serbian: case government,
verbal aspect, the aorist and imperfect, sibilarization, numeral agreement, the ijekavian jat
reflex, pravopis (together/apart, hyphenated compounds, prefixoids), č/ć, and Cyrillic/Latin
consistency. It runs on
[lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness) 0.4.12.

This dataset is the **official set v1.2**: {sum(sizes.values())} items in {len(tasks)} tasks, plus the
harder **v2** passage-correction config `{V2_CONFIG}` ({v2_n} passages; see below).
v1.1 and v1.2 (2026-10-17) fixed gold answers and dropped 3 items; v1.2 checked every changed
gold against the text of Pravopis 2010 (tačka and page in the explanation). Both spellings are
accepted only where Pravopis 2010 and Klajn disagree. The history is under `errata` in
`MANIFEST.json`.

## Verification

Every item has a status in `MANIFEST.json`:

| Status | Items | Meaning |
| --- | --- | --- |
| `human` | {counts.get('human', 0)} | checked by a native speaker (blind baseline 29/30, plus the disputed items) |
| `consensus` | {counts.get('consensus', 0)} | fewer than 2 of the 4 strongest models disagreed with the gold |
| `derived` | {counts.get('derived', 0)} | correction item built mechanically from an official item |

Model consensus is not human verification. It is labelled separately on purpose.

Gold answers come from three places:
- hand-written items;
- the srLex lexicon, using only forms attested in the corpus;
- source checks against Pravopis 2010 and Klajn.

Items where the authorities disagree (e.g. *foto-aparat* vs *fotoaparat*) were dropped
rather than pinned to one side.

## Tasks

| Config | Items | What it tests |
| --- | --- | --- |
{rows}

Three item shapes:
- **MCQ:** `question`, `choices` (4), `answer_index`. Gold positions are balanced.
- **Cloze:** `question` with `____`, `cue`, and `answers`, the list of every accepted form.
  Scoring folds case, outer punctuation and script, but never diacritics or an intra-word
  hyphen.
- **Correction:** `text`, which may contain one error; `answers` (the corrected sentence, or
  the text itself when `has_error` is false). There is no cue.

All items also carry `id`, `task`, `category`, `explanation`, `script`, `difficulty`,
`source`, `verified` and `license`.

## Usage

```python
from datasets import load_dataset
ds = load_dataset("djolex999/serbeval", "srb_probe_aorist_imperfekat", split="test")
```

To score models with the exact prompts and scoring rules, use the task YAMLs from the GitHub
repo:

```
lm_eval --tasks srb_official --include_path lm_eval_tasks ...
```

## Leaderboard (official set v1.2, 30 models, zero-shot, runs 2026-10-12 to 17)

{leaderboard_top()}

The frontier is near ceiling (GPT-6 Sol 99%, three more at 98%); its misses are mostly
usage-over-norm spellings. Below it, the set separates models from 38% to 95%, and pravopis
separates them most. The best open-weights model is DeepSeek V4 Pro (95%); turning reasoning on does not raise any tested model by more than 2 points. Details and caveats, including a possible small
selection bias toward the four consensus models, are in the GitHub repo.

## v2: passage correction (`{V2_CONFIG}`, harder)

v1 saturated at the frontier, so v2 asks for whole passages: {v2_n} human-verified passages
(5–7 sentences, Latin and Cyrillic), {v2_sites} errors in total, {v2_clean} passages with no error at
all. The model gets `text` with no hint of how many errors there are or what kind, and must
return the corrected passage. The errors sit where usage and the norm part ways: polusloženice
and compounds (*ekspres lonac*, *kontakt osoba*, *spomen-ploča*), together/apart (*na brzinu*,
*bilo gde*, *usput*), compound adjectives, *hteo – ne hteo*, č/ć. Every gold form cites
Pravopis 2010 (tačka/page) in `pravopis_2010` (list of `form`, `citation`). {v2_hand} passages
were drafted for serbeval with an LLM and checked by a native speaker; {v2_n - v2_hand} are official
texts of Serbian public bodies (not copyrighted, ZASP art. 6), many with the institution's own
real errors.

Fields: `text` (model input), `gold` (corrected passage), `sites` (each error: `wrong`,
accepted `right` forms, and `free` when both forms are acceptable — no credit, no penalty),
`markup` (`{{right|wrong}}` inline), `origin`, `provenance`, `license`.

Scoring (GitHub: `serbeval.passage`): headline is the share of passages corrected exactly
(case, punctuation and script folded; diacritics and intra-word hyphens never); per-edit recall
and precision are diagnostics, and precision catches over-correction.

### v2 results (first run, 2026-10-22, zero-shot)

{v2_table}

The first table compares like with like: per error, frontier models fix ~86–89% on v2 against
~98–99% item accuracy on v1.2, i.e. roughly 5–10× more mistakes. "Passages fully correct" falls
further (72–74%) because it is all-or-nothing over ~4 errors per passage. The errors sit where
usage diverges from the norm (*kontakt-osoba*, *ekspres-lonac*, *nabrzinu*, *do viđenja*), so v2
measures norm adherence in those spots, not general Serbian ability. Command A+'s API returned
empty answers, so its row is not reliable.

## License

Items carry their own `license` field: {licenses.get('CC-BY-4.0', 0)} are CC BY 4.0
(hand-written for this project) and {licenses.get('CC-BY-SA-4.0', 0)} are CC BY-SA 4.0
(word forms from srLex). In `{V2_CONFIG}`, handwritten passages are CC BY 4.0 and official
texts are not copyrighted works (Serbian Copyright Act, art. 6). The dataset as a whole is
distributed under **CC BY-SA 4.0**.

Attribution:
- **srLex 1.3**: Ljubešić, Nikola. CLARIN.SI. CC BY-SA 4.0.
  https://www.clarin.si/repository/xmlui/handle/11356/1233
- **UD_Serbian-SET**: Samardžić, Tanja; Miletić, Aleksandra; Ljubešić, Nikola. CC BY-SA 4.0.

## Citation

```bibtex
@misc{{serbeval2026,
  title  = {{serbeval: a Serbian-language benchmark for large language models}},
  author = {{Markovic, Djordje}},
  note   = {{GitHub: @djolex999}},
  year   = {{2026}},
  url    = {{https://github.com/djolex999/serbeval}}
}}
```
"""
    (OUT / "README.md").write_text(card, encoding="utf-8")
    print(f"OK: {sum(sizes.values())} items, {len(tasks)} configs + v2 ({v2_n} passages) -> {OUT}")


if __name__ == "__main__":
    main()
