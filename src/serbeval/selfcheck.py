"""Self-consistency sanity filter for generated candidates.

Re-answers each candidate ``runs`` times with the model; keeps a candidate only if every
run agrees with the others AND with the gold label. Survivors stay ``verified=False`` — this
is an automated pre-filter, not a substitute for human verification.
"""

import json
import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import anthropic

from serbeval.data import load_items, save_items
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


def run_selfcheck(
    client: anthropic.Anthropic,
    *,
    task: str,
    runs: int,
    model: str,
    data_dir: Path | str,
) -> dict[str, int]:
    """Filter data/<task>/candidates.jsonl in place.

    Survivors are written back to candidates.jsonl (still verified=False); rejects are appended
    to discarded.jsonl with the recorded answers and reason. Returns {"kept", "discarded"}.
    """
    task_dir = Path(data_dir) / task
    candidates_path = task_dir / "candidates.jsonl"
    discarded_path = task_dir / "discarded.jsonl"

    candidates = load_items(candidates_path) if candidates_path.exists() else []
    results = selfcheck_items(client, model, candidates, runs=runs)

    survivors = [r.item for r in results if r.keep]
    rejects = [r for r in results if not r.keep]

    save_items(survivors, candidates_path)
    if rejects:
        discarded_path.parent.mkdir(parents=True, exist_ok=True)
        with open(discarded_path, "a", encoding="utf-8") as fh:
            for r in rejects:
                row = r.item.model_dump()
                row["selfcheck_answers"] = r.answers
                row["dropReason"] = r.reason
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    return {"kept": len(survivors), "discarded": len(rejects)}
