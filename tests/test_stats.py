import json
from pathlib import Path

from serbeval.data import save_items
from serbeval.stats import collect_stats, format_stats
from test_review import grammar_item, pair_items


def test_collect_stats_counts_items(tmp_path: Path) -> None:
    save_items(
        [grammar_item(1, verified=True), grammar_item(2)],
        tmp_path / "srb_grammar" / "items.jsonl",
    )
    (tmp_path / "srb_grammar" / "candidates.jsonl").write_text(
        json.dumps(grammar_item(9).model_dump()) + "\n", encoding="utf-8"
    )
    (tmp_path / "srb_grammar" / "discarded.jsonl").write_text(
        '{"question": "x", "reasons": ["y"]}\n', encoding="utf-8"
    )
    save_items(pair_items(1), tmp_path / "srb_cyrillic_agreement" / "items.jsonl")

    stats = collect_stats(str(tmp_path))
    by_task = {s.task: s for s in stats}
    grammar = by_task["srb_grammar"]
    assert (grammar.total, grammar.verified, grammar.candidates, grammar.discarded) == (2, 1, 1, 1)
    assert grammar.categories == {"padezi": 2}
    assert grammar.pairs is None

    cyr = by_task["srb_cyrillic_agreement"]
    assert cyr.pairs == 1
    assert cyr.total == 2


def test_collect_stats_empty_dir(tmp_path: Path) -> None:
    assert collect_stats(str(tmp_path)) == []


def test_format_stats_shows_progress(tmp_path: Path) -> None:
    save_items(
        [grammar_item(1, verified=True), grammar_item(2)],
        tmp_path / "srb_grammar" / "items.jsonl",
    )
    text = format_stats(collect_stats(str(tmp_path)))
    assert "srb_grammar" in text
    assert "1/2" in text


def test_collect_stats_reports_broken_file_without_aborting(tmp_path: Path) -> None:
    save_items([grammar_item(1)], tmp_path / "srb_grammar" / "items.jsonl")
    bad = tmp_path / "srb_broken"
    bad.mkdir()
    (bad / "items.jsonl").write_text("{not json\n", encoding="utf-8")

    stats = collect_stats(str(tmp_path))
    by_task = {s.task: s for s in stats}
    assert by_task["srb_broken"].error is not None
    assert by_task["srb_grammar"].total == 1

    text = format_stats(stats)
    assert "ERROR" in text
    assert "srb_grammar: 0/1 verified" in text
