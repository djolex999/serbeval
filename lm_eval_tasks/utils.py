"""Helper functions referenced by the task YAMLs via lm-eval's ``!function`` directive.

Every serbeval task is a 4-way MCQ scored as ``generate_until``: we render an A/B/C/D prompt,
ask for a single letter, and regex-extract it. The cyrillic-agreement task additionally reports
a per-pair answer-agreement metric (see ``process_results_pair`` / ``pair_agreement``).
"""

from collections.abc import Sequence

LETTERS = ("A", "B", "C", "D")


def doc_to_text(doc: dict) -> str:
    lines = [doc["question"], ""]
    for letter, choice in zip(LETTERS, doc["choices"]):
        lines.append(f"{letter}) {choice}")
    lines.append("")
    lines.append("Odgovori samo slovom tačnog odgovora (A, B, C ili D).")
    lines.append("Odgovor:")
    return "\n".join(lines)


def doc_to_target(doc: dict) -> str:
    return LETTERS[doc["answer_index"]]


def _extracted_correct(doc: dict, results: list[str]) -> float:
    pred = (results[0] or "").strip().upper()[:1]
    return 1.0 if pred == LETTERS[doc["answer_index"]] else 0.0


def process_results_pair(doc: dict, results: list[str]) -> dict:
    """Emit both standard accuracy and a (pair_id, correct) tuple for pair aggregation."""
    correct = _extracted_correct(doc, results)
    return {
        "exact_match": correct,
        "pair_agreement": (doc["pair_id"], correct),
    }


def pair_agreement(items: Sequence[tuple[str, float]]) -> float:
    """Fraction of pairs whose two scripts produced the SAME correctness outcome.

    A pair "agrees" when the model is right on both scripts or wrong on both — i.e. the
    answer is script-invariant. Mixed outcomes count as disagreement.
    """
    by_pair: dict[str, list[float]] = {}
    for pair_id, correct in items:
        by_pair.setdefault(pair_id, []).append(correct)
    complete = [vals for vals in by_pair.values() if len(vals) == 2]
    if not complete:
        return 0.0
    agreed = sum(1 for vals in complete if vals[0] == vals[1])
    return agreed / len(complete)
