"""Reader for an inflectional lexicon in srLex's tab-separated format.

srLex (CLARIN.SI, CC BY-SA 4.0) lists every attested form of every lemma with its
morphological features and a corpus frequency. That gives a *paradigm* — the form for a
given case and number — which is what lets serbeval build cloze items whose gold answer
comes from a lexicon rather than from a tagger or a model.

One slot can hold more than one form: genitive plural of „bašta“ is attested as both
„bašta“ and „baštâ“. Every variant is returned, most frequent first, because a benchmark
that accepts only one of two correct forms marks a right answer wrong.

The file is ~7M rows, so `load_lexicon` takes a `lemmas` filter: callers know which handful
of lemmas they need and there is no reason to index the rest.

Columns: form, lemma, MSD, verbose features, UPOS, UD features, frequency, frequency/M.
"""

import gzip
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

_FORM, _LEMMA, _UPOS, _FEATS, _FREQ = 0, 1, 4, 5, 6
_MIN_COLUMNS = 7


@dataclass
class Lexicon:
    #  lemma -> (case, number) -> [(frequency, form), ...]
    paradigms: dict[str, dict[tuple[str, str], list[tuple[int, str]]]] = field(
        default_factory=lambda: defaultdict(lambda: defaultdict(list))
    )
    frequencies: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def lemmas(self) -> set[str]:
        return set(self.paradigms)

    def forms(self, lemma: str, *, case: str, number: str) -> list[str]:
        """Every attested form for one slot, most frequent first."""
        slot = self.paradigms.get(lemma, {}).get((case, number), [])
        ordered = sorted(slot, key=lambda pair: (-pair[0], pair[1]))
        seen: set[str] = set()
        forms = []
        for _, form in ordered:
            if form not in seen:
                seen.add(form)
                forms.append(form)
        return forms

    def frequency(self, lemma: str) -> int:
        return self.frequencies.get(lemma, 0)


def _open(path: Path):  # type: ignore[no-untyped-def]
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return open(path, encoding="utf-8", errors="replace")


def load_lexicon(
    path: Path | str,
    *,
    upos: str = "NOUN",
    lemmas: Iterable[str] | None = None,
) -> Lexicon:
    """Index one part of speech, optionally restricted to a set of lemmas."""
    wanted = set(lemmas) if lemmas is not None else None
    lexicon = Lexicon()

    with _open(Path(path)) as handle:
        for line in handle:
            columns = line.rstrip("\n").split("\t")
            if len(columns) < _MIN_COLUMNS or columns[_UPOS] != upos:
                continue
            lemma = columns[_LEMMA]
            if wanted is not None and lemma not in wanted:
                continue

            feats = dict(
                part.split("=", 1) for part in columns[_FEATS].split("|") if "=" in part
            )
            case, number = feats.get("Case"), feats.get("Number")
            if case is None or number is None:
                continue

            try:
                frequency = int(columns[_FREQ])
            except ValueError:
                frequency = 0

            lexicon.paradigms[lemma][(case, number)].append((frequency, columns[_FORM]))
            lexicon.frequencies[lemma] = lexicon.frequencies.get(lemma, 0) + frequency

    return lexicon
