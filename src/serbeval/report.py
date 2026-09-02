"""Summarize lm-eval results JSON files into a markdown table."""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

# metric keys look like "exact_match,extract_answer" / "pair_agreement,none"
_STDERR_MARKER = "_stderr"

# lm-eval adapter names that show up in config["model"] / results dirs — never
# a real model label, so fall through to the directory name instead
_ADAPTER_NAMES = {
    "anthropic-chat",
    "anthropic-chat-completions",
    "anthropic-completions",
    "openai-chat-completions",
    "openai-completions",
    "local-chat-completions",
    "local-completions",
    "hf",
    "hf-auto",
    "vllm",
    "dummy",
}


@dataclass
class RunResult:
    model: str
    task: str
    source: str
    metrics: dict[str, tuple[float, float | None]] = field(default_factory=dict)


def _model_name(config: dict[str, object], fallback: str) -> str:
    model_args = config.get("model_args")
    if isinstance(model_args, dict):
        model = model_args.get("model")
        if isinstance(model, str) and model:
            return model
    if isinstance(model_args, str):
        match = re.search(r"model=([^,]+)", model_args)
        if match:
            return match.group(1)
    model = config.get("model")
    if isinstance(model, str) and model and model not in _ADAPTER_NAMES:
        return model
    return fallback


def _parse_metrics(task_results: dict[str, object]) -> dict[str, tuple[float, float | None]]:
    values: dict[str, float] = {}
    stderrs: dict[str, float] = {}
    for key, raw in task_results.items():
        if "," not in key or not isinstance(raw, int | float):
            continue
        metric = key.split(",", 1)[0]
        if metric.endswith(_STDERR_MARKER):
            stderrs[metric.removesuffix(_STDERR_MARKER)] = float(raw)
        else:
            values[metric] = float(raw)
    return {name: (value, stderrs.get(name)) for name, value in values.items()}


def collect_results(results_dir: str) -> tuple[list[RunResult], list[str]]:
    """Parse the newest results_*.json per directory anywhere under results_dir.

    Recursive on purpose: with ``--output_path results/haiku-4-5`` lm-eval
    writes ``results/haiku-4-5/<model_name_sanitized>/results_*.json`` — one
    directory deeper than the output path. Returns (runs, warnings); a corrupt
    file is skipped with a warning instead of aborting the whole report.
    """
    root = Path(results_dir)
    runs: list[RunResult] = []
    warnings: list[str] = []
    if not root.is_dir():
        return runs, warnings
    by_dir: dict[Path, list[Path]] = {}
    for found in root.rglob("results_*.json"):
        by_dir.setdefault(found.parent, []).append(found)
    for run_dir in sorted(by_dir):
        # lm-eval names files by ISO timestamp → lexicographic max == newest
        newest = max(by_dir[run_dir])
        try:
            payload = json.loads(newest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            warnings.append(f"skipped {newest}: {exc}")
            continue
        results = payload.get("results")
        config = payload.get("config", {})
        if not isinstance(results, dict) or not isinstance(config, dict):
            warnings.append(f"skipped {newest}: no results/config objects")
            continue
        fallback = str(run_dir.relative_to(root))
        model = _model_name(config, fallback=fallback)
        for task, task_results in sorted(results.items()):
            if not isinstance(task_results, dict):
                continue
            metrics = _parse_metrics(task_results)
            if metrics:
                runs.append(
                    RunResult(model=model, task=task, source=str(newest), metrics=metrics)
                )
    return runs, warnings


def format_markdown(runs: list[RunResult]) -> str:
    if not runs:
        return "No results found."
    metric_names = sorted({name for run in runs for name in run.metrics})
    header = "| Model | Task | " + " | ".join(metric_names) + " |"
    divider = "| --- | --- | " + " | ".join("---" for _ in metric_names) + " |"
    lines = [header, divider]
    for run in sorted(runs, key=lambda r: (r.model, r.task)):
        cells: list[str] = []
        for name in metric_names:
            entry = run.metrics.get(name)
            if entry is None:
                cells.append("—")
                continue
            value, stderr = entry
            cells.append(f"{value:.3f}" + (f" ±{stderr:.3f}" if stderr is not None else ""))
        lines.append(f"| {run.model} | {run.task} | " + " | ".join(cells) + " |")
    return "\n".join(lines)
