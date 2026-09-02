"""Dataset composition and verification-progress statistics."""

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from serbeval.data import load_items

_PAIRED_TASKS = {"srb_cyrillic_agreement"}


@dataclass
class TaskStats:
    task: str
    total: int
    verified: int
    categories: dict[str, int] = field(default_factory=dict)
    candidates: int = 0
    discarded: int = 0
    pairs: int | None = None
    error: str | None = None


def _count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    with open(path, encoding="utf-8") as fh:
        return sum(1 for line in fh if line.strip())


def collect_stats(data_dir: str) -> list[TaskStats]:
    root = Path(data_dir)
    stats: list[TaskStats] = []
    if not root.is_dir():
        return stats
    for items_path in sorted(root.glob("*/items.jsonl")):
        task_dir = items_path.parent
        try:
            items = load_items(items_path)
        except (OSError, ValueError) as exc:
            # one broken file must not hide the stats of every other task
            stats.append(TaskStats(task=task_dir.name, total=0, verified=0, error=str(exc)))
            continue
        pairs: int | None = None
        if task_dir.name in _PAIRED_TASKS:
            pairs = len({i.pair_id for i in items if i.pair_id is not None})
        stats.append(
            TaskStats(
                task=task_dir.name,
                total=len(items),
                verified=sum(1 for i in items if i.verified),
                categories=dict(Counter(i.category for i in items)),
                candidates=_count_lines(task_dir / "candidates.jsonl"),
                discarded=_count_lines(task_dir / "discarded.jsonl"),
                pairs=pairs,
            )
        )
    return stats


def format_stats(stats: list[TaskStats]) -> str:
    if not stats:
        return "No datasets found."
    lines: list[str] = []
    for s in stats:
        if s.error is not None:
            lines.append(f"{s.task}: ERROR — {s.error}")
            continue
        header = f"{s.task}: {s.verified}/{s.total} verified"
        if s.pairs is not None:
            header += f" ({s.pairs} pair(s))"
        header += f" · {s.candidates} candidate(s) · {s.discarded} discarded"
        lines.append(header)
        for category, count in sorted(s.categories.items()):
            lines.append(f"  {category}: {count}")
    return "\n".join(lines)
