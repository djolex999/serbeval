"""Scoring for fill-in-the-blank grammar items.

An MCQ hands the model four options and a 25% floor; a cloze item makes it produce the
form. That removes distractor quality as a variable entirely — there is nothing to
eliminate and no structural giveaway — at the cost of having to decide what counts as
the same answer. This module is that decision, and it is deliberately strict:

Serbian diacritics are NEVER folded. `č`/`ć`, `ž`, `š`, `đ` carry the orthography the
benchmark is testing, so "kuca" is not "kuća" and "basti" is not "bašti". Case, surrounding
punctuation and whitespace are normalized away, and so is script: a form written in
Cyrillic is compared after transliteration, since this task measures morphology and
script consistency has its own task.
"""

import re
import unicodedata
from collections.abc import Sequence

from serbeval.schema import ClozeItem
from serbeval.translit import cyrillic_to_latin

# Models comply with "answer with the form only" to varying degrees; these prefixes are
# framing, not answer content.
_PREFIXES = re.compile(
    r"^\s*(odgovor|rešenje|resenje|answer|tačan oblik|oblik)\s*[:\-—]\s*",
    re.IGNORECASE,
)
# Stripped from both ends only, so an internal hyphen or apostrophe survives.
_WRAPPERS = "\"'`„“”‘’«»()[]{}*_ \t.,;:!?"


# A hyphen between two letters is orthography (kontakt-osoba, crveno-beli), not
# punctuation: folding it to a space would accept the rastavljeno spelling as correct.
_INTRA_WORD_HYPHEN = re.compile(r"(?<=\w)-(?=\w)")
_KEPT_HYPHEN = "\x00"


def normalize(text: str) -> str:
    """Casefold and strip punctuation/whitespace, leaving diacritics and intra-word hyphens."""
    protected = _INTRA_WORD_HYPHEN.sub(_KEPT_HYPHEN, text)
    stripped = "".join(
        " " if unicodedata.category(ch).startswith("P") else ch for ch in protected
    )
    return " ".join(stripped.lower().split()).replace(_KEPT_HYPHEN, "-")


# An answer is a word form or a short phrase ("lošem vremenu", "budeš stigao").
_MAX_ANSWER_WORDS = 3


def _clean(line: str) -> str:
    return _PREFIXES.sub("", line.strip()).strip(_WRAPPERS)


def extract_answer(raw: str) -> str:
    """Pull the produced form out of a model response.

    Returns the first non-empty line that is short enough to be an answer, after
    removing an "Odgovor:"-style prefix and wrapping quotes or brackets. That covers
    both orders models use: "bašti⏎⏎Objašnjenje: …" (answer first) and
    '"kroz" + accusative plural: sela.⏎⏎sela' (reasoning first, which Opus produced
    twice through Kie and was scored wrong while answering correctly). If no line is
    short enough, the first non-empty line is returned.
    """
    lines = [cleaned for line in (raw or "").splitlines() if (cleaned := _clean(line))]
    if not lines:
        return ""
    for line in lines:
        if len(line.split()) <= _MAX_ANSWER_WORDS:
            return line
    return lines[0]


def _comparable(text: str) -> str:
    # Script is folded, diacritics are not: „рата“ and „rata“ are the same form, but
    # „башти“ becomes „bašti“, never „basti“. Grammar is what this task measures;
    # script consistency has its own task (srb_cyrillic_agreement).
    return normalize(cyrillic_to_latin(text))


def matches_any(raw: str, answers: Sequence[str]) -> bool:
    """True when the response matches any accepted form, in either script."""
    produced = _comparable(extract_answer(raw))
    if not produced:
        return False
    return any(produced == _comparable(answer) for answer in answers)


def is_correct(raw: str, item: ClozeItem) -> bool:
    return matches_any(raw, item.answers)
