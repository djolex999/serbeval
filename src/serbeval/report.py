"""Read lm-eval output and say what it does — and does not — support concluding.

Two layers, because they answer different questions and have different requirements:

* `collect_results` + `format_markdown` read the aggregate ``results_*.json`` and produce the
  headline table. They work on any run.
* `load_runs` + `format_analysis` read the per-sample JSONL that ``--log_samples`` writes and
  add the statistics: a **Wilson score interval** per task, and an explicit statement when two
  models' intervals overlap and the item count therefore cannot rank them. serbeval's tasks are
  small (50 / 30 / 30 items), so a ten-point gap is well inside noise and a bare table invites
  the reader to rank anyway.

Wilson rather than the normal approximation: benchmark accuracies sit near 0 and 1 often enough
that the normal interval produces bounds outside [0, 1] and badly wrong coverage at small n.

The per-sample rows carry the whole item as ``doc``, so script, difficulty and category
breakdowns need no join back to the dataset files.

Cloze samples are re-scored with today's rules rather than trusting the ``exact_match`` a run
recorded: a run stores the verdict of the scoring code it ran with, so a later scoring fix
(Cyrillic answers to Latin items, answers after a reasoning line) would otherwise leave the
report quoting stale numbers while `serbeval triage` — which re-scores the same way — shows
the corrected ones. When per-sample logs exist, the table's ``exact_match`` follows them too.
"""

import json
import re
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
from math import sqrt
from pathlib import Path

from serbeval.cloze import matches_any

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

# metric keys look like "exact_match,extract_answer" / "pair_agreement,none"
_STDERR_MARKER = "_stderr"


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


def sample_response(row: dict[str, object]) -> str:
    """The raw model response of one per-sample row, or "" when the provider gave none."""
    resps = row.get("resps")
    if isinstance(resps, list) and resps and isinstance(resps[0], list) and resps[0]:
        return str(resps[0][0]).strip()
    return ""


def sample_correct(row: dict[str, object]) -> float:
    """Verdict for one per-sample row under the CURRENT scoring rules.

    Cloze rows are re-scored from the raw response; MCQ letter extraction has not
    changed since the first run, so its recorded verdict stands.
    """
    doc = row.get("doc")
    answers = doc.get("answers") if isinstance(doc, dict) else None
    if isinstance(answers, list):
        return 1.0 if matches_any(sample_response(row), [str(a) for a in answers]) else 0.0
    recorded = row.get("exact_match", 0.0)
    return float(recorded) if isinstance(recorded, int | float) else 0.0


# 1.96 => 95%. Fixed rather than configurable: the report's job is one honest default.
Z = 1.96
# Below this many items an accuracy estimate is too wide to mean anything.
MIN_USABLE_N = 10
_PAIRED_TASK = "srb_cyrillic_agreement"


@dataclass(frozen=True)
class Stat:
    correct: int
    n: int
    accuracy: float
    ci_low: float
    ci_high: float

    @property
    def half_width(self) -> float:
        return (self.ci_high - self.ci_low) / 2


@dataclass(frozen=True)
class ModelRun:
    name: str
    samples: dict[str, list[tuple[dict[str, object], float]]] = field(default_factory=dict)
    pair_agreement: dict[str, float] = field(default_factory=dict)

    @property
    def tasks(self) -> list[str]:
        return sorted(self.samples)


def wilson_interval(correct: int, n: int, z: float = Z) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion, clamped to [0, 1]."""
    if n <= 0:
        return (0.0, 1.0)
    z2 = z * z
    denominator = n + z2
    center = (correct + z2 / 2) / denominator
    spread = z / denominator * sqrt(correct * (n - correct) / n + z2 / 4)
    return (max(0.0, center - spread), min(1.0, center + spread))


def _stat(correct: int, n: int) -> Stat:
    low, high = wilson_interval(correct, n)
    return Stat(
        correct=correct,
        n=n,
        accuracy=correct / n if n else 0.0,
        ci_low=low,
        ci_high=high,
    )


def load_run(path: Path | str) -> ModelRun:
    """Load one model's lm-eval output directory (the nested run subdir is searched too)."""
    root = Path(path)
    results_files = sorted(root.rglob("results_*.json"))
    if not results_files:
        raise ValueError(f"no lm-eval results_*.json under {root}")
    # Newest wins if a directory was written to more than once.
    results = json.loads(results_files[-1].read_text(encoding="utf-8")).get("results", {})

    pair_agreement = {
        task: float(values["pair_agreement,extract_answer"])
        for task, values in results.items()
        if "pair_agreement,extract_answer" in values
    }

    samples: dict[str, list[tuple[dict[str, object], float]]] = {}
    for sample_file in sorted(root.rglob("samples_*.jsonl")):
        # samples_<task>_<iso timestamp>.jsonl — the timestamp contains no underscores.
        task = sample_file.stem[len("samples_") :].rsplit("_", 1)[0]
        rows: list[tuple[dict[str, object], float]] = []
        with open(sample_file, encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                row = json.loads(line)
                rows.append((row["doc"], sample_correct(row)))
        samples[task] = rows

    return ModelRun(name=root.name, samples=samples, pair_agreement=pair_agreement)


def load_runs(results_dir: str) -> list[ModelRun]:
    """Load every run under `results_dir` that has per-sample logs, newest file per dir.

    Names each run the way `collect_results` does — from lm-eval config, falling back to the
    directory — so the markdown table and the statistics below it refer to the same model by
    the same name. Runs without `--log_samples` are skipped: they still appear in the table,
    but there is nothing per-item for the statistics to read.
    """
    root = Path(results_dir)
    if not root.is_dir():
        return []

    by_dir: dict[Path, list[Path]] = {}
    for found in root.rglob("results_*.json"):
        by_dir.setdefault(found.parent, []).append(found)

    runs: list[ModelRun] = []
    for run_dir in sorted(by_dir):
        if not any(run_dir.glob("samples_*.jsonl")):
            continue
        newest = max(by_dir[run_dir])
        try:
            payload = json.loads(newest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        config = payload.get("config", {})
        fallback = str(run_dir.relative_to(root))
        run = load_run(run_dir)
        name = _model_name(config if isinstance(config, dict) else {}, fallback=fallback)
        runs.append(ModelRun(name=name, samples=run.samples, pair_agreement=run.pair_agreement))
    return runs


def _mean_stderr(values: Sequence[float]) -> float | None:
    """Standard error of the mean, computed the way lm-eval does (sample stddev / sqrt n)."""
    n = len(values)
    if n < 2:
        return None
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / (n - 1)
    return sqrt(variance) / sqrt(n)


def rescore_table(
    runs: Sequence[RunResult], sampled: Sequence[ModelRun]
) -> tuple[list[RunResult], list[str]]:
    """Replace the table's exact_match wherever re-scored samples say otherwise.

    Returns the updated rows and one note per changed cell, so the report says out loud
    which numbers differ from the results file lm-eval wrote.
    """
    by_name = {run.name: run for run in sampled}
    out: list[RunResult] = []
    notes: list[str] = []
    for run in runs:
        recorded = run.metrics.get("exact_match")
        model_run = by_name.get(run.model)
        rows = model_run.samples.get(run.task) if model_run else None
        if recorded is None or not rows:
            out.append(run)
            continue
        values = [correct for _, correct in rows]
        value = sum(values) / len(values)
        if abs(value - recorded[0]) < 1e-9:
            out.append(run)
            continue
        metrics = {**run.metrics, "exact_match": (value, _mean_stderr(values))}
        out.append(RunResult(model=run.model, task=run.task, source=run.source, metrics=metrics))
        notes.append(f"{run.model} / {run.task}: exact_match {recorded[0]:.3f} -> {value:.3f}")
    return out, notes


def task_stat(run: ModelRun, task: str) -> Stat:
    rows = run.samples.get(task, [])
    return _stat(sum(int(correct) for _, correct in rows), len(rows))


def stat_by(run: ModelRun, task: str, key: str) -> dict[str, Stat]:
    """Group a task's samples by a field of the item (`script`, `difficulty`, `category`).

    Items whose value is missing or null are skipped rather than bucketed under "None" —
    difficulty in particular is optional, and an untagged item belongs to no tier.
    """
    buckets: dict[str, list[float]] = defaultdict(list)
    for doc, correct in run.samples.get(task, []):
        value = doc.get(key)
        if value is None:
            continue
        buckets[str(value)].append(correct)
    return {
        name: _stat(sum(int(c) for c in values), len(values))
        for name, values in sorted(buckets.items())
    }


def rankable(a: Stat, b: Stat) -> bool:
    """True when the two confidence intervals are disjoint, i.e. the ordering is real."""
    return a.ci_high < b.ci_low or b.ci_high < a.ci_low


def _pct(value: float) -> str:
    return f"{value:6.3f}"


def format_analysis(runs: Sequence[ModelRun]) -> str:
    if not runs:
        return "no runs to report\n"

    lines: list[str] = []
    width = max(len(run.name) for run in runs)
    tasks = sorted({task for run in runs for task in run.samples})

    for task in tasks:
        lines.append(f"\n{task}")
        stats = {run.name: task_stat(run, task) for run in runs if task in run.samples}
        for name, stat in stats.items():
            lines.append(
                f"  {name:<{width}}  acc {_pct(stat.accuracy)}"
                f"  95% CI [{_pct(stat.ci_low)}, {_pct(stat.ci_high)}]  n={stat.n}"
            )

        ordered = sorted(stats.items(), key=lambda kv: kv[1].accuracy)
        if len(ordered) >= 2:
            (low_name, low), (high_name, high) = ordered[0], ordered[-1]
            spread = high.accuracy - low.accuracy
            lines.append(f"  spread {high_name} - {low_name} = {spread:+.3f}")
            if not rankable(low, high):
                lines.append(
                    f"  ! confidence intervals overlap — n={high.n} cannot rank "
                    f"{high_name} above {low_name}"
                )

        for run in runs:
            if task not in run.samples:
                continue
            for category, stat in stat_by(run, task, "category").items():
                if stat.n < MIN_USABLE_N:
                    lines.append(
                        f"  ! {run.name}: category {category} has n={stat.n} "
                        f"(< {MIN_USABLE_N}) — no usable estimate"
                    )

        if task == _PAIRED_TASK:
            lines.extend(_format_pair_task(runs, task, width))

    return "\n".join(lines) + "\n"


def _format_pair_task(runs: Sequence[ModelRun], task: str, width: int) -> list[str]:
    lines: list[str] = []
    for run in runs:
        if task not in run.samples:
            continue
        by_script = stat_by(run, task, "script")
        latin = by_script.get("latin")
        cyrillic = by_script.get("cyrillic")
        lines.append(f"  {run.name}:")
        for script, stat in by_script.items():
            lines.append(f"    accuracy ({script:<9}) {_pct(stat.accuracy)}  n={stat.n}")
        if latin and cyrillic:
            lines.append(
                f"    script gap             {cyrillic.accuracy - latin.accuracy:+.3f}"
                "  (cyrillic - latin)"
            )
        agreement = run.pair_agreement.get(task)
        if agreement is not None:
            lines.append(f"    pair_agreement         {_pct(agreement)}")

        by_tier = _script_gap_by_difficulty(run, task)
        if by_tier:
            lines.append("    script gap by difficulty:")
            for tier, gap in by_tier:
                lines.append(f"      {tier:<8} {gap:+.3f}")
    return lines


def _script_gap_by_difficulty(run: ModelRun, task: str) -> list[tuple[str, float]]:
    """Cyrillic-minus-latin accuracy per difficulty tier — widening gap is the finding."""
    buckets: dict[tuple[str, str], list[float]] = defaultdict(list)
    for doc, correct in run.samples.get(task, []):
        tier, script = doc.get("difficulty"), doc.get("script")
        if tier is None or script is None:
            continue
        buckets[(str(tier), str(script))].append(correct)

    gaps: list[tuple[str, float]] = []
    tiers = sorted({tier for tier, _ in buckets}, key=["easy", "medium", "hard"].index)
    for tier in tiers:
        latin = buckets.get((tier, "latin"), [])
        cyrillic = buckets.get((tier, "cyrillic"), [])
        if latin and cyrillic:
            gaps.append((tier, sum(cyrillic) / len(cyrillic) - sum(latin) / len(latin)))
    return gaps
