"""Multi-error passage correction (v2 format A): markup, extraction and per-edit scoring.

A passage is written once in markup: `{correct|wrong}` marks an error site, and
`{a/b|wrong}` accepts either correct spelling. The model sees the source (every site
wrong), is not told how many errors there are or what kind, and must return the whole
corrected passage.

Scoring compares token sequences after the cloze folding (case, punctuation and script
folded; diacritics and intra-word hyphens never). The output is aligned to the gold, so:

    true positive   an error site whose gold tokens the output reproduces exactly
    false negative  an error site it left wrong or fixed wrongly
    false positive  a change anywhere outside the error sites (over-correction)

The headline is passage exact match; per-edit recall and precision are the diagnostics.
"""

import difflib
import re
from dataclasses import dataclass
from itertools import product

from serbeval.cloze import normalize
from serbeval.translit import cyrillic_to_latin

_SITE = re.compile(r"\{([^{}|]*)\|([^{}]*)\}")
_MARKER = re.compile(r"ispravljeno\s*:", re.IGNORECASE)
# Below this share of tokens kept (of the source or of the gold, whichever it is closer
# to), the model rewrote the passage instead of correcting it, and per-edit scores would
# only measure the rewrite. Against the source alone, a correct answer to a passage dense
# with joins and splits falls under the bar.
_MIN_KEPT = 0.8


@dataclass(frozen=True)
class Site:
    alternatives: tuple[str, ...]
    wrong: str

    @property
    def free(self) -> bool:
        """The source form is itself accepted: the norm is split here, so no credit or penalty."""
        return self.wrong in self.alternatives


@dataclass(frozen=True)
class Passage:
    source: str
    gold: str
    sites: tuple[Site, ...]
    parts: tuple[str | Site, ...]


@dataclass(frozen=True)
class PassageScore:
    exact: bool
    true_pos: int
    false_pos: int
    false_neg: int
    unparsed: bool


def parse_markup(markup: str) -> Passage:
    parts: list[str | Site] = []
    pos = 0
    for m in _SITE.finditer(markup):
        parts.append(markup[pos : m.start()])
        alternatives = tuple(a.strip() for a in m.group(1).split("/") if a.strip())
        if not alternatives:
            raise ValueError(f"error site without a correct form: {m.group(0)!r}")
        parts.append(Site(alternatives, m.group(2).strip()))
        pos = m.end()
    parts.append(markup[pos:])
    source = "".join(p.wrong if isinstance(p, Site) else p for p in parts)
    gold = "".join(p.alternatives[0] if isinstance(p, Site) else p for p in parts)
    sites = tuple(p for p in parts if isinstance(p, Site))
    return Passage(source, gold, sites, tuple(parts))


def extract_passage(raw: str) -> str:
    """Everything after the last „Ispravljeno:“, lines joined; "" without the marker."""
    markers = list(_MARKER.finditer(raw or ""))
    if not markers:
        return ""
    return " ".join(line.strip() for line in raw[markers[-1].end() :].splitlines() if line.strip())


def _tokens(text: str) -> list[str]:
    return normalize(cyrillic_to_latin(text)).split()


def _kept(reference: list[str], out: list[str]) -> float:
    """Share of `reference` tokens the output keeps in order."""
    matcher = difflib.SequenceMatcher(None, reference, out, autojunk=False)
    return sum(b.size for b in matcher.get_matching_blocks()) / max(len(reference), 1)


def _gold_variants(passage: Passage) -> list[tuple[list[str], list[tuple[int, int]]]]:
    """Every combination of accepted spellings, as tokens plus each site's token span."""
    choices = [p.alternatives if isinstance(p, Site) else (p,) for p in passage.parts]
    variants = []
    for combo in product(*choices):
        tokens: list[str] = []
        spans: list[tuple[int, int]] = []
        for part, text in zip(passage.parts, combo, strict=True):
            start = len(tokens)
            tokens += _tokens(text)
            if isinstance(part, Site):
                spans.append((start, len(tokens)))
        variants.append((tokens, spans))
    return variants


def score_passage(output: str, passage: Passage) -> PassageScore:
    out = _tokens(output)
    unparsed = not out or max(
        _kept(_tokens(passage.source), out), _kept(_tokens(passage.gold), out)
    ) < _MIN_KEPT

    best: PassageScore | None = None
    for gold, spans in _gold_variants(passage):
        ops = [op for op in difflib.SequenceMatcher(None, gold, out, autojunk=False).get_opcodes()
               if op[0] != "equal"]

        def touches(op: tuple[str, int, int, int, int], span: tuple[int, int]) -> bool:
            _, i1, i2, _, _ = op
            a, b = span
            return i1 < b and i2 > a if i1 < i2 else a <= i1 <= b

        errors = [span for span, site in zip(spans, passage.sites, strict=True) if not site.free]
        hit = [not any(touches(op, span) for op in ops) for span in errors]
        false_pos = sum(1 for op in ops if not any(touches(op, span) for span in spans))
        score = PassageScore(
            exact=not ops and not unparsed,
            true_pos=sum(hit),
            false_pos=false_pos,
            false_neg=len(errors) - sum(hit),
            unparsed=unparsed,
        )
        if best is None or (score.exact, score.true_pos, -score.false_pos) > (
            best.exact, best.true_pos, -best.false_pos
        ):
            best = score
    assert best is not None
    return best
