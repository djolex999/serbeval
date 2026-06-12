from unittest.mock import Mock

import pytest

from serbeval.schema import EvalItem
from serbeval.selfcheck import parse_answer, selfcheck_item


def make_item(answer_index: int = 0) -> EvalItem:
    return EvalItem.model_validate(
        {
            "id": "srb-grammar-padezi-0001",
            "task": "srb_grammar",
            "category": "padezi",
            "question": "Dopuni rečenicu: Pišem ____.",
            "choices": ["olovkom", "sa olovkom", "olovka", "olovku"],
            "answer_index": answer_index,
            "explanation": "Instrumental sredstva ide bez predloga 'sa'.",
            "script": "latin",
            "source": "generated-claude-claude-opus-4-8",
        }
    )


def client_answering(*texts: str) -> Mock:
    client = Mock()
    responses = [Mock(content=[Mock(type="text", text=t)]) for t in texts]
    client.messages.create.side_effect = responses
    return client


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("A", 0),
        ("Odgovor: B", 1),
        ("**C**", 2),
        ("D) olovku", 3),
        ("Ne znam.", None),
        ("", None),
    ],
)
def test_parse_answer(text: str, expected: int | None) -> None:
    assert parse_answer(text) == expected


def test_keeps_unanimous_correct() -> None:
    client = client_answering("A", "A", "Odgovor: A")
    result = selfcheck_item(client, "claude-opus-4-8", make_item(answer_index=0), runs=3)
    assert result.keep is True
    assert result.answers == [0, 0, 0]
    assert client.messages.create.call_count == 3


def test_discards_on_disagreement() -> None:
    client = client_answering("A", "B", "A")
    result = selfcheck_item(client, "claude-opus-4-8", make_item(answer_index=0), runs=3)
    assert result.keep is False
    assert "disagree" in (result.reason or "")


def test_discards_on_unanimous_wrong() -> None:
    client = client_answering("B", "B", "B")
    result = selfcheck_item(client, "claude-opus-4-8", make_item(answer_index=0), runs=3)
    assert result.keep is False
    assert "gold" in (result.reason or "")


def test_discards_on_unparseable_answer() -> None:
    client = client_answering("A", "Ne znam.", "A")
    result = selfcheck_item(client, "claude-opus-4-8", make_item(answer_index=0), runs=3)
    assert result.keep is False
