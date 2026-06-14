"""Generate the srb_cyrillic_agreement paired dataset.

Each base item (factual, script-independent, single correct answer) becomes two items sharing a
pair_id: one Latin, one Cyrillic (deterministically transliterated). A/B/C/D labels are added at
prompt time, so stored choices are pure content and transliterate cleanly.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from serbeval.data import save_items, validate_dataset
from serbeval.schema import EvalItem
from serbeval.translit import latin_to_cyrillic

ROOT = Path(__file__).resolve().parent.parent
TASK = "srb_cyrillic_agreement"

# (category, question, choices, answer_index)
BASE: list[tuple[str, str, list[str], int]] = [
    ("matematika", "Koliko je 7 puta 8?", ["54", "56", "58", "64"], 1),
    ("matematika", "Koliko iznosi zbir brojeva 25 i 17?", ["32", "42", "43", "52"], 1),
    ("matematika", "Koliko iznosi sto podeljeno sa četiri?", ["dvadeset", "dvadeset pet", "trideset", "pedeset"], 1),
    ("matematika", "Koliko iznosi zbir uglova u trouglu?", ["90 stepeni", "180 stepeni", "270 stepeni", "360 stepeni"], 1),
    ("matematika", "Koliko strana ima kvadrat?", ["tri", "četiri", "pet", "šest"], 1),
    ("geografija", "Koji je glavni grad Srbije?", ["Beograd", "Novi Sad", "Niš", "Kragujevac"], 0),
    ("geografija", "U kojoj se državi nalazi grad Pariz?", ["Italija", "Španija", "Francuska", "Nemačka"], 2),
    ("geografija", "Koja je najduža reka u Evropi?", ["Dunav", "Volga", "Rajna", "Sena"], 1),
    ("geografija", "Koji je najveći okean na Zemlji?", ["Atlantski", "Indijski", "Tihi", "Severni ledeni"], 2),
    ("priroda", "Koja je najveća planeta u Sunčevom sistemu?", ["Zemlja", "Mars", "Jupiter", "Saturn"], 2),
    ("priroda", "Koja boja nastaje mešanjem plave i žute boje?", ["zelena", "ljubičasta", "narandžasta", "braon"], 0),
    ("priroda", "Koliko nogu ima odrasli pauk?", ["šest", "osam", "deset", "dvanaest"], 1),
    ("priroda", "Koja životinja je poznata kao „kralj životinja“?", ["tigar", "lav", "slon", "medved"], 1),
    ("opste", "Koliko meseci ima jedna godina?", ["deset", "jedanaest", "dvanaest", "trinaest"], 2),
    ("opste", "Koliko sati ima jedan dan?", ["dvanaest", "šesnaest", "dvadeset", "dvadeset četiri"], 3),
]


def main() -> int:
    items: list[EvalItem] = []
    for seq, (category, question, choices, answer_index) in enumerate(BASE, start=1):
        pair_id = f"srb-cyr-{seq:04d}"
        base_id = f"srb-cyrillic-agreement-{category}-{seq:04d}"
        items.append(
            EvalItem(
                id=f"{base_id}-lat", task=TASK, category=category, question=question,
                choices=choices, answer_index=answer_index, script="latin", pair_id=pair_id,
                explanation="Činjenično pitanje; tačan odgovor je nezavisan od pisma.",
                source="handwritten-claude", verified=False,
            )
        )
        items.append(
            EvalItem(
                id=f"{base_id}-cyr", task=TASK, category=category,
                question=latin_to_cyrillic(question),
                choices=[latin_to_cyrillic(c) for c in choices],
                answer_index=answer_index, script="cyrillic", pair_id=pair_id,
                explanation=latin_to_cyrillic("Činjenično pitanje; tačan odgovor je nezavisan od pisma."),
                source="handwritten-claude", verified=False,
            )
        )

    problems = validate_dataset(items)
    if problems:
        print("VALIDATION FAILED:")
        for p in problems:
            print(f"  {p}")
        return 1

    save_items(items, ROOT / "data" / TASK / "items.jsonl")
    print(f"{TASK}: {len(items)} items ({len(BASE)} pairs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
