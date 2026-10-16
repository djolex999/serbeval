"""Cross-item lint for the official set: one lexical family, one spelling policy.

v1 accepted „kontakt-telefon“ (hyphen) but only „kontakt osobi“ (apart), and „ekspres-lonac“
but „ekspres pošiljku“ — the frontier's last "errors" were mostly these (v1.1 errata).
"""

import json
from collections import defaultdict
from pathlib import Path

OFFICIAL = Path(__file__).resolve().parent.parent / "data" / "official"
FAMILIES = ("kontakt", "ekspres", "foto", "auto", "radio", "video")


def _style(answer: str, first: str) -> str:
    rest = answer.lower().split(first, 1)[1]
    return "hyphen" if rest.startswith("-") else "apart" if rest.startswith(" ") else "together"


def test_each_compound_family_has_one_spelling_policy() -> None:
    policies: dict[str, dict[str, frozenset[str]]] = defaultdict(dict)
    for path in OFFICIAL.glob("*.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            first = str(row.get("cue", "")).split(" + ")[0].strip().lower()
            if first in FAMILIES:
                policies[first][row["id"]] = frozenset(_style(a, first) for a in row["answers"])
    assert policies, "no family items found"
    for first, by_item in policies.items():
        assert len(set(by_item.values())) == 1, f"{first}-: inconsistent {by_item}"
