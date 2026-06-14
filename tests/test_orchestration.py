"""Orchestration helpers wire the Claude-backed core to on-disk dataset files.

The Anthropic client is always mocked — these tests never hit the network.
"""

from pathlib import Path
from unittest.mock import Mock

from serbeval.data import load_items, save_items
from serbeval.generate import CandidateBatch, CandidateItem, run_generate
from serbeval.schema import EvalItem
from serbeval.selfcheck import run_selfcheck


def existing_item(**overrides: object) -> EvalItem:
    raw: dict[str, object] = {
        "id": "srb-grammar-padezi-0001",
        "task": "srb_grammar",
        "category": "padezi",
        "question": "Postojeće pitanje?",
        "choices": ["a", "b", "c", "d"],
        "answer_index": 0,
        "explanation": "x",
        "script": "latin",
        "source": "handwritten-claude",
    }
    raw.update(overrides)
    return EvalItem.model_validate(raw)


def test_run_generate_appends_to_candidates_skipping_existing(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    save_items([existing_item()], data_dir / "srb_grammar" / "items.jsonl")

    batch = CandidateBatch(
        items=[
            CandidateItem(
                question="Novo pitanje?",
                choices=["w", "x", "y", "z"],
                answer_index=1,
                explanation="zato",
            )
        ]
    )
    client = Mock()
    client.messages.parse.return_value = Mock(parsed_output=batch)

    written = run_generate(
        client,
        task="srb_grammar",
        category="padezi",
        n=1,
        model="claude-opus-4-8",
        data_dir=data_dir,
    )

    candidates = load_items(data_dir / "srb_grammar" / "candidates.jsonl")
    assert [c.question for c in candidates] == ["Novo pitanje?"]
    # id continues past the existing items.jsonl id
    assert candidates[0].id == "srb-grammar-padezi-0002"
    assert written == 1


def test_run_generate_is_idempotent_on_existing_candidates(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    cand = existing_item(id="srb-grammar-padezi-0005", question="Već kandidat?")
    save_items([cand], data_dir / "srb_grammar" / "candidates.jsonl")

    batch = CandidateBatch(
        items=[
            CandidateItem(
                question="Već kandidat?",
                choices=["a", "b", "c", "d"],
                answer_index=0,
                explanation="x",
            )
        ]
    )
    client = Mock()
    client.messages.parse.return_value = Mock(parsed_output=batch)

    written = run_generate(
        client, task="srb_grammar", category="padezi", n=1, model="m", data_dir=data_dir
    )
    assert written == 0
    assert len(load_items(data_dir / "srb_grammar" / "candidates.jsonl")) == 1


def test_run_selfcheck_partitions_candidates(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    keep = existing_item(id="srb-grammar-padezi-0010", question="Keep me?", answer_index=0)
    drop = existing_item(id="srb-grammar-padezi-0011", question="Drop me?", answer_index=0)
    save_items([keep, drop], data_dir / "srb_grammar" / "candidates.jsonl")

    # keep -> unanimous correct (A); drop -> disagreement (A,B,A)
    replies = iter(["A", "A", "A", "A", "B", "A"])
    client = Mock()
    client.messages.create.side_effect = lambda **_: Mock(
        content=[Mock(type="text", text=next(replies))]
    )

    summary = run_selfcheck(client, task="srb_grammar", runs=3, model="m", data_dir=data_dir)

    survivors = load_items(data_dir / "srb_grammar" / "candidates.jsonl")
    assert [s.question for s in survivors] == ["Keep me?"]
    discarded = (data_dir / "srb_grammar" / "discarded.jsonl").read_text(encoding="utf-8")
    assert "Drop me?" in discarded
    assert summary == {"kept": 1, "discarded": 1}
