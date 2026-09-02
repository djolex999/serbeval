import json
from pathlib import Path

from serbeval.report import collect_results, format_markdown


def write_results(
    path: Path,
    model_args: object = "model=claude-haiku-4-5",
    value: float = 0.84,
) -> None:
    payload = {
        "results": {
            "srb_grammar": {
                "alias": "srb_grammar",
                "exact_match,extract_answer": value,
                "exact_match_stderr,extract_answer": 0.031,
            },
            "srb_cyrillic_agreement": {
                "alias": "srb_cyrillic_agreement",
                "exact_match,extract_answer": 0.9,
                "exact_match_stderr,extract_answer": 0.02,
                "pair_agreement,none": 0.8,
            },
        },
        "config": {"model": "anthropic-chat", "model_args": model_args},
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_collect_results_parses_model_and_metrics(tmp_path: Path) -> None:
    write_results(tmp_path / "haiku-4-5" / "results_2026-06-14T12-00-00.json")
    runs, warnings = collect_results(str(tmp_path))
    assert warnings == []
    assert len(runs) == 2  # one row per task
    grammar = next(r for r in runs if r.task == "srb_grammar")
    assert grammar.model == "claude-haiku-4-5"
    assert grammar.metrics["exact_match"] == (0.84, 0.031)
    cyr = next(r for r in runs if r.task == "srb_cyrillic_agreement")
    assert cyr.metrics["pair_agreement"] == (0.8, None)


def test_collect_results_takes_newest_file_per_dir(tmp_path: Path) -> None:
    write_results(tmp_path / "haiku-4-5" / "results_2026-06-14T12-00-00.json", value=0.1)
    write_results(tmp_path / "haiku-4-5" / "results_2026-06-15T09-00-00.json", value=0.9)
    runs, _ = collect_results(str(tmp_path))
    grammar = next(r for r in runs if r.task == "srb_grammar")
    assert grammar.metrics["exact_match"][0] == 0.9


def test_collect_results_model_args_as_dict(tmp_path: Path) -> None:
    write_results(
        tmp_path / "x" / "results_2026-06-14T12-00-00.json",
        model_args={"model": "claude-opus-4-8"},
    )
    runs, _ = collect_results(str(tmp_path))
    assert runs[0].model == "claude-opus-4-8"


def test_collect_results_empty(tmp_path: Path) -> None:
    assert collect_results(str(tmp_path)) == ([], [])


def test_format_markdown_table(tmp_path: Path) -> None:
    write_results(tmp_path / "haiku-4-5" / "results_2026-06-14T12-00-00.json")
    text = format_markdown(collect_results(str(tmp_path))[0])
    assert "| Model | Task |" in text
    assert "claude-haiku-4-5" in text
    assert "0.840 ±0.031" in text
    assert "pair_agreement" in text


def test_format_markdown_empty() -> None:
    assert "No results" in format_markdown([])


def test_collect_results_finds_lm_eval_nested_layout(tmp_path: Path) -> None:
    # lm-eval appends a model_name_sanitized dir below --output_path
    write_results(
        tmp_path / "haiku-4-5" / "claude-haiku-4-5" / "results_2026-08-06T12-00-00.json"
    )
    runs, warnings = collect_results(str(tmp_path))
    assert warnings == []
    assert {r.task for r in runs} == {"srb_grammar", "srb_cyrillic_agreement"}
    assert all(r.model == "claude-haiku-4-5" for r in runs)


def test_collect_results_skips_corrupt_file_with_warning(tmp_path: Path) -> None:
    write_results(tmp_path / "good" / "results_2026-08-06T12-00-00.json")
    bad = tmp_path / "bad"
    bad.mkdir()
    (bad / "results_2026-08-06T12-00-00.json").write_text("{truncated", encoding="utf-8")
    runs, warnings = collect_results(str(tmp_path))
    assert len(runs) == 2  # the good dir still parses
    assert len(warnings) == 1
    assert "skipped" in warnings[0]


def test_model_name_never_uses_adapter_string(tmp_path: Path) -> None:
    write_results(tmp_path / "smoke" / "results_2026-08-06T12-00-00.json", model_args="")
    runs, _ = collect_results(str(tmp_path))
    # config model is "anthropic-chat" (an adapter, not a model) -> dir fallback
    assert runs[0].model == "smoke"
