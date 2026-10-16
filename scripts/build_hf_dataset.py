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

    configs = "\n".join(
        f"- config_name: {t}\n  data_files:\n  - split: test\n    path: data/{t}.jsonl"
        for t in tasks
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

# serbeval: a Serbian-language LLM benchmark (official set v1)

**Author:** Djordje Markovic ([@djolex999](https://github.com/djolex999))

**Code, task YAMLs, full leaderboard and methodology:** https://github.com/djolex999/serbeval

serbeval tests what translated benchmarks cannot carry over into Serbian: case government,
verbal aspect, the aorist and imperfect, sibilarization, numeral agreement, the ijekavian jat
reflex, pravopis (together/apart, hyphenated compounds, prefixoids), č/ć, and Cyrillic/Latin
consistency. It runs on
[lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness) 0.4.12.

This dataset is the **official set v1**: {sum(sizes.values())} items in {len(tasks)} tasks.

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

## Leaderboard (official set v1, 30 models, zero-shot, 2026-10-12 to 17)

{leaderboard_top()}

The frontier is at ceiling (five models at 98%). Below it, the set separates models from
38% to 98%, and pravopis separates them most. The best open-weights model is DeepSeek V4 Pro
(95%); turning reasoning on does not raise any tested model by more than 2 points. Details and caveats, including a possible small
selection bias toward the four consensus models, are in the GitHub repo.

## License

Items carry their own `license` field: {licenses.get('CC-BY-4.0', 0)} are CC BY 4.0
(hand-written for this project) and {licenses.get('CC-BY-SA-4.0', 0)} are CC BY-SA 4.0
(word forms from srLex). The dataset as a whole is distributed under **CC BY-SA 4.0**.

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
    print(f"OK: {sum(sizes.values())} items, {len(tasks)} configs -> {OUT}")


if __name__ == "__main__":
    main()
