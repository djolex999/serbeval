"""Human baseline: the control that tells a bad model from a bad benchmark.

A low model score has two explanations — the model is weak at Serbian, or the items are
broken — and the numbers alone cannot separate them. A native speaker answering a sample
does separate them: if a native speaker does not score near 100%, the items are wrong,
and no amount of model comparison means anything until they are fixed.

The flow is one file. `build_worksheet` writes the sampled items with blank ODGOVOR lines,
the human fills them in, and `score_worksheet` reads the same file back. The gold answer
and the explanation are never written into the worksheet, because a control that shows the
answer while you answer measures nothing.

Cloze answers are scored with `serbeval.cloze.is_correct` — the benchmark's own rule — so
the human baseline and a model score are measured on identical terms rather than by a
second, subtly different comparison.
"""

import random
import re
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field

from serbeval.cloze import is_correct
from serbeval.schema import ANSWER_LETTERS, ClozeItem, EvalItem

Item = EvalItem | ClozeItem

_ANSWER_LINE = "ODGOVOR:"
_ID_LINE = re.compile(r"^\[\d+\]\s+(\S+)")
_FILLED = re.compile(rf"^{_ANSWER_LINE}\s*(.+?)\s*$")

_HEADER = """# serbeval — ljudski baseline
#
# Popuni svaku ODGOVOR: liniju. Za pitanja sa ponuđenim odgovorima upiši slovo
# (A, B, C ili D); za dopunjavanje upiši traženi oblik reči.
#
# Kad završiš:  serbeval baseline --score <ovaj fajl>
#
# Poenta nije da izmerimo tebe. Ako izvorni govornik ne pogodi skoro sve, itemi su
# pokvareni — a to se iz rezultata modela ne vidi.
"""


@dataclass
class BaselineResult:
    answered: int = 0
    correct: int = 0
    wrong: list[str] = field(default_factory=list)
    unanswered: list[str] = field(default_factory=list)

    @property
    def accuracy(self) -> float:
        return self.correct / self.answered if self.answered else 0.0


def sample_items(pool: Sequence[Item], *, n: int, seed: int = 0) -> list[Item]:
    """Draw `n` items spread evenly across tasks, deterministically.

    A flat random draw over a pool that is 90% one task leaves the other tasks
    unmeasured — and the baseline exists to find broken items everywhere, not to
    re-measure the largest dataset.
    """
    by_task: dict[str, list[Item]] = defaultdict(list)
    for item in pool:
        by_task[item.task].append(item)

    rng = random.Random(seed)
    for items in by_task.values():
        rng.shuffle(items)

    drawn: list[Item] = []
    tasks = sorted(by_task)
    depth = 0
    while len(drawn) < n and any(depth < len(by_task[t]) for t in tasks):
        for task in tasks:
            if depth < len(by_task[task]) and len(drawn) < n:
                drawn.append(by_task[task][depth])
        depth += 1
    return drawn


def build_worksheet(items: Sequence[Item]) -> str:
    lines = [_HEADER]
    for number, item in enumerate(items, start=1):
        lines.append(f"[{number}] {item.id}")
        if isinstance(item, ClozeItem):
            lines.append(f"{item.question}  ({item.cue})")
        else:
            lines.append(item.question)
            for letter, choice in zip(ANSWER_LETTERS, item.choices, strict=False):
                lines.append(f"  {letter}) {choice}")
        lines.append(_ANSWER_LINE)
        lines.append("")
    return "\n".join(lines)


def parse_worksheet(text: str) -> dict[str, str]:
    """Map item id -> the answer written on its ODGOVOR line, skipping blank ones."""
    answers: dict[str, str] = {}
    current: str | None = None
    for line in text.splitlines():
        match = _ID_LINE.match(line.strip())
        if match:
            current = match.group(1)
            continue
        filled = _FILLED.match(line.strip())
        if filled and current is not None:
            answers[current] = filled.group(1)
            current = None
    return answers


def score_worksheet(text: str, items: Sequence[Item]) -> BaselineResult:
    given = parse_worksheet(text)
    result = BaselineResult()
    for item in items:
        answer = given.get(item.id)
        if answer is None:
            result.unanswered.append(item.id)
            continue
        result.answered += 1
        if isinstance(item, ClozeItem):
            correct = is_correct(answer, item)
        else:
            correct = answer.strip().upper()[:1] == item.answer_letter
        if correct:
            result.correct += 1
        else:
            result.wrong.append(item.id)
    return result
