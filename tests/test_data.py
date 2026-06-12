import json
from pathlib import Path

from serbeval.data import load_items, save_items, validate_dataset
from serbeval.schema import EvalItem


def make_item(**overrides: object) -> EvalItem:
    raw: dict[str, object] = {
        "id": "srb-grammar-padezi-0001",
        "task": "srb_grammar",
        "category": "padezi",
        "question": "Dopuni rečenicu: Pišem ____.",
        "choices": ["olovkom", "sa olovkom", "olovka", "olovku"],
        "answer_index": 0,
        "explanation": "Instrumental sredstva ide bez predloga 'sa'.",
        "script": "latin",
        "source": "handwritten-claude",
    }
    raw.update(overrides)
    return EvalItem.model_validate(raw)


def test_jsonl_round_trip(tmp_path: Path) -> None:
    items = [make_item(), make_item(id="srb-grammar-padezi-0002")]
    path = tmp_path / "items.jsonl"
    save_items(items, path)
    loaded = load_items(path)
    assert loaded == items
    # one JSON object per line
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["id"] == "srb-grammar-padezi-0001"


def test_validate_flags_duplicate_ids() -> None:
    problems = validate_dataset([make_item(), make_item()])
    assert any("duplicate id" in p for p in problems)


def test_validate_flags_duplicate_questions() -> None:
    problems = validate_dataset([make_item(), make_item(id="srb-grammar-padezi-0002")])
    assert any("duplicate question" in p for p in problems)


def test_validate_flags_cyrillic_text_in_latin_item() -> None:
    item = make_item(question="Допуни реченицу: Пишем ____.")
    problems = validate_dataset([item])
    assert any("script" in p for p in problems)


def test_validate_flags_latin_text_in_cyrillic_item() -> None:
    item = make_item(script="cyrillic")  # question is latin
    problems = validate_dataset([item])
    assert any("script" in p for p in problems)


def test_validate_accepts_clean_dataset() -> None:
    items = [
        make_item(),
        make_item(
            id="srb-grammar-padezi-0002",
            question="Dopuni rečenicu: Idem ____.",
            choices=["u školu", "u školi", "kod škole", "ka školi u"],
        ),
    ]
    assert validate_dataset(items) == []


def _pair(answer_a: int = 0, answer_b: int = 0) -> list[EvalItem]:
    return [
        make_item(
            id="srb-cyr-0001-lat",
            task="srb_cyrillic_agreement",
            pair_id="srb-cyr-0001",
            answer_index=answer_a,
        ),
        make_item(
            id="srb-cyr-0001-cyr",
            task="srb_cyrillic_agreement",
            pair_id="srb-cyr-0001",
            script="cyrillic",
            question="Допуни реченицу: Пишем ____.",
            choices=["оловком", "са оловком", "оловка", "оловку"],
            answer_index=answer_b,
        ),
    ]


def test_validate_accepts_well_formed_pair() -> None:
    assert validate_dataset(_pair()) == []


def test_validate_flags_pair_with_mismatched_answers() -> None:
    problems = validate_dataset(_pair(answer_a=0, answer_b=1))
    assert any("pair" in p for p in problems)


def test_validate_flags_incomplete_pair() -> None:
    problems = validate_dataset(_pair()[:1])
    assert any("pair" in p for p in problems)
