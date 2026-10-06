from collections import Counter
from pathlib import Path

from serbeval.balance import balance_positions
from serbeval.schema import EvalItem


def item(i: int, answer_index: int = 0, **overrides: object) -> EvalItem:
    raw: dict[str, object] = {
        "id": f"srb-grammar-padezi-{i:04d}",
        "task": "srb_grammar",
        "category": "padezi",
        "question": f"Pitanje {i}?",
        "choices": [f"tačno {i}", f"pogrešno1 {i}", f"pogrešno2 {i}", f"pogrešno3 {i}"],
        "answer_index": answer_index,
        "explanation": "e",
        "script": "latin",
        "source": "handwritten-claude",
    }
    raw.update(overrides)
    return EvalItem.model_validate(raw)


def letters(items: list[EvalItem]) -> Counter[str]:
    return Counter(i.answer_letter for i in items)


def test_gold_positions_end_up_even() -> None:
    # The seed set had gold at A for 30 of 50 grammar items and never at D, so a model
    # that always answers "A" scored 60% without knowing any Serbian.
    balanced = balance_positions([item(i) for i in range(40)])
    assert letters(balanced) == Counter({"A": 10, "B": 10, "C": 10, "D": 10})


def test_uneven_counts_differ_by_at_most_one() -> None:
    counts = letters(balance_positions([item(i) for i in range(30)]))
    assert set(counts) == {"A", "B", "C", "D"}
    assert max(counts.values()) - min(counts.values()) <= 1


def test_the_correct_answer_text_is_preserved() -> None:
    before = [item(i) for i in range(12)]
    after = balance_positions(before)
    for old, new in zip(before, after, strict=True):
        assert new.choices[new.answer_index] == old.choices[old.answer_index]


def test_only_the_order_changes() -> None:
    before = [item(i) for i in range(12)]
    for old, new in zip(before, balance_positions(before), strict=True):
        assert sorted(new.choices) == sorted(old.choices)
        assert (new.id, new.question, new.explanation) == (old.id, old.question, old.explanation)


def test_distractors_keep_their_relative_order() -> None:
    new = balance_positions([item(i) for i in range(8)])
    for it in new:
        distractors = [c for j, c in enumerate(it.choices) if j != it.answer_index]
        assert [d.split()[0] for d in distractors] == ["pogrešno1", "pogrešno2", "pogrešno3"]


def test_is_deterministic_and_idempotent() -> None:
    once = balance_positions([item(i) for i in range(20)])
    assert balance_positions([item(i) for i in range(20)]) == once
    assert balance_positions(once) == once


def test_a_script_pair_gets_the_same_permutation() -> None:
    # The Cyrillic item's choices are transliterations of the Latin item's, position
    # by position. Permuting the two differently would break that alignment and make
    # pair_agreement compare different answers.
    lat = item(1, task="srb_cyrillic_agreement", pair_id="p1", id="p1-lat",
               choices=["pet", "šest", "sedam", "osam"])
    cyr = item(1, task="srb_cyrillic_agreement", pair_id="p1", id="p1-cyr", script="cyrillic",
               question="Питање?", choices=["пет", "шест", "седам", "осам"])
    pool = [lat, cyr] + [item(i) for i in range(2, 9)]
    out = {i.id: i for i in balance_positions(pool)}
    assert out["p1-lat"].answer_index == out["p1-cyr"].answer_index
    translit = {"pet": "пет", "šest": "шест", "sedam": "седам", "osam": "осам"}
    assert [translit[c] for c in out["p1-lat"].choices] == out["p1-cyr"].choices


def test_balanced_output_still_validates() -> None:
    from serbeval.data import validate_dataset

    assert validate_dataset(balance_positions([item(i) for i in range(16)])) == []


# --- guard on the shipped data ---------------------------------------------


def test_shipped_mcq_datasets_have_no_position_bias() -> None:
    # Fails the build if the gold letter drifts out of balance again — e.g. after
    # merging generated items, which Claude tends to write with the answer first.
    from serbeval.data import load_items

    root = Path(__file__).resolve().parent.parent / "data"
    for task in ("srb_grammar", "srb_idioms", "srb_cyrillic_agreement"):
        counts = letters(load_items(root / task / "items.jsonl"))
        assert set(counts) == {"A", "B", "C", "D"}, (task, counts)
        assert max(counts.values()) - min(counts.values()) <= 2, (task, counts)
