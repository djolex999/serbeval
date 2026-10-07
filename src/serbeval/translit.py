"""Serbian Latin -> Cyrillic transliteration.

Serbian has a near-perfect 1:1 orthographic mapping between the two scripts. Digraphs
(lj, nj, dž) must be matched before their component letters. This is intended for the
controlled vocabulary of the cyrillic-agreement dataset — avoid words where a digraph spans
a morpheme boundary (e.g. "nadživeti" = nad+živeti, "injekcija" = in+jekcija), since those
are not single Cyrillic letters and this function cannot know the boundary.
"""

# Order matters: digraphs first, longest first, and case variants before single letters.
_PAIRS: list[tuple[str, str]] = [
    ("Lj", "Љ"), ("LJ", "Љ"), ("lj", "љ"),
    ("Nj", "Њ"), ("NJ", "Њ"), ("nj", "њ"),
    ("Dž", "Џ"), ("DŽ", "Џ"), ("dž", "џ"),
    ("A", "А"), ("B", "Б"), ("V", "В"), ("G", "Г"), ("D", "Д"), ("Đ", "Ђ"),
    ("E", "Е"), ("Ž", "Ж"), ("Z", "З"), ("I", "И"), ("J", "Ј"), ("K", "К"),
    ("L", "Л"), ("M", "М"), ("N", "Н"), ("O", "О"), ("P", "П"), ("R", "Р"),
    ("S", "С"), ("T", "Т"), ("Ć", "Ћ"), ("U", "У"), ("F", "Ф"), ("H", "Х"),
    ("C", "Ц"), ("Č", "Ч"), ("Š", "Ш"),
    ("a", "а"), ("b", "б"), ("v", "в"), ("g", "г"), ("d", "д"), ("đ", "ђ"),
    ("e", "е"), ("ž", "ж"), ("z", "з"), ("i", "и"), ("j", "ј"), ("k", "к"),
    ("l", "л"), ("m", "м"), ("n", "н"), ("o", "о"), ("p", "п"), ("r", "р"),
    ("s", "с"), ("t", "т"), ("ć", "ћ"), ("u", "у"), ("f", "ф"), ("h", "х"),
    ("c", "ц"), ("č", "ч"), ("š", "ш"),
]

# Build a longest-key-first list for a single left-to-right scan.
_SORTED = sorted(_PAIRS, key=lambda kv: -len(kv[0]))


def latin_to_cyrillic(text: str) -> str:
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        for latin, cyr in _SORTED:
            if text.startswith(latin, i):
                out.append(cyr)
                i += len(latin)
                break
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


# Cyrillic -> Latin is unambiguous: every Cyrillic letter has exactly one Latin spelling
# (љ -> lj, њ -> nj, џ -> dž), so the morpheme-boundary caveat above does not apply.
# The first pair listed for each Cyrillic letter is its canonical spelling.
_REVERSE: dict[str, str] = {}
for _latin, _cyr in _PAIRS:
    _REVERSE.setdefault(_cyr, _latin)


def cyrillic_to_latin(text: str) -> str:
    """Transliterate Serbian Cyrillic to Latin; anything else passes through unchanged."""
    return "".join(_REVERSE.get(ch, ch) for ch in text)
