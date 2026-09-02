"""Interactive human verification of dataset items.

The maintainer walks through unverified items one by one (pairs together for
paired-script tasks) and either verifies, rejects, or skips each. Every
decision is written to disk immediately, so a review session can be
interrupted at any point without losing work.
"""

import json
from collections import Counter, defaultdict
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Literal

from serbeval.data import load_items, save_items, validate_dataset
from serbeval.schema import ANSWER_LETTERS, EvalItem

Decision = Literal["verify", "reject"]

_PAIRED_TASKS = {"srb_cyrillic_agreement"}

_HELP = "y = verified (correct), n = reject, s = skip, q = quit"


def build_units(items: Sequence[EvalItem]) -> list[list[EvalItem]]:
    """Group items into review units: single items, or whole pairs.

    A pair is reviewed (and verified/rejected) atomically even when one of its
    members is already verified — rejecting a single member would break pair
    integrity.
    """
    units: list[list[EvalItem]] = []
    pairs: dict[str, list[EvalItem]] = defaultdict(list)
    for item in items:
        if item.task in _PAIRED_TASKS and item.pair_id is not None:
            pairs[item.pair_id].append(item)
        elif not item.verified:
            units.append([item])
    units.extend(members for members in pairs.values() if any(not m.verified for m in members))
    return units


def apply_decision(
    items: Sequence[EvalItem],
    unit_ids: set[str],
    decision: Decision,
    reason: str,
) -> tuple[list[EvalItem], list[dict[str, object]]]:
    """Return (kept items, discarded rows) after verifying or rejecting a unit."""
    if decision == "verify":
        kept = [
            item.model_copy(update={"verified": True}) if item.id in unit_ids else item
            for item in items
        ]
        return kept, []

    kept = [item for item in items if item.id not in unit_ids]
    discarded: list[dict[str, object]] = [
        {
            **item.model_dump(),
            "dropReason": "human-review",
            "reasons": [reason or "rejected in human review"],
        }
        for item in items
        if item.id in unit_ids
    ]
    return kept, discarded


def format_unit(unit: Sequence[EvalItem]) -> str:
    """Printable review card for one unit (item or script pair)."""
    lines: list[str] = []
    first = unit[0]
    lines.append(f"[{first.task} / {first.category}]  {' + '.join(i.id for i in unit)}")
    for item in unit:
        lines.append("")
        lines.append(f"  ({item.script}) {item.question}")
        for idx, choice in enumerate(item.choices):
            marker = " ✓" if idx == item.answer_index else ""
            lines.append(f"    {ANSWER_LETTERS[idx]}. {choice}{marker}")
    lines.append("")
    lines.append(f"  Objašnjenje: {first.explanation}")
    return "\n".join(lines)


def _append_discarded(rows: Sequence[dict[str, object]], path: Path) -> None:
    with open(path, "a", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def _ask(input_fn: Callable[[str], str], prompt: str) -> str | None:
    """Read one answer; None means the session was interrupted (EOF/Ctrl-C).

    Interrupts are caught ONLY here, at the prompt — never around file writes,
    so a Ctrl-C that lands mid-save propagates instead of being reported as a
    clean stop.
    """
    try:
        return input_fn(prompt)
    except (EOFError, KeyboardInterrupt):
        return None


def run_review(
    task: str,
    data_dir: str,
    input_fn: Callable[[str], str] | None = None,
    print_fn: Callable[[str], None] = print,
) -> dict[str, int]:
    """Interactive review loop over unverified items of one task."""
    if input_fn is None:
        # resolved at call time so tests can monkeypatch builtins.input
        input_fn = input
    task_dir = Path(data_dir) / task
    items_path = task_dir / "items.jsonl"
    items = load_items(items_path)
    units = build_units(items)

    summary = {"verified": 0, "rejected": 0, "skipped": 0, "remaining": len(units)}
    if not units:
        print_fn(f"Nothing to review: all {len(items)} item(s) in {task} are verified.")
        return summary

    # a dataset with duplicate ids would make id-keyed decisions hit multiple
    # items at once — refuse to review until it is fixed
    counts = Counter(i.id for i in items)
    duplicates = sorted(id_ for id_, n in counts.items() if n > 1)
    if duplicates:
        print_fn(f"FAIL: duplicate id(s) in {items_path}: {', '.join(duplicates)}")
        print_fn("Fix the dataset (serbeval validate) before reviewing.")
        return summary

    last_mtime = items_path.stat().st_mtime_ns
    interrupted = False
    print_fn(f"{len(units)} unit(s) to review in {task}. {_HELP}")
    for pos, unit in enumerate(units, start=1):
        if interrupted:
            break
        print_fn("")
        print_fn(f"--- {pos}/{len(units)} " + "-" * 40)
        print_fn(format_unit(unit))
        unit_ids = {i.id for i in unit}
        while True:
            key = _ask(input_fn, "[y/n/s/q] > ")
            key = "q" if key is None else key.strip().lower()
            if key == "q":
                interrupted = True
                break
            if key == "s":
                summary["skipped"] += 1
                break
            if key in ("y", "n"):
                if items_path.stat().st_mtime_ns != last_mtime:
                    print_fn(f"FAIL: {items_path} changed on disk mid-session — stopping.")
                    interrupted = True
                    break
                if key == "y":
                    items, _ = apply_decision(items, unit_ids, "verify", "")
                    save_items(items, items_path)
                    summary["verified"] += 1
                else:
                    raw_reason = _ask(input_fn, "Razlog odbacivanja: ")
                    if raw_reason is None:  # Ctrl-C at the reason prompt aborts the reject
                        interrupted = True
                        break
                    items, discarded = apply_decision(items, unit_ids, "reject", raw_reason.strip())
                    # discarded first: a crash between the two writes must leave
                    # the item recoverable (in both files), never in neither
                    _append_discarded(discarded, task_dir / "discarded.jsonl")
                    save_items(items, items_path)
                    summary["rejected"] += 1
                last_mtime = items_path.stat().st_mtime_ns
                summary["remaining"] -= 1
                break
            print_fn(_HELP)

    if interrupted:
        print_fn("")
        print_fn("Prekinuto — dosadašnje odluke su sačuvane.")

    problems = validate_dataset(load_items(items_path))
    for problem in problems:
        print_fn(f"WARNING: {problem}")
    return summary
