import json
from pathlib import Path

from serbeval.triage import collect_misses, format_misses

MCQ = {
    "id": "g1", "task": "srb_grammar", "category": "padezi", "question": "Koja je ispravna?",
    "choices": ["a", "b", "c", "d"], "answer_index": 1,
}
CLOZE = {
    "id": "c1", "task": "srb_grammar_cloze", "category": "padezi",
    "question": "Otkazali su izlet zbog ____.", "cue": "nevreme, jednina",
    "answers": ["nevremena"],
}


def write_model_run(root: Path, model: str, rows: dict[str, list[tuple[dict, str, float]]]) -> None:
    """lm-eval's real layout: <root>/<model>/results_*.json + samples_<task>_*.jsonl."""
    run = root / model
    run.mkdir(parents=True)
    (run / "results_2026-10-07T00-00-00.json").write_text(
        json.dumps({"results": {}, "config": {"model_args": {"model": model}}}), encoding="utf-8"
    )
    for task, samples in rows.items():
        with open(run / f"samples_{task}_2026-10-07T00-00-00.jsonl", "w", encoding="utf-8") as fh:
            for i, (doc, response, correct) in enumerate(samples):
                fh.write(json.dumps({"doc_id": i, "doc": doc, "resps": [[response]],
                                     "exact_match": correct}, ensure_ascii=False) + "\n")


def test_lists_only_items_some_model_missed(tmp_path: Path) -> None:
    write_model_run(tmp_path, "opus", {"srb_grammar": [(MCQ, "B", 1.0)],
                                       "srb_grammar_cloze": [(CLOZE, "nevremenu", 0.0)]})
    misses = collect_misses(str(tmp_path))
    assert [m.item_id for m in misses] == ["c1"]


def test_items_every_model_missed_come_first(tmp_path: Path) -> None:
    # Missed by every model is the strongest hint the ITEM is wrong, not the models.
    other = {**MCQ, "id": "g2"}
    write_model_run(tmp_path, "opus", {"srb_grammar": [(MCQ, "C", 0.0), (other, "B", 1.0)]})
    write_model_run(tmp_path, "gpt", {"srb_grammar": [(MCQ, "C", 0.0), (other, "A", 0.0)]})
    misses = collect_misses(str(tmp_path))
    assert [(m.item_id, m.missed_by, m.models) for m in misses] == [
        ("g1", 2, 2),
        ("g2", 1, 2),
    ]


def test_shows_gold_and_each_models_answer(tmp_path: Path) -> None:
    write_model_run(tmp_path, "opus", {"srb_grammar_cloze": [(CLOZE, "nevremenu", 0.0)]})
    write_model_run(tmp_path, "gpt", {"srb_grammar_cloze": [(CLOZE, "nevremena", 1.0)]})
    miss = collect_misses(str(tmp_path))[0]
    assert miss.gold == "nevremena"
    assert miss.answers == {"gpt": "nevremena", "opus": "nevremenu"}


def test_mcq_gold_is_the_letter(tmp_path: Path) -> None:
    write_model_run(tmp_path, "opus", {"srb_grammar": [(MCQ, "C", 0.0)]})
    assert collect_misses(str(tmp_path))[0].gold == "B"


def test_report_flags_unanimous_misses_as_suspect_items(tmp_path: Path) -> None:
    write_model_run(tmp_path, "opus", {"srb_grammar": [(MCQ, "C", 0.0)]})
    write_model_run(tmp_path, "gpt", {"srb_grammar": [(MCQ, "C", 0.0)]})
    out = format_misses(collect_misses(str(tmp_path)))
    assert "g1" in out
    assert "missed by 2/2" in out
    assert "gold: B" in out


def test_report_on_a_clean_run_says_so(tmp_path: Path) -> None:
    write_model_run(tmp_path, "opus", {"srb_grammar": [(MCQ, "B", 1.0)]})
    assert "No misses" in format_misses(collect_misses(str(tmp_path)))


def test_cloze_answers_are_rescored_with_the_current_rules(tmp_path: Path) -> None:
    # A run records exact_match under the scoring rules of its day. When a scoring bug
    # is fixed (e.g. Cyrillic answers to Latin items), triage must not keep flagging
    # items as missed on stale verdicts — or keep charging for re-runs to clear them.
    write_model_run(tmp_path, "opus", {"srb_grammar_cloze": [(CLOZE, "невремена", 0.0)]})
    assert collect_misses(str(tmp_path)) == []


def test_a_genuinely_wrong_cloze_answer_is_still_a_miss(tmp_path: Path) -> None:
    write_model_run(tmp_path, "opus", {"srb_grammar_cloze": [(CLOZE, "nevremenu", 0.0)]})
    assert [m.item_id for m in collect_misses(str(tmp_path))] == ["c1"]
