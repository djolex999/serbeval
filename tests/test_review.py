import json
from pathlib import Path

import pytest

from serbeval.data import load_items, save_items, validate_dataset
from serbeval.review import apply_decision, build_units, format_unit, run_review
from serbeval.schema import EvalItem


def grammar_item(n: int, verified: bool = False) -> EvalItem:
    return EvalItem(
        id=f"srb-grammar-padezi-{n:04d}",
        task="srb_grammar",
        category="padezi",
        question=f"Pitanje broj {n}?",
        choices=[f"a{n}", f"b{n}", f"c{n}", f"d{n}"],
        answer_index=1,
        explanation="Zato.",
        script="latin",
        source="handwritten-claude",
        verified=verified,
    )


def pair_items(n: int, verified: bool = False) -> list[EvalItem]:
    base = {
        "task": "srb_cyrillic_agreement",
        "category": "matematika",
        "answer_index": 2,
        "explanation": "Činjenica.",
        "source": "handwritten-claude",
        "verified": verified,
        "pair_id": f"srb-cyr-{n:04d}",
    }
    choices = [str(n + 100), str(n + 200), str(2 * n), str(n + 300)]
    lat = EvalItem(
        id=f"srb-cyr-{n:04d}-lat",
        question=f"Koliko je {n} plus {n}?",
        choices=choices,
        script="latin",
        **base,
    )
    cyr = EvalItem(
        id=f"srb-cyr-{n:04d}-cyr",
        question=f"Колико је {n} плус {n}?",
        choices=choices,
        script="cyrillic",
        **base,
    )
    return [lat, cyr]


# --- build_units ---


def test_build_units_skips_verified_items() -> None:
    items = [grammar_item(1, verified=True), grammar_item(2)]
    units = build_units(items)
    assert [[i.id for i in u] for u in units] == [["srb-grammar-padezi-0002"]]


def test_build_units_groups_pairs_together() -> None:
    items = [*pair_items(1), grammar_item(1)]
    units = build_units(items)
    pair_unit = next(u for u in units if len(u) == 2)
    assert {i.script for i in pair_unit} == {"latin", "cyrillic"}


def test_build_units_pair_with_one_verified_member_still_reviews_both() -> None:
    lat, cyr = pair_items(1)
    lat = lat.model_copy(update={"verified": True})
    units = build_units([lat, cyr])
    assert len(units) == 1
    assert {i.id for i in units[0]} == {lat.id, cyr.id}


# --- apply_decision ---


def test_verify_flips_verified_flag() -> None:
    items = [grammar_item(1), grammar_item(2)]
    kept, discarded = apply_decision(items, {items[0].id}, "verify", reason="")
    assert [i.verified for i in kept] == [True, False]
    assert discarded == []


def test_reject_removes_items_and_records_reason() -> None:
    items = [grammar_item(1), grammar_item(2)]
    kept, discarded = apply_decision(items, {items[0].id}, "reject", reason="dvosmisleno")
    assert [i.id for i in kept] == ["srb-grammar-padezi-0002"]
    assert len(discarded) == 1
    assert discarded[0]["dropReason"] == "human-review"
    assert discarded[0]["reasons"] == ["dvosmisleno"]
    assert discarded[0]["id"] == "srb-grammar-padezi-0001"


def test_reject_of_pair_keeps_dataset_valid() -> None:
    items = pair_items(1) + pair_items(2)
    unit_ids = {i.id for i in pair_items(1)}
    kept, discarded = apply_decision(items, unit_ids, "reject", reason="los par")
    assert validate_dataset(kept) == []
    assert len(kept) == 2
    assert len(discarded) == 2


# --- format_unit ---


def test_format_unit_marks_gold_answer_and_shows_both_scripts() -> None:
    unit = pair_items(3)
    text = format_unit(unit)
    assert "Koliko je 3 plus 3?" in text
    assert "Колико је 3 плус 3?" in text
    assert "C." in text  # answer_index 2 -> C
    assert "✓" in text


# --- run_review (scripted IO) ---


def test_run_review_verify_reject_skip_quit(tmp_path: Path) -> None:
    task_dir = tmp_path / "srb_grammar"
    items = [grammar_item(n) for n in range(1, 5)]
    save_items(items, task_dir / "items.jsonl")

    answers = iter(["y", "meh", "n", "razlog odbacivanja", "s", "q"])
    outputs: list[str] = []
    summary = run_review(
        task="srb_grammar",
        data_dir=str(tmp_path),
        input_fn=lambda _prompt: next(answers),
        print_fn=outputs.append,
    )
    # "meh" is not a valid key: re-prompted, then n + reason consumed
    assert summary == {"verified": 1, "rejected": 1, "skipped": 1, "remaining": 2}

    kept = load_items(task_dir / "items.jsonl")
    assert [i.verified for i in kept] == [True, False, False]
    discarded = [
        json.loads(line)
        for line in (task_dir / "discarded.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert discarded[-1]["reasons"] == ["razlog odbacivanja"]


def test_run_review_saves_after_each_decision(tmp_path: Path) -> None:
    task_dir = tmp_path / "srb_grammar"
    save_items([grammar_item(1), grammar_item(2)], task_dir / "items.jsonl")

    def scripted(_prompt: str) -> str:
        # first decision lands on disk before the crash
        on_disk = load_items(task_dir / "items.jsonl")
        if on_disk[0].verified:
            raise KeyboardInterrupt
        return "y"

    summary = run_review(
        task="srb_grammar",
        data_dir=str(tmp_path),
        input_fn=scripted,
        print_fn=lambda _s: None,
    )
    assert summary["verified"] == 1
    assert load_items(task_dir / "items.jsonl")[0].verified is True


def test_run_review_eof_quits_cleanly(tmp_path: Path) -> None:
    task_dir = tmp_path / "srb_grammar"
    save_items([grammar_item(1)], task_dir / "items.jsonl")

    def eof(_prompt: str) -> str:
        raise EOFError

    summary = run_review(
        task="srb_grammar", data_dir=str(tmp_path), input_fn=eof, print_fn=lambda _s: None
    )
    assert summary == {"verified": 0, "rejected": 0, "skipped": 0, "remaining": 1}


def test_run_review_nothing_to_review(tmp_path: Path) -> None:
    task_dir = tmp_path / "srb_grammar"
    save_items([grammar_item(1, verified=True)], task_dir / "items.jsonl")
    summary = run_review(
        task="srb_grammar",
        data_dir=str(tmp_path),
        input_fn=lambda _p: "q",
        print_fn=lambda _s: None,
    )
    assert summary == {"verified": 0, "rejected": 0, "skipped": 0, "remaining": 0}


def test_run_review_pair_end_to_end_reject_keeps_dataset_valid(tmp_path: Path) -> None:
    task_dir = tmp_path / "srb_cyrillic_agreement"
    save_items([*pair_items(1), *pair_items(2)], task_dir / "items.jsonl")

    answers = iter(["n", "los par", "y", "q"])
    outputs: list[str] = []
    summary = run_review(
        task="srb_cyrillic_agreement",
        data_dir=str(tmp_path),
        input_fn=lambda _p: next(answers),
        print_fn=outputs.append,
    )
    assert summary == {"verified": 1, "rejected": 1, "skipped": 0, "remaining": 0}
    kept = load_items(task_dir / "items.jsonl")
    assert validate_dataset(kept) == []
    assert len(kept) == 2
    assert all(i.verified for i in kept)
    # both pair members went to discarded, none printed a WARNING
    discarded = (task_dir / "discarded.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(discarded) == 2
    assert not [line for line in outputs if line.startswith("WARNING")]


def test_run_review_quit_still_runs_integrity_check(tmp_path: Path) -> None:
    task_dir = tmp_path / "srb_grammar"
    # two items with identical question text -> validate_dataset problem
    broken = grammar_item(2).model_copy(update={"question": grammar_item(1).question})
    save_items([grammar_item(1), broken], task_dir / "items.jsonl")

    outputs: list[str] = []
    run_review(
        task="srb_grammar",
        data_dir=str(tmp_path),
        input_fn=lambda _p: "q",
        print_fn=outputs.append,
    )
    assert any(line.startswith("WARNING") for line in outputs)


def test_run_review_refuses_duplicate_ids(tmp_path: Path) -> None:
    task_dir = tmp_path / "srb_grammar"
    dupe = grammar_item(1).model_copy(update={"question": "Drugo pitanje?"})
    save_items([grammar_item(1), dupe], task_dir / "items.jsonl")

    outputs: list[str] = []
    summary = run_review(
        task="srb_grammar",
        data_dir=str(tmp_path),
        input_fn=lambda _p: "y",
        print_fn=outputs.append,
    )
    assert summary["verified"] == 0
    assert any("duplicate id" in line for line in outputs)
    # nothing was touched on disk
    assert [i.verified for i in load_items(task_dir / "items.jsonl")] == [False, False]


def test_run_review_stops_when_file_changes_on_disk(tmp_path: Path) -> None:
    task_dir = tmp_path / "srb_grammar"
    save_items([grammar_item(1), grammar_item(2)], task_dir / "items.jsonl")

    def racing(_prompt: str) -> str:
        # another session rewrites the file before every answer
        save_items(load_items(task_dir / "items.jsonl"), task_dir / "items.jsonl")
        return "y"

    outputs: list[str] = []
    summary = run_review(
        task="srb_grammar", data_dir=str(tmp_path), input_fn=racing, print_fn=outputs.append
    )
    assert summary["verified"] == 0
    assert any("changed on disk" in line for line in outputs)


def test_save_items_is_atomic_on_interrupt(tmp_path: Path) -> None:
    # an exception raised mid-serialization must leave the original file intact
    items = [grammar_item(n) for n in range(1, 6)]
    path = tmp_path / "items.jsonl"
    save_items(items, path)

    class Boom(Exception):
        pass

    exploding = [*items]

    class ExplodingItem(EvalItem):
        def model_dump(self, **kwargs: object) -> dict[str, object]:  # type: ignore[override]
            raise Boom

    exploding[3] = ExplodingItem.model_construct(**items[3].__dict__)
    with pytest.raises(Boom):
        save_items(exploding, path)
    assert len(load_items(path)) == 5  # original untouched
