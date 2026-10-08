"""Turn triage runs into a review queue of likely-broken items.

An item that every strong model gets wrong is more often a broken item — wrong gold,
two defensible answers, ambiguous prompt — than a genuinely hard one. Items missed by
every model are therefore listed first, each with the gold answer next to what every
model actually said, so a human reviewer decides in seconds rather than re-deriving it.

Reads the per-sample JSONL that `--log_samples` writes; model names come from lm-eval's
config the same way `serbeval report` names them.
"""

import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from serbeval.report import _model_name, sample_correct, sample_response
from serbeval.schema import ANSWER_LETTERS


@dataclass
class Miss:
    item_id: str
    task: str
    question: str
    gold: str
    models: int
    answers: dict[str, str] = field(default_factory=dict)
    missed_by: int = 0


def _gold(doc: dict[str, object]) -> str:
    answers = doc.get("answers")
    if isinstance(answers, list) and answers:
        return " / ".join(str(a) for a in answers)
    index = doc.get("answer_index")
    return ANSWER_LETTERS[index] if isinstance(index, int) else "?"


def _runs(root: Path) -> dict[str, Path]:
    """Model name -> run directory, for every run that logged samples."""
    runs: dict[str, Path] = {}
    for results in sorted(root.rglob("results_*.json")):
        run_dir = results.parent
        if not any(run_dir.glob("samples_*.jsonl")):
            continue
        try:
            config = json.loads(results.read_text(encoding="utf-8")).get("config", {})
        except (OSError, json.JSONDecodeError):
            continue
        name = _model_name(config if isinstance(config, dict) else {}, str(run_dir.name))
        runs[name] = run_dir
    return runs


def collect_misses(results_dir: str) -> list[Miss]:
    """Every item at least one model got wrong, most-missed first."""
    runs = _runs(Path(results_dir))
    misses: dict[str, Miss] = {}
    seen_by: dict[str, set[str]] = defaultdict(set)

    for model, run_dir in runs.items():
        for sample_file in sorted(run_dir.glob("samples_*.jsonl")):
            for line in sample_file.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                doc = row.get("doc", {})
                item_id = str(doc.get("id", f"{sample_file.stem}:{row.get('doc_id')}"))
                seen_by[item_id].add(model)
                entry = misses.setdefault(
                    item_id,
                    Miss(
                        item_id=item_id,
                        task=str(doc.get("task", "")),
                        question=str(doc.get("question", "")),
                        gold=_gold(doc),
                        models=0,
                    ),
                )
                response = sample_response(row)
                entry.answers[model] = response
                # No answer at all is a provider failure, not evidence about the item.
                if response and sample_correct(row) < 1.0:
                    entry.missed_by += 1

    result = []
    for item_id, entry in misses.items():
        if entry.missed_by == 0:
            continue
        entry.models = len(seen_by[item_id])
        entry.answers = dict(sorted(entry.answers.items()))
        result.append(entry)
    return sorted(result, key=lambda m: (-m.missed_by / max(m.models, 1), m.task, m.item_id))


def collect_unanswered(results_dir: str) -> list[tuple[str, str]]:
    """(item id, model) for every request that came back with no answer at all.

    On Kie, 6 of GPT's 10 apparent misses were requests the provider never answered.
    They say nothing about the item, so they are reported apart from the review queue
    — and are the ones to re-send.
    """
    out: list[tuple[str, str]] = []
    for model, run_dir in _runs(Path(results_dir)).items():
        for sample_file in sorted(run_dir.glob("samples_*.jsonl")):
            for line in sample_file.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    row = json.loads(line)
                    if not sample_response(row):
                        out.append((str(row.get("doc", {}).get("id", "?")), model))
    return sorted(out)


def format_misses(
    misses: list[Miss], unanswered: list[tuple[str, str]] | None = None
) -> str:
    footer = ""
    if unanswered:
        footer = (
            f"\n{len(unanswered)} request(s) got no answer from the provider — not counted "
            "as misses; re-send them:\n"
            + "".join(f"    {model}: {item_id}\n" for item_id, model in unanswered)
        )
    if not misses:
        return "No misses: every model answered every item correctly.\n" + footer
    lines = [f"{len(misses)} item(s) missed by at least one model — check the ITEM first.\n"]
    for miss in misses:
        lines.append(f"{miss.item_id}   [{miss.task}]   missed by {miss.missed_by}/{miss.models}")
        lines.append(f"    {miss.question[:110]}")
        lines.append(f"    gold: {miss.gold}")
        for model, answer in miss.answers.items():
            shown = answer.replace("\n", " ")[:60] or "(no readable answer)"
            lines.append(f"    {model}: {shown}")
        lines.append("")
    return "\n".join(lines) + footer
