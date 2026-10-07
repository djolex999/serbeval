"""Integration tests: lm-eval (pinned 0.4.12) must load our task configs and build prompts.

These run against the real seed data under data/, from the repo root.
"""

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TASKS_DIR = REPO_ROOT / "lm_eval_tasks"

sys.path.insert(0, str(TASKS_DIR))
import utils  # noqa: E402


def test_doc_to_text_builds_labeled_prompt() -> None:
    doc = {
        "question": "Dopuni rečenicu: Pišem ____.",
        "choices": ["olovkom", "sa olovkom", "olovka", "olovku"],
        "answer_index": 0,
    }
    text = utils.doc_to_text(doc)
    assert "Dopuni rečenicu: Pišem ____." in text
    assert "A) olovkom" in text
    assert "D) olovku" in text
    assert text.rstrip().endswith("Odgovor:")


def test_doc_to_target_returns_letter() -> None:
    assert utils.doc_to_target({"answer_index": 2}) == "C"


def test_process_results_pair_extracts_letter_without_filter() -> None:
    doc = {
        "question": "x",
        "choices": ["a", "b", "c", "d"],
        "answer_index": 1,
        "pair_id": "p1",
    }
    # Raw, unfiltered model output (filter pipeline may be bypassed for custom process_results)
    out = utils.process_results_pair(doc, ["Odgovor: B"])
    assert out["exact_match"] == 1.0
    assert out["pair_agreement"] == ("p1", 1.0)

    wrong = utils.process_results_pair(doc, ["A) nije tačno"])
    assert wrong["exact_match"] == 0.0
    assert wrong["pair_agreement"] == ("p1", 0.0)


def test_pair_agreement_aggregation() -> None:
    # (pair_id, correct) tuples from process_results
    results = [
        ("p1", 1.0),  # pair p1: both correct -> agree
        ("p1", 1.0),
        ("p2", 1.0),  # pair p2: split -> disagree
        ("p2", 0.0),
        ("p3", 0.0),  # pair p3: both wrong -> agree (consistent, even if wrong)
        ("p3", 0.0),
    ]
    assert utils.pair_agreement(results) == pytest.approx(2 / 3)


@pytest.mark.slow
def test_lm_eval_loads_all_tasks() -> None:
    from lm_eval.tasks import TaskManager

    tm = TaskManager(include_path=str(TASKS_DIR))
    for name in ("srb_grammar", "srb_idioms", "srb_cyrillic_agreement"):
        assert name in tm.all_tasks, f"{name} not registered"

    task = tm.load(["srb_grammar"])["tasks"]["srb_grammar"]
    docs = list(task.test_docs())
    assert len(docs) >= 40
    rendered = task.doc_to_text(docs[0])
    assert "A)" in rendered and "Odgovor:" in rendered
    assert task.doc_to_target(docs[0]) in {"A", "B", "C", "D"}


@pytest.mark.slow
def test_cloze_task_runs_through_the_harness(tmp_path: Path) -> None:
    """The cloze task is a real lm-eval task, not a bespoke script: prove it aggregates."""
    import subprocess
    import sys

    result = subprocess.run(
        [
            sys.executable, "-m", "lm_eval",
            "--model", "dummy",
            "--tasks", "srb_grammar_cloze",
            "--include_path", "lm_eval_tasks",
            "--output_path", str(tmp_path),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stderr
    written = list(Path(tmp_path).rglob("results_*.json"))
    assert written, "no results file written"
    payload = json.loads(written[0].read_text(encoding="utf-8"))
    assert "exact_match,none" in payload["results"]["srb_grammar_cloze"]


# --- unparsed responses ----------------------------------------------------
#
# A response we cannot read scored 0, exactly like a wrong answer. That makes a
# formatting or refusal problem look like a Serbian-competence problem, and there was
# no way to tell them apart from the results file.


def test_mcq_marks_a_correct_letter_as_parsed_and_right() -> None:
    doc = {"question": "q", "choices": ["a", "b", "c", "d"], "answer_index": 1}
    assert utils.process_results_mcq(doc, ["B"]) == {"exact_match": 1.0, "unparsed": 0.0}


def test_mcq_marks_a_wrong_letter_as_parsed_but_wrong() -> None:
    doc = {"question": "q", "choices": ["a", "b", "c", "d"], "answer_index": 1}
    assert utils.process_results_mcq(doc, ["C"]) == {"exact_match": 0.0, "unparsed": 0.0}


def test_mcq_marks_a_response_with_no_letter_as_unparsed() -> None:
    doc = {"question": "q", "choices": ["a", "b", "c", "d"], "answer_index": 1}
    assert utils.process_results_mcq(doc, ["Ne mogu da odgovorim."]) == {
        "exact_match": 0.0,
        "unparsed": 1.0,
    }


def test_mcq_marks_an_empty_response_as_unparsed() -> None:
    doc = {"question": "q", "choices": ["a", "b", "c", "d"], "answer_index": 1}
    assert utils.process_results_mcq(doc, [""])["unparsed"] == 1.0


def test_pair_task_also_reports_unparsed() -> None:
    doc = {
        "question": "q", "choices": ["a", "b", "c", "d"],
        "answer_index": 0, "pair_id": "p1",
    }
    result = utils.process_results_pair(doc, ["nema slova"])
    assert result["unparsed"] == 1.0
    assert result["exact_match"] == 0.0


def test_cloze_reports_unparsed_for_an_empty_response() -> None:
    doc = {
        "id": "c1", "task": "srb_grammar_cloze", "category": "padezi",
        "question": "Zbog ____.", "cue": "nevreme", "answers": ["nevremena"],
        "explanation": "e", "script": "latin", "source": "s",
    }
    assert utils.process_results_cloze(doc, ["   "]) == {
        "exact_match": 0.0,
        "unparsed": 1.0,
    }


def test_cloze_wrong_but_readable_answer_is_not_unparsed() -> None:
    doc = {
        "id": "c1", "task": "srb_grammar_cloze", "category": "padezi",
        "question": "Zbog ____.", "cue": "nevreme", "answers": ["nevremena"],
        "explanation": "e", "script": "latin", "source": "s",
    }
    assert utils.process_results_cloze(doc, ["nevremenu"]) == {
        "exact_match": 0.0,
        "unparsed": 0.0,
    }


PROBE_TASKS = {
    "srb_probe_jat": 20,
    "srb_probe_aorist_imperfekat": 20,
    "srb_probe_sibilarizacija": 20,
    "srb_probe_broj_pridev_imenica": 20,
    "srb_probe_sastavljeno_rastavljeno": 20,
    "srb_probe_poluslozenice": 20,
}


@pytest.mark.slow
def test_probe_tasks_load_one_per_phenomenon_with_twenty_items() -> None:
    # One task per phenomenon so the results table reads off per-phenomenon accuracy
    # directly: the probe's only question is which phenomena fall below ~90%.
    from lm_eval.tasks import TaskManager

    tm = TaskManager(include_path=str(TASKS_DIR))
    loaded = tm.load(list(PROBE_TASKS))["tasks"]
    for name, expected in PROBE_TASKS.items():
        docs = list(loaded[name].test_docs())
        assert len(docs) == expected, name
        assert {doc["task"] for doc in docs} == {"srb_probe"}
    assert "srb_probe" in tm.all_tags
