#!/usr/bin/env python
"""Where models fail on v2: miss rate per error category, frontier vs all models (Markdown).

    PYTHONPATH=src python scripts/v2_error_categories.py

A site counts as missed when the model's passage does not reproduce its gold tokens (same
alignment as serbeval.passage). Free sites are skipped; Command A+ is left out (empty answers).
"""

import collections
import difflib
import json
from pathlib import Path

from serbeval.passage import Passage, _gold_variants, _tokens, extract_passage, parse_markup
from serbeval.translit import cyrillic_to_latin

ROOT = Path(__file__).resolve().parent.parent
FRONTIER = {"anthropic_claude-opus-5.5", "openai_gpt-6-sol"}
SKIP = {"cohere_command-a-plus"}
NAMED = [  # (substring of the gold form, category)
    ("ekspres", "*ekspres* apart (ekspres lonac)"), ("kontakt", "*kontakt* apart (kontakt osoba)"),
    ("džez", "*džez* apart (džez muzika)"), ("hteo", "*hteo – ne hteo* (dash, not hyphen)"),
    ("na brzinu", "*na brzinu* (not nabrzinu)"), ("doviđenja", "*doviđenja* (not do viđenja)"),
    ("vikend", "*vikend-* hyphen (vikend-kuća)"), ("spomen", "*spomen-* hyphen (spomen-ploča)"),
    ("general", "*general-* hyphen (general-major)"),
]


def category(right: str, wrong: str, cite: str) -> str:
    r, w = cyrillic_to_latin(right).lower(), cyrillic_to_latin(wrong).lower()
    for key, name in NAMED:
        if key in r:
            return name
    if "t. 33" in cite or w.replace("č", "ć") == r.replace("č", "ć"):
        return "č / ć"
    if "124" in cite:
        return "*ne* + verb apart (ne mogu)"
    if "t. 111" in cite or "t. 113" in cite or r.startswith(("ni ", "bilo ")):
        return "*ni* / *bilo* + word apart (ni s kim, bilo gde)"
    if "iako" in r:
        return "*iako* (not i ako)"
    if "-" in r and "-" not in w:
        return "other hyphenated compounds (srpsko-engleski)"
    if "-" in w and "-" not in r:
        return "compound adjectives / prefixoids together (naučnofantastični)"
    if " " in r and " " not in w:
        return "phrases apart (bez obzira, na primer)"
    if " " in w and " " not in r:
        return "adverbs together (napamet, uzalud)"
    return "other (real errors in the original texts)"


def fixed_sites(output: str, passage: Passage) -> list[bool]:
    out = _tokens(output)
    best: list[bool] | None = None
    for gold, spans in _gold_variants(passage):
        ops = [op for op in difflib.SequenceMatcher(None, gold, out, autojunk=False).get_opcodes()
               if op[0] != "equal"]
        hit = [not any((i1 < b and i2 > a) if i1 < i2 else (a < i1 < b) for _, i1, i2, _, _ in ops)
               for a, b in spans]
        if best is None or sum(hit) > sum(best):
            best = hit
    return best or []


def main() -> None:
    data = ROOT / "data" / "v2"
    keep = set(json.loads((data / "evaluation.json").read_text())["included_ids"])
    items = {r["id"]: r for path in data.glob("passages-*.jsonl")
             for r in map(json.loads, path.read_text(encoding="utf-8").splitlines()) if r["id"] in keep}
    sites: collections.Counter[str] = collections.Counter()
    miss = {"front": collections.Counter[str](), "all": collections.Counter[str]()}
    total = {"front": collections.Counter[str](), "all": collections.Counter[str]()}
    counted: set[tuple[str, int]] = set()
    for path in sorted((ROOT / "results" / "v2").glob("*.jsonl")):
        if path.stem in SKIP:
            continue
        groups = ["all", "front"] if path.stem in FRONTIER else ["all"]
        for answer in map(json.loads, path.read_text(encoding="utf-8").splitlines()):
            item = items.get(answer["id"])
            if item is None:
                continue
            passage = parse_markup(item["markup"])
            cites = item.get("pravopis_2010", {})
            for n, (site, ok) in enumerate(zip(passage.sites,
                                               fixed_sites(extract_passage(answer["raw"]), passage),
                                               strict=True)):
                if site.free:
                    continue
                right = cyrillic_to_latin(site.alternatives[0]).lower()
                cite = next((v for k, v in cites.items() if site.wrong in k or k in right), "")
                cat = category(site.alternatives[0], site.wrong, cite)
                if (item["id"], n) not in counted:
                    counted.add((item["id"], n))
                    sites[cat] += 1
                for g in groups:
                    total[g][cat] += 1
                    miss[g][cat] += not ok
    print("| Error type | Sites | Missed: frontier (Opus 5.5, GPT-6 Sol) | Missed: all 18 models |")
    print("|---|---|---|---|")
    for cat in sorted(total["all"], key=lambda c: -miss["all"][c] / total["all"][c]):
        front = f"{100 * miss['front'][cat] / total['front'][cat]:.0f}%" if total["front"][cat] else "–"
        print(f"| {cat} | {sites[cat]} | {front} | {100 * miss['all'][cat] / total['all'][cat]:.0f}% |")


if __name__ == "__main__":
    main()
