#!/usr/bin/env python
"""Re-score saved official-set runs against the current data/official/ (errata, no API).

For every per-sample log, each answer is checked against the item as it is NOW: dropped
items leave the task, items whose gold changed are scored again with the task's own
process_results, unchanged ones keep their stored score. The task's entry in the matching
results_*.json is rewritten; the per-sample logs are left as they were (the raw record).

    PYTHONPATH=src python scripts/rescore_official.py results/official [more roots...]
"""

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lm_eval_tasks"))
import utils  # noqa: E402  (the task YAMLs' own !function helpers)

OFFICIAL = ROOT / "data" / "official"
VERSION = json.loads((OFFICIAL / "MANIFEST.json").read_text(encoding="utf-8"))["version"]


def current_items() -> dict[str, dict[str, object]]:
    items: dict[str, dict[str, object]] = {}
    for path in OFFICIAL.glob("*.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            items[row["id"]] = row
    return items


def score(task: str, doc: dict[str, object], raw: str) -> dict[str, float]:
    if task.startswith("srb_correction"):
        return utils.process_results_correction(doc, [raw])
    if "answer_index" in doc:
        return utils.process_results_mcq(doc, [raw])
    return utils.process_results_cloze(doc, [raw])


def _differs(now: dict[str, object], doc: dict[str, object]) -> bool:
    # The datasets loader fills keys missing from a row with None; those are not changes.
    def clean(row: dict[str, object]) -> dict[str, object]:
        return {k: v for k, v in row.items() if v is not None}
    return clean(now) != clean(doc)


def stderr(values: list[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    return math.sqrt(sum((v - mean) ** 2 for v in values) / (n - 1) / n)


def rescore_samples(path: Path, items: dict[str, dict[str, object]]) -> tuple[str, dict[str, list[float]]] | None:
    task = path.name.removeprefix("samples_").rsplit("_", 1)[0]
    changed = False
    metrics: dict[str, list[float]] = {"exact_match": [], "unparsed": []}
    for line in path.read_text(encoding="utf-8").splitlines():
        sample = json.loads(line)
        doc = sample["doc"]
        now = items.get(str(doc["id"]))
        if now is None:
            changed = True
            continue
        if _differs(now, doc):
            changed = True
            result = score(task, now, sample["resps"][0][0])
        else:
            result = {k: sample[k] for k in metrics}
        for k in metrics:
            metrics[k].append(float(result[k]))
    return (task, metrics) if changed else None


def main() -> None:
    items = current_items()
    roots = [Path(a) for a in sys.argv[1:]] or [ROOT / "results" / "official"]
    touched = 0
    for root in roots:
        for samples in sorted(root.rglob("samples_srb_*.jsonl")):
            if "cyrillic_agreement" in samples.name:
                continue  # pair metric; no cyrillic item has been changed by any errata
            rescored = rescore_samples(samples, items)
            if rescored is None:
                continue
            task, metrics = rescored
            [results_path] = samples.parent.glob(
                "results_" + samples.name.rsplit("_", 1)[1].removesuffix(".jsonl") + ".json"
            )
            data = json.loads(results_path.read_text(encoding="utf-8"))
            entry = data["results"][task]
            key = next(k.split(",", 1)[1] for k in entry if k.startswith("exact_match,"))
            for name, values in metrics.items():
                entry[f"{name},{key}"] = sum(values) / len(values)
                entry[f"{name}_stderr,{key}"] = stderr(values)
            entry["sample_len"] = len(metrics["exact_match"])
            data["n-samples"][task]["effective"] = len(metrics["exact_match"])
            data.setdefault("serbeval_rescored", {})[task] = VERSION
            results_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                                    encoding="utf-8")
            touched += 1
    print(f"OK: re-scored {touched} task result(s) against official {VERSION}")


if __name__ == "__main__":
    main()
