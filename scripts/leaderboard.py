#!/usr/bin/env python
"""Print the leaderboard table from results/openrouter/<model>/.

Every results_*.json under a model's directory is merged, so a run split into parallel
parts (one process per task group) reads as one model. A model missing any task is left
out rather than averaged over fewer tasks.

    scripts/leaderboard.py [results/openrouter]
"""

import json
import sys
from pathlib import Path

GROUPS = {
    "MCQ": ["srb_grammar", "srb_idioms", "srb_cyrillic_agreement"],
    "Cloze": ["srb_grammar_cloze", "srb_grammar_cloze_mined", "srb_grammar_cloze_synth"],
    "Pravopis": [
        f"srb_pravopis_{x}"
        for x in ["prefiksoidi", "poluslozenice", "slozeni_pridevi", "sastavljeno_rastavljeno"]
    ],
    "Probni": [
        f"srb_probe_{x}"
        for x in [
            "jat", "aorist_imperfekat", "sibilarizacija",
            "broj_pridev_imenica", "sastavljeno_rastavljeno", "poluslozenice",
        ]
    ],
    "Ispravljanje": [
        "srb_correction_razmak_crtica", "srb_correction_c_c", "srb_correction_ispravno",
    ],
}
ALL_TASKS = [task for tasks in GROUPS.values() for task in tasks]


def metric(result: dict[str, float], name: str) -> float:
    # MCQ tasks report under the regex filter, cloze/correction under "none".
    return float(result.get(f"{name},none", result.get(f"{name},extract_answer", 0.0)))


def merged_results(model_dir: Path) -> dict[str, dict[str, float]]:
    merged: dict[str, dict[str, float]] = {}
    for path in sorted(model_dir.rglob("results_*.json")):
        with open(path, encoding="utf-8") as fh:
            results = json.load(fh)["results"]
        merged.update({k: v for k, v in results.items() if k.startswith("srb_")})
    return merged


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "results/openrouter")
    rows = []
    for model_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        results = merged_results(model_dir)
        if not all(task in results for task in ALL_TASKS):
            continue
        groups = {
            name: 100 * sum(metric(results[t], "exact_match") for t in tasks) / len(tasks)
            for name, tasks in GROUPS.items()
        }
        worst_unparsed = max(metric(results[t], "unparsed") for t in ALL_TASKS)
        rows.append((sum(groups.values()) / len(groups), model_dir.name, groups, worst_unparsed))

    print("| # | Model | " + " | ".join(GROUPS) + " | Prosek | max unparsed |")
    print("|---|---|" + "---|" * (len(GROUPS) + 2))
    for rank, (avg, name, groups, unparsed) in enumerate(sorted(rows, reverse=True), 1):
        cells = " | ".join(f"{value:.0f}%" for value in groups.values())
        print(f"| {rank} | {name} | {cells} | **{avg:.0f}%** | {unparsed:.2f} |")


if __name__ == "__main__":
    main()
