import json
from pathlib import Path
from unittest.mock import Mock

import pytest

import serbeval.cli as cli
from serbeval.cli import main


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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


def test_generate_subcommand_wiring(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from serbeval.generate import CandidateBatch, CandidateItem

    batch = CandidateBatch(
        items=[
            CandidateItem(
                question="Q?", choices=["a", "b", "c", "d"], answer_index=0, explanation="x"
            )
        ]
    )
    client = Mock()
    client.messages.parse.return_value = Mock(parsed_output=batch)
    monkeypatch.setattr(cli, "_make_client", lambda: client)

    code = main(
        ["generate", "--task", "srb_grammar", "--category", "padezi", "-n", "1",
         "--data-dir", str(tmp_path)]
    )
    assert code == 0
    assert "wrote 1 new candidate" in capsys.readouterr().out
    assert (tmp_path / "srb_grammar" / "candidates.jsonl").exists()


def test_selfcheck_subcommand_wiring(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    write_jsonl(
        tmp_path / "srb_grammar" / "candidates.jsonl",
        [valid_row(id="srb-grammar-padezi-0001", source="generated-claude-x")],
    )
    replies = iter(["A", "A", "A"])
    client = Mock()
    client.messages.create.side_effect = lambda **_: Mock(
        content=[Mock(type="text", text=next(replies))]
    )
    monkeypatch.setattr(cli, "_make_client", lambda: client)

    code = main(["selfcheck", "--task", "srb_grammar", "--runs", "3", "--data-dir", str(tmp_path)])
    assert code == 0
    assert "kept 1, discarded 0" in capsys.readouterr().out
