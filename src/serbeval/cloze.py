"""Scoring for fill-in-the-blank grammar items.

An MCQ hands the model four options and a 25% floor; a cloze item makes it produce the
form. That removes distractor quality as a variable entirely — there is nothing to
eliminate and no structural giveaway — at the cost of having to decide what counts as
the same answer. This module is that decision, and it is deliberately strict:

Serbian diacritics are NEVER folded. `č`/`ć`, `ž`, `š`, `đ` carry the orthography the
benchmark is testing, so "kuca" is not "kuća" and "basti" is not "bašti". Only case,
surrounding punctuation and whitespace are normalized away.
"""

import re
import unicodedata

from serbeval.schema import ClozeItem

# Models comply with "answer with the form only" to varying degrees; these prefixes are
# framing, not answer content.
_PREFIXES = re.compile(
    r"^\s*(odgovor|rešenje|resenje|answer|tačan oblik|oblik)\s*[:\-—]\s*",
    re.IGNORECASE,
)
# Stripped from both ends only, so an internal hyphen or apostrophe survives.
_WRAPPERS = "\"'`„“”‘’«»()[]{}*_ \t.,;:!?"


def normalize(text: str) -> str:
    """Casefold and strip punctuation/whitespace, leaving diacritics intact."""
    stripped = "".join(
        " " if unicodedata.category(ch).startswith("P") else ch for ch in text
    )
    return " ".join(stripped.lower().split())


def extract_answer(raw: str) -> str:
    """Pull the produced form out of a model response.

    Takes the first non-empty line — anything after it is commentary — then removes an
    "Odgovor:"-style prefix and any wrapping quotes or brackets. Multi-word answers are
    preserved, since case government on a phrase ("lošem vremenu") is a legitimate item.
    """
    if not raw:
        return ""
    for line in raw.splitlines():
        candidate = line.strip()
        if not candidate:
            continue
        candidate = _PREFIXES.sub("", candidate)
        candidate = candidate.strip(_WRAPPERS)
        if candidate:
            return candidate
    return ""


def is_correct(raw: str, item: ClozeItem) -> bool:
    """True when the response matches any accepted form after normalization."""
    produced = normalize(extract_answer(raw))
    if not produced:
        return False
    return any(produced == normalize(answer) for answer in item.answers)
