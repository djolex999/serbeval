import json
from pathlib import Path

import pytest

from serbeval.cli import main


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")


def valid_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
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
    row.update(overrides)
    return row


def test_validate_clean_file_exits_zero(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "items.jsonl"
    write_jsonl(path, [valid_row()])
    assert main(["validate", str(path)]) == 0
    assert "OK" in capsys.readouterr().out


def test_validate_broken_file_exits_one(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "items.jsonl"
    write_jsonl(path, [valid_row(), valid_row()])  # duplicate id
    assert main(["validate", str(path)]) == 1
    assert "duplicate id" in capsys.readouterr().out


def test_validate_schema_error_exits_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "items.jsonl"
    write_jsonl(path, [valid_row(answer_index=9)])
    assert main(["validate", str(path)]) == 1
