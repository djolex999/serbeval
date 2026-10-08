import json
from pathlib import Path

import pytest

from serbeval.report import (
    Stat,
    collect_results,
    format_analysis,
    format_markdown,
    load_run,
    load_runs,
    rankable,
    rescore_table,
    stat_by,
    task_stat,
    wilson_interval,
)

# --- aggregate results table ----------------------------------------------


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


# --- per-sample statistics -------------------------------------------------


def write_run(
    root: Path,
    name: str,
    *,
    samples: dict[str, list[tuple[dict[str, object], float]]],
    pair_agreement: dict[str, float] | None = None,
) -> Path:
    """Build a directory in lm-eval's real on-disk layout (nested run subdir included)."""
    run_dir = root / name / "abc12345"
    run_dir.mkdir(parents=True)
    results: dict[str, dict[str, object]] = {}
    for task, rows in samples.items():
        results[task] = {
            "alias": task,
            "sample_len": len(rows),
            "exact_match,extract_answer": (
                sum(c for _, c in rows) / len(rows) if rows else 0.0
            ),
        }
        if pair_agreement and task in pair_agreement:
            results[task]["pair_agreement,extract_answer"] = pair_agreement[task]
        with open(run_dir / f"samples_{task}_2026-09-02T00-00-00.jsonl", "w") as fh:
            for doc_id, (doc, correct) in enumerate(rows):
                fh.write(
                    json.dumps(
                        {"doc_id": doc_id, "doc": doc, "exact_match": correct},
                        ensure_ascii=False,
                    )
                    + "\n"
                )
    with open(run_dir / "results_2026-09-02T00-00-00.json", "w") as fh:
        json.dump({"results": results}, fh)
    return root / name


def doc(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": "x",
        "task": "srb_grammar",
        "category": "padezi",
        "script": "latin",
        "difficulty": None,
    }
    base.update(overrides)
    return base


# --- Wilson score interval -------------------------------------------------


def test_wilson_matches_known_value_for_half_of_one_hundred() -> None:
    low, high = wilson_interval(50, 100)
    assert low == pytest.approx(0.4038, abs=0.001)
    assert high == pytest.approx(0.5962, abs=0.001)


def test_wilson_lower_bound_is_zero_when_nothing_correct() -> None:
    low, high = wilson_interval(0, 10)
    assert low == 0.0
    assert high == pytest.approx(0.2775, abs=0.001)


def test_wilson_upper_bound_is_one_when_all_correct() -> None:
    low, high = wilson_interval(10, 10)
    assert low == pytest.approx(0.7225, abs=0.001)
    assert high == 1.0


def test_wilson_of_empty_sample_spans_the_whole_range() -> None:
    assert wilson_interval(0, 0) == (0.0, 1.0)


def test_wilson_interval_narrows_as_sample_grows() -> None:
    small_low, small_high = wilson_interval(25, 50)
    large_low, large_high = wilson_interval(250, 500)
    assert (large_high - large_low) < (small_high - small_low)


# --- loading runs ----------------------------------------------------------


def test_load_run_reads_samples_and_names_run_after_its_directory(tmp_path: Path) -> None:
    path = write_run(
        tmp_path,
        "haiku-4-5",
        samples={"srb_grammar": [(doc(), 1.0), (doc(), 0.0)]},
    )
    run = load_run(path)
    assert run.name == "haiku-4-5"
    assert len(run.samples["srb_grammar"]) == 2


def test_load_run_reads_pair_agreement_from_results_json(tmp_path: Path) -> None:
    path = write_run(
        tmp_path,
        "haiku-4-5",
        samples={"srb_cyrillic_agreement": [(doc(task="srb_cyrillic_agreement"), 1.0)]},
        pair_agreement={"srb_cyrillic_agreement": 0.8},
    )
    assert load_run(path).pair_agreement["srb_cyrillic_agreement"] == 0.8


def test_load_run_rejects_a_directory_with_no_results_file(tmp_path: Path) -> None:
    empty = tmp_path / "nothing"
    empty.mkdir()
    with pytest.raises(ValueError, match="no lm-eval results"):
        load_run(empty)


# --- statistics ------------------------------------------------------------


def test_task_stat_counts_correct_answers(tmp_path: Path) -> None:
    path = write_run(
        tmp_path,
        "m",
        samples={"srb_grammar": [(doc(), 1.0), (doc(), 1.0), (doc(), 0.0), (doc(), 0.0)]},
    )
    stat = task_stat(load_run(path), "srb_grammar")
    assert (stat.correct, stat.n) == (2, 4)
    assert stat.accuracy == 0.5


def test_stat_by_script_splits_the_two_scripts(tmp_path: Path) -> None:
    path = write_run(
        tmp_path,
        "m",
        samples={
            "srb_cyrillic_agreement": [
                (doc(script="latin"), 1.0),
                (doc(script="latin"), 1.0),
                (doc(script="cyrillic"), 1.0),
                (doc(script="cyrillic"), 0.0),
            ]
        },
    )
    by_script = stat_by(load_run(path), "srb_cyrillic_agreement", "script")
    assert by_script["latin"].accuracy == 1.0
    assert by_script["cyrillic"].accuracy == 0.5


def test_stat_by_difficulty_ignores_items_without_a_tier(tmp_path: Path) -> None:
    path = write_run(
        tmp_path,
        "m",
        samples={
            "srb_cyrillic_agreement": [
                (doc(difficulty="easy"), 1.0),
                (doc(difficulty="hard"), 0.0),
                (doc(difficulty=None), 1.0),
            ]
        },
    )
    by_tier = stat_by(load_run(path), "srb_cyrillic_agreement", "difficulty")
    assert set(by_tier) == {"easy", "hard"}


# --- rankability -----------------------------------------------------------


def test_models_with_overlapping_intervals_are_not_rankable() -> None:
    a = Stat(correct=36, n=50, accuracy=0.72, ci_low=0.58, ci_high=0.83)
    b = Stat(correct=43, n=50, accuracy=0.86, ci_low=0.74, ci_high=0.93)
    assert rankable(a, b) is False


def test_models_with_disjoint_intervals_are_rankable() -> None:
    a = Stat(correct=150, n=500, accuracy=0.30, ci_low=0.26, ci_high=0.34)
    b = Stat(correct=400, n=500, accuracy=0.80, ci_low=0.76, ci_high=0.83)
    assert rankable(a, b) is True


# --- formatting ------------------------------------------------------------


def test_report_states_when_item_count_cannot_rank_the_models(tmp_path: Path) -> None:
    rows_a = [(doc(), 1.0)] * 36 + [(doc(), 0.0)] * 14
    rows_b = [(doc(), 1.0)] * 43 + [(doc(), 0.0)] * 7
    runs = [
        load_run(write_run(tmp_path, "haiku", samples={"srb_grammar": rows_a})),
        load_run(write_run(tmp_path, "opus", samples={"srb_grammar": rows_b})),
    ]
    out = format_analysis(runs)
    assert "cannot rank" in out


def test_report_warns_about_categories_too_small_to_estimate(tmp_path: Path) -> None:
    rows = [(doc(category="glagolski-vid"), 1.0)] * 4 + [(doc(category="padezi"), 1.0)] * 40
    runs = [load_run(write_run(tmp_path, "haiku", samples={"srb_grammar": rows}))]
    out = format_analysis(runs)
    assert "glagolski-vid" in out
    assert "no usable estimate" in out


def test_report_shows_the_script_gap_for_the_paired_task(tmp_path: Path) -> None:
    rows = [(doc(task="srb_cyrillic_agreement", script="latin"), 1.0)] * 10 + [
        (doc(task="srb_cyrillic_agreement", script="cyrillic"), 0.0)
    ] * 10
    runs = [
        load_run(
            write_run(
                tmp_path,
                "haiku",
                samples={"srb_cyrillic_agreement": rows},
                pair_agreement={"srb_cyrillic_agreement": 0.0},
            )
        )
    ]
    out = format_analysis(runs)
    assert "script gap" in out
    assert "pair_agreement" in out


def test_load_runs_scans_a_results_root_and_uses_config_model_names(tmp_path: Path) -> None:
    # The aggregate table and the per-sample analysis must agree on what a model is called,
    # so load_runs names runs the same way collect_results does: from lm-eval config, with
    # the directory as fallback. load_run (singular) keeps naming by directory.
    run_dir = tmp_path / "smoke" / "claude-haiku-4-5"
    run_dir.mkdir(parents=True)
    (run_dir / "results_2026-09-02T00-00-00.json").write_text(
        json.dumps(
            {
                "results": {"srb_grammar": {"exact_match,extract_answer": 0.5}},
                "config": {"model": "anthropic-chat", "model_args": "model=claude-haiku-4-5"},
            }
        ),
        encoding="utf-8",
    )
    with open(run_dir / "samples_srb_grammar_2026-09-02T00-00-00.jsonl", "w") as fh:
        fh.write(json.dumps({"doc_id": 0, "doc": doc(), "exact_match": 1.0}) + "\n")

    runs = load_runs(str(tmp_path))
    assert [r.name for r in runs] == ["claude-haiku-4-5"]
    assert len(runs[0].samples["srb_grammar"]) == 1


def test_load_runs_ignores_runs_without_logged_samples(tmp_path: Path) -> None:
    # --log_samples is optional; a run without it still belongs in the markdown table
    # but has nothing for the statistics to work with.
    run_dir = tmp_path / "nosamples" / "x"
    run_dir.mkdir(parents=True)
    (run_dir / "results_2026-09-02T00-00-00.json").write_text(
        json.dumps({"results": {"srb_grammar": {"exact_match,extract_answer": 0.5}}, "config": {}}),
        encoding="utf-8",
    )
    assert load_runs(str(tmp_path)) == []


def test_load_runs_on_a_missing_directory_is_empty(tmp_path: Path) -> None:
    assert load_runs(str(tmp_path / "nope")) == []


# --- re-scoring with the current rules -------------------------------------

CLOZE_DOC: dict[str, object] = {
    "id": "c1",
    "task": "srb_grammar_cloze",
    "category": "padezi",
    "question": "Otkazali su izlet zbog ____.",
    "cue": "nevreme, jednina",
    "answers": ["nevremena"],
    "script": "latin",
    "difficulty": "medium",
}


def write_raw_run(root: Path, task: str, rows: list[tuple[dict[str, object], str, float]]) -> Path:
    """A run whose per-sample rows carry the raw response, as lm-eval writes them."""
    run_dir = root / "opus" / "claude-opus-5-5"
    run_dir.mkdir(parents=True)
    recorded = sum(c for _, _, c in rows) / len(rows)
    (run_dir / "results_2026-10-07T00-00-00.json").write_text(
        json.dumps(
            {
                "results": {task: {"exact_match,none": recorded, "exact_match_stderr,none": 0.05}},
                "config": {"model_args": "model=claude-opus-5-5"},
            }
        ),
        encoding="utf-8",
    )
    with open(run_dir / f"samples_{task}_2026-10-07T00-00-00.jsonl", "w", encoding="utf-8") as fh:
        for i, (item, response, correct) in enumerate(rows):
            row = {"doc_id": i, "doc": item, "resps": [[response]], "exact_match": correct}
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return root


def test_cloze_samples_are_rescored_with_the_current_rules(tmp_path: Path) -> None:
    # Recorded 0.0 under an older rule that did not fold script; today the Cyrillic
    # form of the right answer counts. report must agree with triage on this.
    write_raw_run(tmp_path, "srb_grammar_cloze", [(CLOZE_DOC, "невремена", 0.0)])
    (run,) = load_runs(str(tmp_path))
    assert task_stat(run, "srb_grammar_cloze").correct == 1


def test_a_wrong_cloze_answer_stays_wrong_after_rescoring(tmp_path: Path) -> None:
    write_raw_run(tmp_path, "srb_grammar_cloze", [(CLOZE_DOC, "nevremenu", 1.0)])
    (run,) = load_runs(str(tmp_path))
    assert task_stat(run, "srb_grammar_cloze").correct == 0


def test_mcq_samples_keep_their_recorded_verdict(tmp_path: Path) -> None:
    write_raw_run(tmp_path, "srb_grammar", [(doc(answer_index=1), "B", 1.0)])
    (run,) = load_runs(str(tmp_path))
    assert task_stat(run, "srb_grammar").correct == 1


def test_table_exact_match_follows_the_rescored_samples(tmp_path: Path) -> None:
    write_raw_run(
        tmp_path,
        "srb_grammar_cloze",
        [(CLOZE_DOC, "невремена", 0.0), ({**CLOZE_DOC, "id": "c2"}, "nevremena", 1.0)],
    )
    runs, _ = collect_results(str(tmp_path))
    rescored, notes = rescore_table(runs, load_runs(str(tmp_path)))
    (cloze,) = rescored
    value, stderr = cloze.metrics["exact_match"]
    assert value == 1.0
    assert stderr == 0.0
    assert notes == ["claude-opus-5-5 / srb_grammar_cloze: exact_match 0.500 -> 1.000"]


def test_table_is_untouched_when_rescoring_changes_nothing(tmp_path: Path) -> None:
    write_raw_run(tmp_path, "srb_grammar_cloze", [(CLOZE_DOC, "nevremena", 1.0)])
    runs, _ = collect_results(str(tmp_path))
    rescored, notes = rescore_table(runs, load_runs(str(tmp_path)))
    assert rescored[0].metrics["exact_match"] == (1.0, 0.05)
    assert notes == []
