"""Advisory quality checks on MCQ distractors.

`serbeval validate` answers "is this data well-formed"; this module answers "is this data
*good*". It is deliberately advisory — `lint_items` never fails a build — because every
threshold here is a heuristic and the maintainer, not the linter, decides what to rewrite.

What it can see (deterministically, no model calls):

* **shape** — whether the four choices are edits of one sentence (`variant`, e.g. srb_grammar)
  or four independent statements (`semantic`, e.g. srb_idioms). Minimal-pair reasoning is only
  meaningful for the former, so applying it to idioms would produce pure false positives.
* **near-miss count** — a distractor one edit away from gold is a real trap; one that stacks two
  or more errors is not something a speaker would produce, so nobody is fooled by it. An item
  with fewer than two real traps is effectively a 2-way MCQ, where chance is 50%, not 25%.
* **structural leaks** — a gold answer that is the uniquely longest or shortest choice can be
  picked by shape alone, without knowing any Serbian.

What it explicitly CANNOT see: semantic plausibility. A distractor that is a clean one-token
edit but means something absurd ("Pišem pismo o olovkom" — a preposition/case pairing no
speaker produces) scores as a minimal pair here. Catching that needs morphological analysis of
Serbian case government, which is out of scope; a human reading the ranked output catches it.
"""

import unicodedata
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Literal

from serbeval.schema import ANSWER_LETTERS, EvalItem

Shape = Literal["variant", "semantic"]
Verdict = Literal["minimal-pair", "weak", "dead", "n/a"]

# Median pairwise token overlap at or above this means the choices are edits of one sentence.
_VARIANT_JACCARD = 0.4
# Below this overlap with gold, a distractor shares almost no material with it and is
# eliminable without reading past the first few words.
_DEAD_JACCARD = 0.3
_MIN_NEAR_MISSES = 2
_LENGTH_OUTLIER_PENALTY = 0.25
# Gold must differ from every distractor by at least this fraction of the mean choice
# length before its length counts as a giveaway (see _length_outlier).
_LENGTH_OUTLIER_MARGIN = 0.3
_SEMANTIC_LEAK_PENALTY = 0.4

# `variant`: the four choices are edits of one sentence, so minimal-pair analysis applies.
# `semantic`: they are independent statements (idiom meanings, bare facts) and it does not.
_TASK_SHAPES: dict[str, Shape] = {
    "srb_grammar": "variant",
    "srb_idioms": "semantic",
    "srb_cyrillic_agreement": "semantic",
}


@dataclass(frozen=True)
class DistractorVerdict:
    index: int
    letter: str
    text: str
    verdict: Verdict
    reason: str


@dataclass(frozen=True)
class ItemReport:
    item_id: str
    shape: Shape
    score: float
    verdicts: list[DistractorVerdict]
    flags: list[str] = field(default_factory=list)

    @property
    def near_misses(self) -> int:
        return sum(1 for v in self.verdicts if v.verdict == "minimal-pair")


def _tokens(text: str) -> list[str]:
    """Lowercased word tokens, punctuation stripped, so „olovkom." == „olovkom"."""
    normalized = "".join(
        " " if unicodedata.category(ch).startswith("P") else ch for ch in text.lower()
    )
    return normalized.split()


def _jaccard(left: Sequence[str], right: Sequence[str]) -> float:
    a, b = set(left), set(right)
    if not a and not b:
        return 1.0
    union = a | b
    return len(a & b) / len(union) if union else 1.0


def _median(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def _detect_shape(task: str, token_lists: Sequence[list[str]]) -> Shape:
    """Shape is declared per task, because it cannot be recovered from the choices.

    An item whose distractors are all unrelated garbage has exactly the same low mutual
    overlap as a well-built idiom item. Inferring shape from overlap alone therefore lets
    the worst variant items escape analysis by masquerading as semantic ones. Overlap is
    used only as a fallback for tasks this module has not been told about.
    """
    declared = _TASK_SHAPES.get(task)
    if declared is not None:
        return declared
    overlaps = [
        _jaccard(token_lists[i], token_lists[j])
        for i in range(len(token_lists))
        for j in range(i + 1, len(token_lists))
    ]
    return "variant" if _median(overlaps) >= _VARIANT_JACCARD else "semantic"


def _error_dimensions(gold: Sequence[str], other: Sequence[str]) -> tuple[int, bool]:
    """Count how many independent things a distractor changes, and whether order is one.

    A naive sequence diff is wrong here: moving one token registers as a delete plus an
    insert, so every clitic-placement distractor — the whole point of srb_grammar's
    `enklitike` category — would look like two stacked errors when it is really one very
    real trap. So lexical substitutions and word order are counted separately.
    """
    gold_counts, other_counts = Counter(gold), Counter(other)
    removed = sum((gold_counts - other_counts).values())
    added = sum((other_counts - gold_counts).values())
    lexical = max(removed, added)

    shared = gold_counts & other_counts
    gold_common = _keep_only(gold, shared)
    other_common = _keep_only(other, shared)
    reordered = gold_common != other_common

    return lexical + (1 if reordered else 0), reordered


def _keep_only(tokens: Sequence[str], allowed: Counter[str]) -> list[str]:
    remaining = Counter(allowed)
    kept = []
    for token in tokens:
        if remaining[token] > 0:
            remaining[token] -= 1
            kept.append(token)
    return kept


def _classify(gold: Sequence[str], other: Sequence[str]) -> tuple[Verdict, str]:
    overlap = _jaccard(gold, other)
    if overlap < _DEAD_JACCARD:
        return "dead", "shares almost nothing with the gold answer; eliminable at a glance"
    dimensions, reordered = _error_dimensions(gold, other)
    if dimensions <= 1:
        if reordered:
            return "minimal-pair", "same words in a different order — a word-order trap"
        return "minimal-pair", "differs from gold in one place — a real trap"
    if dimensions == 2:
        return "weak", "stacks 2 separate errors; no speaker would produce this"
    return "dead", f"stacks {dimensions} separate errors; not a plausible sentence"


def _length_outlier(token_lists: Sequence[list[str]], answer_index: int) -> bool:
    """True when gold stands out by length far enough to be pickable on shape alone.

    Rank alone is not evidence: with four choices of differing length, gold is the
    uniquely longest or shortest ~50% of the time purely by chance. The leak only exists
    when the margin to the nearest distractor is wide relative to the choices themselves,
    so we additionally require a gap of `_LENGTH_OUTLIER_MARGIN` of the mean length.
    """
    lengths = [len(t) for t in token_lists]
    gold_len = lengths[answer_index]
    others = [n for i, n in enumerate(lengths) if i != answer_index]
    mean_len = sum(lengths) / len(lengths)
    if mean_len == 0:
        return False
    margin = _LENGTH_OUTLIER_MARGIN * mean_len
    shortest_by_margin = all(gold_len + margin <= n for n in others)
    longest_by_margin = all(gold_len - margin >= n for n in others)
    return shortest_by_margin or longest_by_margin


def lint_item(item: EvalItem) -> ItemReport:
    token_lists = [_tokens(choice) for choice in item.choices]
    shape = _detect_shape(item.task, token_lists)
    gold = token_lists[item.answer_index]

    verdicts: list[DistractorVerdict] = []
    for index, tokens in enumerate(token_lists):
        if index == item.answer_index:
            continue
        if shape == "variant":
            verdict, reason = _classify(gold, tokens)
        else:
            verdict, reason = "n/a", "choices are independent statements; not a minimal-pair set"
        verdicts.append(
            DistractorVerdict(
                index=index,
                letter=ANSWER_LETTERS[index],
                text=item.choices[index],
                verdict=verdict,
                reason=reason,
            )
        )

    flags: list[str] = []
    near_misses = sum(1 for v in verdicts if v.verdict == "minimal-pair")
    if shape == "variant" and near_misses < _MIN_NEAR_MISSES:
        flags.append("two-way-mcq")
    if _length_outlier(token_lists, item.answer_index):
        flags.append("gold-length-outlier")

    if shape == "variant":
        score = near_misses / len(verdicts)
        if "gold-length-outlier" in flags:
            score -= _LENGTH_OUTLIER_PENALTY
    else:
        score = 1.0 - (_SEMANTIC_LEAK_PENALTY if "gold-length-outlier" in flags else 0.0)

    return ItemReport(
        item_id=item.id,
        shape=shape,
        score=max(0.0, min(1.0, score)),
        verdicts=verdicts,
        flags=flags,
    )


def lint_items(items: Iterable[EvalItem]) -> list[ItemReport]:
    """Report on every item, worst score first (ties broken by id for stable output)."""
    reports = [lint_item(item) for item in items]
    return sorted(reports, key=lambda r: (r.score, r.item_id))
