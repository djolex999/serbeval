"""Cue-free error correction: find and fix the one error in a sentence, if there is one.

The cloze sets name the word under test in brackets („spomen + ploča“, „ruka, jednina“),
and that cue does most of the work: Opus 5.5 is at ceiling on every cued phenomenon
tried, pravopis included. Here the model sees only a sentence. It must notice whether
anything is wrong, find where, and fix just that — and leave clean sentences alone.

Items are DERIVED, not written: the sentence and its correct form come from existing,
source-checked cloze items, and the error is made mechanically from them —

    razmak-crtica  the spelling of the gold form is changed between together / apart /
                   hyphen, using the cue's parts to find the boundary (kontakt-telefon ->
                   kontakt telefon, jugoistočnom -> jugo-istočnom, ni od koga -> niodkoga)
    c-ć            one č/ć in one word is swapped, and only where the result is NOT a
                   known form, so the "error" can never be a different real word

Scoring compares the whole sentence with the same folding as cloze (case, surrounding
punctuation, script) — diacritics and intra-word hyphens stay significant.
"""

import random
import re
from collections.abc import Collection, Sequence
from typing import NamedTuple

from serbeval.cloze import _comparable
from serbeval.schema import BLANK, ClozeItem, CorrectionItem

_MARKER = re.compile(r"ispravljeno\s*:\s*", re.IGNORECASE)
_WRAPPERS = "\"'`„“”‘’«»*_ \t"
_WORD = re.compile(r"\w+")
_SWAP = {"č": "ć", "ć": "č", "Č": "Ć", "Ć": "Č"}
# A cue part shorter than this is searched for whole; longer ones by their first letters,
# because the gold is inflected (jug + istočni -> jugoistočnom).
_STEM = 3


class Sentence(NamedTuple):
    """A known-correct sentence for c-ć errors and clean items, with its provenance."""

    text: str
    source: str
    license: str


def fill(item: ClozeItem, form: str) -> str:
    if item.question.startswith(BLANK):
        form = form[:1].upper() + form[1:]
    return item.question.replace(BLANK, form, 1)


def _boundaries(gold: str, parts: list[str]) -> list[int] | None:
    """Where each cue part after the first begins inside the gold form."""
    lowered = gold.lower()
    positions = []
    # Skip most of the first part: its own letters can contain the next stem („pol“ in
    # „spoljni“). Not all of it — the gold may shorten it (latinski -> latino-).
    start = max(1, len(parts[0]) - _STEM)
    for part in parts[1:]:
        stem = part.lower()[:_STEM]
        at = lowered.find(stem, start)
        if at < 0:
            return None
        positions.append(at)
        start = at + 1
    return positions


def spacing_error(item: ClozeItem) -> str | None:
    """The gold form misspelt as the realistic together/apart/hyphen alternative."""
    if " + " not in item.cue:
        return None
    parts = [part.strip() for part in item.cue.split("+")]
    gold = item.answers[0]

    if "-" in gold:
        # Coordinate adjectives get written together (srpskoengleski); noun
        # polusloženice get written apart (kontakt telefon).
        wrong = gold.replace("-", "" if item.category == "slozeni-pridevi" else " ")
    elif " " in gold:
        wrong = gold.replace(" ", "")
    else:
        cuts = _boundaries(gold, parts)
        if cuts is None:
            return None
        sep = " " if item.category == "sastavljeno-rastavljeno" else "-"
        pieces, prev = [], 0
        for cut in cuts:
            pieces.append(gold[prev:cut])
            prev = cut
        pieces.append(gold[prev:])
        wrong = sep.join(pieces)

    if any(_comparable(wrong) == _comparable(answer) for answer in item.answers):
        return None
    return wrong


def diacritic_error(
    sentence: str, known: Collection[str], rng: random.Random
) -> tuple[str, str, str] | None:
    """Swap one č/ć so the word becomes a NON-word: (wrong sentence, original, swapped)."""
    options = []
    for match in _WORD.finditer(sentence):
        word = match.group()
        for i, ch in enumerate(word):
            if ch in _SWAP:
                swapped = word[:i] + _SWAP[ch] + word[i + 1 :]
                if swapped.lower() not in known:
                    options.append((match.start(), match.end(), word, swapped))
    if not options:
        return None
    start, end, word, swapped = rng.choice(options)
    return sentence[:start] + swapped + sentence[end:], word, swapped


def extract_correction(raw: str) -> str:
    """The sentence after the last „Ispravljeno:“, else the first non-empty line."""
    text = raw or ""
    markers = list(_MARKER.finditer(text))
    if markers:
        rest = text[markers[-1].end() :].strip().splitlines()
        return rest[0].strip(_WRAPPERS) if rest else ""
    for line in text.splitlines():
        if line.strip():
            return line.strip().strip(_WRAPPERS)
    return ""


def is_correct(raw: str, item: CorrectionItem) -> bool:
    produced = _comparable(extract_correction(raw))
    if not produced:
        return False
    return any(produced == _comparable(answer) for answer in item.answers)


TASK = "srb_correction"
CATEGORIES = ("razmak-crtica", "c-ć", "ispravno")
SLUGS = {"razmak-crtica": "razmak-crtica", "c-ć": "c-c", "ispravno": "ispravno"}
_CLEAN = "Rečenica je ispravna; ništa ne treba menjati."


def _derived(
    category: str, index: int, text: str, answers: list[str], has_error: bool,
    explanation: str, source: ClozeItem | Sentence,
) -> CorrectionItem:
    source_id = source.id if isinstance(source, ClozeItem) else source.source
    return CorrectionItem(
        id=f"srb-correction-{SLUGS[category]}-{index:04d}",
        task=TASK,
        category=category,
        text=text,
        answers=answers,
        has_error=has_error,
        explanation=explanation,
        script="latin",
        difficulty="hard",
        source=f"derived:{source_id}",
        license=source.license,
    )


def build_correction_set(
    pravopis: list[ClozeItem],
    pool: Sequence[Sentence],
    *,
    known: Collection[str],
    per_category: int,
    seed: int = 0,
) -> list[CorrectionItem]:
    """`per_category` spacing errors, č/ć errors and clean sentences, no sentence reused.

    Spacing errors and half the clean sentences come from `pravopis`, so the clean half
    contains exactly the tricky spellings the error items test, spelt right — that is
    what catches over-correction. č/ć errors and the other clean half come from `pool`.
    """
    rng = random.Random(seed)
    used: set[str] = set()

    eligible = [(item, wrong) for item in pravopis if (wrong := spacing_error(item))]
    rng.shuffle(eligible)
    spacing: list[CorrectionItem] = []
    for item, wrong in eligible[:per_category]:
        right = fill(item, item.answers[0])
        used.add(right)
        spacing.append(_derived(
            "razmak-crtica", len(spacing) + 1, fill(item, wrong),
            [fill(item, answer) for answer in item.answers], True,
            f"Treba „{item.answers[0]}“, a ne „{wrong}“. {item.explanation}", item,
        ))

    clean: list[CorrectionItem] = []
    for item, _ in eligible[per_category : per_category + per_category // 2]:
        text = fill(item, item.answers[0])
        used.add(text)
        clean.append(_derived("ispravno", len(clean) + 1, text, [text], False, _CLEAN, item))

    shuffled = list(pool)
    rng.shuffle(shuffled)
    diacritics: list[CorrectionItem] = []
    rest: list[Sentence] = []
    # One word, one item: otherwise a frame like „... već deset godina“ repeated across
    # lemmas turns the category into twelve copies of the same „več“.
    swapped_words: set[str] = set()
    for sentence in shuffled:
        if sentence.text in used:
            continue
        used.add(sentence.text)
        made = None
        if len(diacritics) < per_category:
            made = diacritic_error(sentence.text, known, rng)
            if made is not None and made[1].lower() in swapped_words:
                made = None
        if made is None:
            rest.append(sentence)
            continue
        wrong, original, swapped = made
        swapped_words.add(original.lower())
        diacritics.append(_derived(
            "c-ć", len(diacritics) + 1, wrong, [sentence.text], True,
            f"Treba „{original}“, a ne „{swapped}“ (č/ć).", sentence,
        ))

    for sentence in rest[: per_category - len(clean)]:
        clean.append(_derived(
            "ispravno", len(clean) + 1, sentence.text, [sentence.text], False, _CLEAN, sentence,
        ))

    counts = {"razmak-crtica": len(spacing), "c-ć": len(diacritics), "ispravno": len(clean)}
    if any(count < per_category for count in counts.values()):
        raise ValueError(f"not enough source items for {per_category} per category: {counts}")
    return spacing + diacritics + clean
