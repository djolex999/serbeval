"""Spread the correct answer evenly across A/B/C/D.

The seed items were written with the correct answer first and never shuffled: in
srb_grammar the gold letter was A for 30 of 50 items and never D, in srb_idioms A for
24 of 30. A model that always answers "A" scored 60% and 80% there without knowing any
Serbian, so MCQ accuracy partly measured a letter preference.

Each item (or script pair) gets a target position from a balanced, seeded assignment;
the gold choice moves there and the distractors keep their relative order. Targets
depend only on item ids, so the result is deterministic and idempotent — re-running on
balanced data changes nothing. Both members of a Cyrillic/Latin pair receive the same
permutation, because their choices are transliterations aligned position by position.
"""

import random
from collections import defaultdict
from collections.abc import Sequence

from serbeval.schema import EvalItem

_SEED = 20261007


def _reorder(item: EvalItem, target: int) -> EvalItem:
    gold = item.choices[item.answer_index]
    distractors = [c for i, c in enumerate(item.choices) if i != item.answer_index]
    choices = [*distractors[:target], gold, *distractors[target:]]
    return item.model_copy(update={"choices": choices, "answer_index": target})


def balance_positions(items: Sequence[EvalItem]) -> list[EvalItem]:
    """Return the items with gold positions spread evenly; order of items is preserved."""
    units: dict[str, list[int]] = defaultdict(list)
    for index, item in enumerate(items):
        units[item.pair_id or item.id].append(index)

    keys = sorted(units)
    slots = len(items[0].choices) if items else 4
    targets = [n % slots for n in range(len(keys))]
    random.Random(_SEED).shuffle(targets)

    out = list(items)
    for key, target in zip(keys, targets, strict=True):
        for index in units[key]:
            out[index] = _reorder(items[index], target)
    return out
