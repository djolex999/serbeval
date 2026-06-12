from unittest.mock import Mock

from serbeval.generate import (
    CandidateBatch,
    CandidateItem,
    build_prompt,
    generate_candidates,
    next_id,
)


def make_candidate(question: str = "Dopuni rečenicu: Pišem ____.") -> CandidateItem:
    return CandidateItem(
        question=question,
        choices=["olovkom", "sa olovkom", "olovka", "olovku"],
        answer_index=0,
        explanation="Instrumental sredstva ide bez predloga 'sa'.",
    )


def mock_client(batch: CandidateBatch) -> Mock:
    client = Mock()
    client.messages.parse.return_value = Mock(parsed_output=batch)
    return client


def test_next_id_starts_at_one() -> None:
    assert next_id("srb_grammar", "padezi", set()) == "srb-grammar-padezi-0001"


def test_next_id_increments_past_existing() -> None:
    existing = {"srb-grammar-padezi-0001", "srb-grammar-padezi-0007", "srb-grammar-vid-0009"}
    assert next_id("srb_grammar", "padezi", existing) == "srb-grammar-padezi-0008"


def test_build_prompt_mentions_category_count_and_existing() -> None:
    prompt = build_prompt("srb_grammar", "enklitike", 5, ["Postojeće pitanje?"])
    assert "enklitike" in prompt
    assert "5" in prompt
    assert "Postojeće pitanje?" in prompt


def test_generate_candidates_assigns_ids_and_metadata() -> None:
    batch = CandidateBatch(items=[make_candidate(), make_candidate("Drugo pitanje ____?")])
    client = mock_client(batch)

    items = generate_candidates(
        client,
        task="srb_grammar",
        category="padezi",
        n=2,
        model="claude-opus-4-8",
        existing_ids={"srb-grammar-padezi-0003"},
        existing_questions=set(),
    )

    assert [i.id for i in items] == ["srb-grammar-padezi-0004", "srb-grammar-padezi-0005"]
    assert all(i.verified is False for i in items)
    assert all(i.source == "generated-claude-claude-opus-4-8" for i in items)
    assert all(i.task == "srb_grammar" and i.category == "padezi" for i in items)
    client.messages.parse.assert_called_once()
    assert client.messages.parse.call_args.kwargs["model"] == "claude-opus-4-8"


def test_generate_skips_duplicate_questions() -> None:
    dupe = "Dopuni rečenicu: Pišem ____."
    batch = CandidateBatch(items=[make_candidate(dupe), make_candidate("Sveže pitanje ____?")])
    client = mock_client(batch)

    items = generate_candidates(
        client,
        task="srb_grammar",
        category="padezi",
        n=2,
        model="claude-opus-4-8",
        existing_ids=set(),
        existing_questions={dupe},
    )

    assert len(items) == 1
    assert items[0].question == "Sveže pitanje ____?"
