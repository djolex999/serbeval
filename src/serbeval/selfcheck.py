"""Self-consistency sanity filter for generated candidates.

Re-answers each candidate ``runs`` times with the model; keeps a candidate only if every
run agrees with the others AND with the gold label. Survivors stay ``verified=False`` — this
is an automated pre-filter, not a substitute for human verification.
"""

import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

import anthropic

from serbeval.schema import ANSWER_LETTERS, EvalItem

DEFAULT_MODEL = "claude-opus-4-8"

_ANSWER_RE = re.compile(r"\b([ABCD])\b")


@dataclass(frozen=True)
class SelfCheckResult:
    item: EvalItem
    answers: list[int | None]
    keep: bool
    reason: str | None


def parse_answer(text: str) -> int | None:
    """Extract the first A/B/C/D letter from a model reply, or None."""
    match = _ANSWER_RE.search(text)
    if match is None:
        return None
    return ANSWER_LETTERS.index(match.group(1))


def _prompt(item: EvalItem) -> str:
    lines = [item.question, ""]
    for letter, choice in zip(ANSWER_LETTERS, item.choices, strict=True):
        lines.append(f"{letter}) {choice}")
    lines.append("")
    lines.append("Odgovori samo slovom tačnog odgovora (A, B, C ili D).")
    return "\n".join(lines)


def _answer_once(client: anthropic.Anthropic, model: str, item: EvalItem) -> int | None:
    response = client.messages.create(
        model=model,
        max_tokens=8,
        messages=[{"role": "user", "content": _prompt(item)}],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    return parse_answer(text)


def selfcheck_item(
    client: anthropic.Anthropic, model: str, item: EvalItem, *, runs: int = 3
) -> SelfCheckResult:
    answers = [_answer_once(client, model, item) for _ in range(runs)]

    if any(a is None for a in answers):
        return SelfCheckResult(item, answers, keep=False, reason="model gave an unparseable answer")

    counts = Counter(answers)
    if len(counts) > 1:
        return SelfCheckResult(item, answers, keep=False, reason="runs disagree with each other")

    (chosen,) = counts
    if chosen != item.answer_index:
        return SelfCheckResult(
            item, answers, keep=False, reason="unanimous answer disagrees with gold label"
        )

    return SelfCheckResult(item, answers, keep=True, reason=None)


def selfcheck_items(
    client: anthropic.Anthropic, model: str, items: Sequence[EvalItem], *, runs: int = 3
) -> list[SelfCheckResult]:
    return [selfcheck_item(client, model, item, runs=runs) for item in items]
