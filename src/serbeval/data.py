"""Dataset IO and integrity validation."""

import json
import os
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path

from serbeval.schema import EvalItem

# A/B/C/D answer labels are intentionally Latin even in Cyrillic items (script-independent
# extraction), so label letters never count as a script violation.
_CYRILLIC = range(0x0400, 0x0500)
_PAIRED_TASKS = {"srb_cyrillic_agreement"}


def load_items(path: Path | str) -> list[EvalItem]:
    items = []
    with open(path, encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            try:
                items.append(EvalItem.model_validate(json.loads(line)))
            except (json.JSONDecodeError, ValueError) as exc:
                raise ValueError(f"{path}:{line_no}: {exc}") from exc
    return items


def save_items(items: Sequence[EvalItem], path: Path | str) -> None:
    # atomic: a crash mid-write must never truncate the curated dataset in place
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        for item in items:
            fh.write(json.dumps(item.model_dump(), ensure_ascii=False) + "\n")
    os.replace(tmp, target)


def _has_cyrillic(text: str) -> bool:
    return any(ord(ch) in _CYRILLIC for ch in text)


def _has_latin_letters(text: str) -> bool:
    return any(("a" <= ch <= "z") or ("A" <= ch <= "Z") or ch in "čćžšđČĆŽŠĐ" for ch in text)


def _script_problems(item: EvalItem) -> list[str]:
    text = " ".join([item.question, *item.choices])
    if item.script == "latin" and _has_cyrillic(text):
        return [f"{item.id}: script is 'latin' but text contains Cyrillic characters"]
    if item.script == "cyrillic":
        if not _has_cyrillic(text):
            return [f"{item.id}: script is 'cyrillic' but text contains no Cyrillic characters"]
        if _has_latin_letters(text):
            return [f"{item.id}: script is 'cyrillic' but text contains Latin letters"]
    return []


def _pair_problems(items: Sequence[EvalItem]) -> list[str]:
    problems = []
    pairs: dict[str, list[EvalItem]] = defaultdict(list)
    for item in items:
        if item.task in _PAIRED_TASKS:
            if item.pair_id is None:
                problems.append(f"{item.id}: pair task item without pair_id")
            else:
                pairs[item.pair_id].append(item)
    for pair_id, members in pairs.items():
        if len(members) != 2:
            problems.append(f"pair {pair_id}: expected 2 items, found {len(members)}")
            continue
        if {m.script for m in members} != {"cyrillic", "latin"}:
            problems.append(f"pair {pair_id}: must have one cyrillic and one latin item")
        if len({m.answer_index for m in members}) != 1:
            problems.append(f"pair {pair_id}: answer_index differs between scripts")
        if len({(m.task, m.category) for m in members}) != 1:
            problems.append(f"pair {pair_id}: task/category differs between scripts")
    return problems


def validate_dataset(items: Sequence[EvalItem]) -> list[str]:
    """Return a list of integrity problems; empty list means the dataset is clean."""
    problems = []

    seen_ids: set[str] = set()
    seen_questions: set[str] = set()
    for item in items:
        if item.id in seen_ids:
            problems.append(f"{item.id}: duplicate id")
        seen_ids.add(item.id)
        # identical question text is allowed across a script pair, never within one script
        question_key = f"{item.script}:{item.question.strip()}"
        if question_key in seen_questions:
            problems.append(f"{item.id}: duplicate question text")
        seen_questions.add(question_key)
        problems.extend(_script_problems(item))

    problems.extend(_pair_problems(items))
    return problems
