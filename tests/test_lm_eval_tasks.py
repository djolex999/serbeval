"""Integration tests: lm-eval (pinned 0.4.12) must load our task configs and build prompts.

These run against the real seed data under data/, from the repo root.
"""

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
