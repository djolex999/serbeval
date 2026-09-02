import pytest
from pydantic import ValidationError

from serbeval.schema import EvalItem


def make_raw(**overrides: object) -> dict[str, object]:
    raw: dict[str, object] = {
        "id": "srb-grammar-enklitike-0001",
        "task": "srb_grammar",
        "category": "enklitike",
        "question": "Koja je rečenica gramatički ispravna?",
        "choices": [
            "Ja sam mu ga dao juče.",
            "Ja mu sam ga dao juče.",
            "Ja mu ga sam dao juče.",
            "Sam ja mu ga dao juče.",
        ],
        "answer_index": 0,
        "explanation": "Enklitike idu redom: glagolska 'sam' pre zameničkih 'mu ga'... ",
        "script": "latin",
        "source": "handwritten-claude",
    }
    raw.update(overrides)
    return raw


def test_valid_item_parses_with_defaults() -> None:
    item = EvalItem.model_validate(make_raw())
    assert item.id == "srb-grammar-enklitike-0001"
    assert item.verified is False
    assert item.pair_id is None
    assert item.license == "CC-BY-4.0"


def test_rejects_wrong_choice_count() -> None:
    with pytest.raises(ValidationError, match="choices"):
        EvalItem.model_validate(make_raw(choices=["a", "b", "c"]))


def test_rejects_duplicate_choices() -> None:
    with pytest.raises(ValidationError, match="unique"):
        EvalItem.model_validate(make_raw(choices=["a", "b", "b", "d"]))


def test_rejects_answer_index_out_of_range() -> None:
    with pytest.raises(ValidationError, match="answer_index"):
        EvalItem.model_validate(make_raw(answer_index=4))


def test_rejects_empty_question() -> None:
    with pytest.raises(ValidationError, match="question"):
        EvalItem.model_validate(make_raw(question="   "))


def test_rejects_unknown_script() -> None:
    with pytest.raises(ValidationError):
        EvalItem.model_validate(make_raw(script="glagolitic"))


def test_answer_letter_property() -> None:
    item = EvalItem.model_validate(make_raw(answer_index=2))
    assert item.answer_letter == "C"


def test_difficulty_defaults_to_none() -> None:
    item = EvalItem.model_validate(make_raw())
    assert item.difficulty is None


def test_difficulty_accepts_known_tiers() -> None:
    for tier in ("easy", "medium", "hard"):
        item = EvalItem.model_validate(make_raw(difficulty=tier))
        assert item.difficulty == tier


def test_difficulty_rejects_unknown_tier() -> None:
    with pytest.raises(ValidationError, match="difficulty"):
        EvalItem.model_validate(make_raw(difficulty="trivial"))
