"""serbeval command-line interface."""

import argparse
import sys
from collections.abc import Sequence

from serbeval.data import load_items, validate_dataset

DEFAULT_DATA_DIR = "data"


def _cmd_validate(args: argparse.Namespace) -> int:
    try:
        items = load_items(args.path)
    except (OSError, ValueError) as exc:
        print(f"FAIL: {exc}")
        return 1
    problems = validate_dataset(items)
    if problems:
        for problem in problems:
            print(problem)
        print(f"FAIL: {len(problems)} problem(s) in {len(items)} item(s)")
        return 1
    print(f"OK: {len(items)} item(s)")
    return 0


def _cmd_lint(args: argparse.Namespace) -> int:
    """Advisory: always exits 0 unless the file itself is unreadable.

    Quality is a judgement call, so lint reports and lets the maintainer decide. Only
    `validate` gates on well-formedness.
    """
    from serbeval.lint import lint_items

    try:
        items = load_items(args.path)
    except (OSError, ValueError) as exc:
        print(f"FAIL: {exc}")
        return 1

    reports = [r for r in lint_items(items) if r.score < 1.0 or r.flags]
    if not reports:
        print(f"OK: no weak items in {len(items)} item(s)")
        return 0

    print(f"WEAK ITEMS ({len(reports)} of {len(items)})\n")
    for report in reports[: args.limit]:
        flags = f"  [{', '.join(report.flags)}]" if report.flags else ""
        print(f"  {report.item_id}    score {report.score:.2f}  ({report.shape}){flags}")
        for verdict in report.verdicts:
            if verdict.verdict in ("minimal-pair", "n/a"):
                continue
            print(f"      {verdict.letter}. {verdict.text}")
            print(f"         → {verdict.verdict}: {verdict.reason}")
        print()

    if len(reports) > args.limit:
        print(f"  ... {len(reports) - args.limit} more (use --limit to show)")
    print("advisory only — exit 0")
    return 0


def _make_client() -> object:
    import anthropic

    return anthropic.Anthropic()


def _cmd_generate(args: argparse.Namespace) -> int:
    from serbeval.generate import run_generate

    client = _make_client()
    written = run_generate(
        client,  # type: ignore[arg-type]
        task=args.task,
        category=args.category,
        n=args.n,
        model=args.model,
        data_dir=args.data_dir,
    )
    print(f"OK: wrote {written} new candidate(s) to {args.data_dir}/{args.task}/candidates.jsonl")
    return 0


def _cmd_selfcheck(args: argparse.Namespace) -> int:
    from serbeval.selfcheck import run_selfcheck

    client = _make_client()
    summary = run_selfcheck(
        client,  # type: ignore[arg-type]
        task=args.task,
        runs=args.runs,
        model=args.model,
        data_dir=args.data_dir,
    )
    print(f"OK: kept {summary['kept']}, discarded {summary['discarded']}")
    return 0


def _cmd_review(args: argparse.Namespace) -> int:
    from serbeval.review import run_review

    summary = run_review(task=args.task, data_dir=args.data_dir)
    print(
        f"OK: verified {summary['verified']}, rejected {summary['rejected']}, "
        f"skipped {summary['skipped']}, remaining {summary['remaining']}"
    )
    return 0


def _cmd_stats(args: argparse.Namespace) -> int:
    from serbeval.stats import collect_stats, format_stats

    print(format_stats(collect_stats(args.data_dir)))
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    """Markdown metrics table, followed by the statistics when per-sample logs exist.

    The table alone invites ranking models that the item count cannot separate, so any run
    with `--log_samples` also gets confidence intervals and an explicit rankability verdict.
    """
    from serbeval.report import collect_results, format_analysis, format_markdown, load_runs

    runs, warnings = collect_results(args.results_dir)
    for warning in warnings:
        print(f"WARNING: {warning}")

    text = format_markdown(runs)
    sampled = load_runs(args.results_dir)
    if sampled:
        text += "\n" + format_analysis(sampled)
    elif runs:
        text += "\n\nNo per-sample logs found — re-run with --log_samples for confidence\n"
        text += "intervals and the script/difficulty breakdown.\n"

    if args.out is not None:
        from pathlib import Path

        Path(args.out).write_text(text + "\n", encoding="utf-8")
        print(f"OK: wrote {args.out}")
    else:
        print(text)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="serbeval")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="validate a dataset JSONL file")
    validate.add_argument("path", help="path to items.jsonl")
    validate.set_defaults(func=_cmd_validate)

    lint = sub.add_parser("lint", help="advisory distractor-quality report (never fails)")
    lint.add_argument("path", help="path to items.jsonl")
    lint.add_argument("--limit", type=int, default=20, help="how many weak items to print")
    lint.set_defaults(func=_cmd_lint)

    from serbeval.generate import DEFAULT_MODEL

    generate = sub.add_parser("generate", help="author candidate items via Claude")
    generate.add_argument("--task", required=True)
    generate.add_argument("--category", required=True)
    generate.add_argument("-n", type=int, default=10, help="number of candidates to request")
    generate.add_argument("--model", default=DEFAULT_MODEL)
    generate.add_argument("--data-dir", default=DEFAULT_DATA_DIR)
    generate.set_defaults(func=_cmd_generate)

    selfcheck = sub.add_parser("selfcheck", help="self-consistency filter on candidates")
    selfcheck.add_argument("--task", required=True)
    selfcheck.add_argument("--runs", type=int, default=3)
    selfcheck.add_argument("--model", default=DEFAULT_MODEL)
    selfcheck.add_argument("--data-dir", default=DEFAULT_DATA_DIR)
    selfcheck.set_defaults(func=_cmd_selfcheck)

    review = sub.add_parser("review", help="interactively verify unverified items")
    review.add_argument("--task", required=True)
    review.add_argument("--data-dir", default=DEFAULT_DATA_DIR)
    review.set_defaults(func=_cmd_review)

    stats = sub.add_parser("stats", help="dataset composition and verification progress")
    stats.add_argument("--data-dir", default=DEFAULT_DATA_DIR)
    stats.set_defaults(func=_cmd_stats)

    report = sub.add_parser("report", help="lm-eval results table + confidence intervals")
    report.add_argument("--results-dir", default="results")
    report.add_argument("--out", default=None, help="write to file instead of stdout")
    report.set_defaults(func=_cmd_report)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result: int = args.func(args)
    return result


if __name__ == "__main__":
    sys.exit(main())
