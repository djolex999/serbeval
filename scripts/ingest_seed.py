"""One-shot: ingest the seed-dataset workflow result into data/ files.

Reads the workflow's JSON result, assigns schema fields, applies two mechanical cleanups
(dedupe identical questions; reject items whose Latin text contains Cyrillic letters — the
clean-script convention for srb_grammar/srb_idioms), then writes items.jsonl + discarded.jsonl
per task. All items land verified=False.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from serbeval.data import save_items, validate_dataset
from serbeval.schema import EvalItem

RESULT_FILE = sys.argv[1]
ROOT = Path(__file__).resolve().parent.parent

_CYRILLIC = range(0x0400, 0x0500)


def has_cyrillic(text: str) -> bool:
    return any(ord(ch) in _CYRILLIC for ch in text)


def slug(task: str) -> str:
    return task.replace("_", "-")


def main() -> int:
    with open(RESULT_FILE, encoding="utf-8") as fh:
        payload = json.load(fh)["result"]
    raw_items = payload["items"]
    dropped = list(payload["dropped"])

    seen_questions: dict[str, set[str]] = {}  # task -> normalized questions
    seq: dict[tuple[str, str], int] = {}  # (task, category) -> counter
    kept: dict[str, list[EvalItem]] = {}

    for raw in raw_items:
        task = raw["task"]
        category = raw["category"]
        question = raw["question"]
        choices = raw["choices"]
        text = " ".join([question, *choices])

        norm = question.strip()
        if norm in seen_questions.setdefault(task, set()):
            dropped.append({**raw, "reasons": ["duplicate question"], "dropReason": "duplicate"})
            continue
        if has_cyrillic(text):
            dropped.append(
                {**raw, "reasons": ["Cyrillic in Latin item"], "dropReason": "mixed-script"}
            )
            continue
        seen_questions[task].add(norm)

        key = (task, category)
        seq[key] = seq.get(key, 0) + 1
        item = EvalItem(
            id=f"{slug(task)}-{category}-{seq[key]:04d}",
            task=task,
            category=category,
            question=question,
            choices=choices,
            answer_index=raw["answer_index"],
            explanation=raw["explanation"],
            script="latin",
            source="handwritten-claude",
            verified=False,
        )
        kept.setdefault(task, []).append(item)

    for task, items in sorted(kept.items()):
        problems = validate_dataset(items)
        if problems:
            print(f"VALIDATION FAILED for {task}:")
            for p in problems:
                print(f"  {p}")
            return 1
        save_items(items, ROOT / "data" / task / "items.jsonl")
        by_cat: dict[str, int] = {}
        for it in items:
            by_cat[it.category] = by_cat.get(it.category, 0) + 1
        print(f"{task}: {len(items)} items {dict(sorted(by_cat.items()))}")

    # discarded items grouped per task
    dropped_by_task: dict[str, list[dict]] = {}
    for d in dropped:
        dropped_by_task.setdefault(d.get("task", "unknown"), []).append(d)
    for task, rows in dropped_by_task.items():
        if task == "unknown":
            continue
        path = ROOT / "data" / task / "discarded.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"{task}: {len(rows)} discarded -> {path.relative_to(ROOT)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
