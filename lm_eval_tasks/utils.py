"""Helper functions referenced by the task YAMLs via lm-eval's ``!function`` directive.

Every serbeval task is a 4-way MCQ scored as ``generate_until``: we render an A/B/C/D prompt,
ask for a single letter, and regex-extract it. The cyrillic-agreement task additionally reports
a per-pair answer-agreement metric (see ``process_results_pair`` / ``pair_agreement``).
"""

import re
from collections.abc import Sequence

LETTERS = ("A", "B", "C", "D")

_ANSWER_RE = re.compile(r"\b([ABCD])\b")


def doc_to_text(doc: dict) -> str:
    lines = [doc["question"], ""]
    for letter, choice in zip(LETTERS, doc["choices"], strict=False):
        lines.append(f"{letter}) {choice}")
    lines.append("")
    lines.append("Odgovori samo slovom tačnog odgovora (A, B, C ili D).")
    lines.append("Odgovor:")
    return "\n".join(lines)


def doc_to_target(doc: dict) -> str:
    return LETTERS[doc["answer_index"]]


def _extract_letter(raw: str) -> str | None:
    match = _ANSWER_RE.search((raw or "").upper())
    return match.group(1) if match else None


def _extracted_correct(doc: dict, results: list[str]) -> float:
    # Self-contained extraction: correct whether or not the YAML filter pipeline ran first.
    pred = _extract_letter(results[0]) if results else None
    return 1.0 if pred == LETTERS[doc["answer_index"]] else 0.0


def _unparsed(results: list[str]) -> float:
    """1.0 when no answer letter could be read out of the response at all.

    Without this a refusal, a rambling answer, or a format the regex misses all score
    exactly like a wrong answer — so a prompting problem is indistinguishable from a
    Serbian-competence problem. Report it separately and the results file says which.
    """
    return 0.0 if results and _extract_letter(results[0]) is not None else 1.0


def process_results_mcq(doc: dict, results: list[str]) -> dict:
    return {
        "exact_match": _extracted_correct(doc, results),
        "unparsed": _unparsed(results),
    }


def process_results_pair(doc: dict, results: list[str]) -> dict:
    """Emit accuracy, an unparsed flag, and a (pair_id, correct) tuple for aggregation."""
    correct = _extracted_correct(doc, results)
    return {
        "exact_match": correct,
        "unparsed": _unparsed(results),
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


# --- srb_grammar_cloze -----------------------------------------------------
#
# Unlike the MCQ letter extraction above, cloze scoring is NOT duplicated here: it imports
# serbeval.cloze directly. Answer normalization is a correctness-critical judgement (which
# characters may be folded — never the Serbian diacritics), and two copies of that rule
# would drift silently and change scores. The package is always installed alongside these
# task files, so the import is safe.


def doc_to_text_cloze(doc: dict) -> str:
    return (
        "Dopuni rečenicu pravilnim oblikom reči u zagradi.\n\n"
        f"{doc['question']}  ({doc['cue']})\n\n"
        "Odgovori samo traženim oblikom reči, bez objašnjenja.\n"
        "Odgovor:"
    )


def doc_to_target_cloze(doc: dict) -> str:
    return doc["answers"][0]


def process_results_cloze(doc: dict, results: list[str]) -> dict:
    from serbeval.cloze import extract_answer, is_correct
    from serbeval.schema import ClozeItem

    item = ClozeItem.model_validate(doc)
    raw = results[0] if results else ""
    return {
        "exact_match": 1.0 if is_correct(raw, item) else 0.0,
        # An empty extraction is a response we could not read, not a wrong form.
        "unparsed": 0.0 if extract_answer(raw) else 1.0,
    }
