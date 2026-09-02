"""serbeval command-line interface."""

import argparse
import sys
from collections.abc import Sequence

from serbeval.data import load_items, validate_dataset
from serbeval.schema import ClozeItem, EvalItem

DEFAULT_DATA_DIR = "data"


def _is_cloze_file(path: str) -> bool:
    """Cloze and MCQ datasets share the .jsonl name, so detect by shape, not by path."""
    import json

    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    return "answers" in json.loads(line)
    except (OSError, json.JSONDecodeError):
        return False
    return False


def _cmd_validate(args: argparse.Namespace) -> int:
    if _is_cloze_file(args.path):
        from serbeval.data import load_cloze_items, validate_cloze_dataset

        try:
            cloze_items = load_cloze_items(args.path)
        except (OSError, ValueError) as exc:
            print(f"FAIL: {exc}")
            return 1
        cloze_problems = validate_cloze_dataset(cloze_items)
        if cloze_problems:
            for problem in cloze_problems:
                print(problem)
            print(f"FAIL: {len(cloze_problems)} problem(s) in {len(cloze_items)} item(s)")
            return 1
        print(f"OK: {len(cloze_items)} cloze item(s)")
        return 0

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


def _cmd_mine(args: argparse.Namespace) -> int:
    """Mine cloze candidates from an annotated corpus — no API key, no model authorship."""
    from pathlib import Path

    from serbeval.conllu import load_conllu
    from serbeval.data import save_cloze_items
    from serbeval.mine import mine_cloze_items

    try:
        sentences = load_conllu(args.conllu)
    except OSError as exc:
        print(f"FAIL: {exc}")
        return 1

    items = mine_cloze_items(
        sentences, min_purity=args.min_purity, min_count=args.min_count, limit=args.n
    )
    out = Path(args.data_dir) / args.task / "candidates.jsonl"
    save_cloze_items(items, out)
    print(f"OK: wrote {len(items)} candidate(s) to {out}")
    print("     unverified — a human must spot-check before merging into items.jsonl")
    return 0


def _cmd_synth(args: argparse.Namespace) -> int:
    """Generate cloze items from authored frames + an inflectional lexicon."""
    from pathlib import Path

    from serbeval.data import save_cloze_items
    from serbeval.lexicon import load_lexicon
    from serbeval.synth import LEMMA_CLASSES, synthesize_items

    wanted = {lemma for lemmas in LEMMA_CLASSES.values() for lemma in lemmas}
    try:
        lexicon = load_lexicon(args.lexicon, upos="NOUN", lemmas=wanted)
    except OSError as exc:
        print(f"FAIL: {exc}")
        return 1

    absent = wanted - lexicon.lemmas()
    if absent:
        print(f"WARNING: lexicon has no NOUN entry for: {', '.join(sorted(absent))}")

    items = synthesize_items(lexicon, limit=args.n, seed=args.seed)
    out = Path(args.out) if args.out else Path(args.data_dir) / args.task / "candidates-synth.jsonl"
    save_cloze_items(items, out)
    print(f"OK: wrote {len(items)} candidate(s) to {out}")
    print("     novel sentences — never published, so not in any training set")
    print("     unverified: check the FRAMES, not every item")
    return 0


def _cmd_index(args: argparse.Namespace) -> int:
    """Condense a full lexicon into the one column `check` needs."""
    from serbeval.check import forms_from_lexicon, write_form_index

    try:
        forms = forms_from_lexicon(args.lexicon)
    except OSError as exc:
        print(f"FAIL: {exc}")
        return 1
    write_form_index(forms, args.out)
    print(f"OK: {len(forms)} form(s) -> {args.out}")
    return 0


def _cmd_check(args: argparse.Namespace) -> int:
    """Advisory, like `lint`: reports language problems, never fails the caller."""
    import sys as _sys

    from serbeval.check import check_text, load_form_index

    try:
        index = load_form_index(args.index)
    except OSError as exc:
        print(f"FAIL: {exc} (build one with `serbeval index`)")
        return 1

    total = 0
    for path in args.paths or ["-"]:
        if path == "-":
            text = _sys.stdin.read()
        else:
            with open(path, encoding="utf-8") as handle:
                text = handle.read()
        findings = [f for f in check_text(text, index) if f.kind not in args.ignore]
        label = "<stdin>" if path == "-" else path
        for finding in findings:
            where = f"{label}:{finding.line}:{finding.column}" if finding.line else label
            print(f"{where}: {finding.kind}: {finding.message}")
        total += len(findings)

    print(f"{total} finding(s)" if total else "OK: no language problems found")
    return 0


def _load_pool(data_dir: str) -> "list[EvalItem | ClozeItem]":
    """Every item across every task, MCQ and cloze alike."""
    import json
    from pathlib import Path

    from serbeval.data import load_cloze_items, load_items

    pool: list[EvalItem | ClozeItem] = []
    for path in sorted(Path(data_dir).glob("*/items.jsonl")):
        with open(path, encoding="utf-8") as fh:
            first = next((line for line in fh if line.strip()), "")
        if not first:
            continue
        is_cloze = "answers" in json.loads(first)
        pool.extend(load_cloze_items(path) if is_cloze else load_items(path))
    return pool


def _cmd_baseline(args: argparse.Namespace) -> int:
    """Build or score a human-baseline worksheet.

    This is the control that separates "the model is weak" from "the items are broken".
    Without it a low score is ambiguous and no model comparison means anything.
    """
    from pathlib import Path

    from serbeval.baseline import build_worksheet, sample_items, score_worksheet

    pool = _load_pool(args.data_dir)
    if not pool:
        print(f"FAIL: no items under {args.data_dir}")
        return 1

    if args.new:
        items = sample_items(pool, n=args.n, seed=args.seed)
        Path(args.out).write_text(build_worksheet(items), encoding="utf-8")
        print(f"OK: {len(items)} item(s) -> {args.out}")
        print("     popuni ODGOVOR: linije, pa: serbeval baseline --score " + args.out)
        return 0

    text = Path(args.score).read_text(encoding="utf-8")
    by_id = {item.id: item for item in pool}
    from serbeval.baseline import parse_worksheet

    answered_ids = parse_worksheet(text)
    items = [by_id[i] for i in answered_ids if i in by_id]
    result = score_worksheet(text, items)
    print(f"{result.correct}/{result.answered} tačno ({result.accuracy:.0%})")
    if result.wrong:
        print("\nPromašeni itemi — proveri JESU LI ONI TAČNI, ne ti:")
        for item_id in result.wrong:
            print(f"  {item_id}")
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

    mine = sub.add_parser("mine", help="mine cloze candidates from a CoNLL-U corpus")
    mine.add_argument("--conllu", required=True, help="path to an annotated .conllu file")
    mine.add_argument("--task", default="srb_grammar_cloze")
    mine.add_argument("-n", type=int, default=None, help="cap on candidates produced")
    mine.add_argument("--min-purity", type=float, default=0.95)
    mine.add_argument("--min-count", type=int, default=20)
    mine.add_argument("--data-dir", default=DEFAULT_DATA_DIR)
    mine.set_defaults(func=_cmd_mine)

    synth = sub.add_parser("synth", help="generate cloze items from frames + a lexicon")
    synth.add_argument("--lexicon", required=True, help="srLex-format .tsv or .gz")
    synth.add_argument("--task", default="srb_grammar_cloze")
    synth.add_argument("-n", type=int, default=None, help="cap on items produced")
    synth.add_argument("--seed", type=int, default=0)
    synth.add_argument("--out", default=None)
    synth.add_argument("--data-dir", default=DEFAULT_DATA_DIR)
    synth.set_defaults(func=_cmd_synth)

    index = sub.add_parser("index", help="build the form index `check` uses")
    index.add_argument("--lexicon", required=True, help="srLex-format .tsv or .gz")
    index.add_argument("--out", default="data/forms.txt.gz")
    index.set_defaults(func=_cmd_index)

    check = sub.add_parser("check", help="find Serbian language errors in generated text")
    check.add_argument("paths", nargs="*", help="files to check (default: stdin)")
    check.add_argument("--index", default="data/forms.txt.gz")
    check.add_argument(
        "--ignore", nargs="*", default=[], help="finding kinds to suppress"
    )
    check.set_defaults(func=_cmd_check)

    baseline = sub.add_parser("baseline", help="human baseline worksheet: build or score")
    group = baseline.add_mutually_exclusive_group(required=True)
    group.add_argument("--new", action="store_true", help="build a worksheet")
    group.add_argument("--score", metavar="FILE", help="score a filled worksheet")
    baseline.add_argument("-n", type=int, default=30)
    baseline.add_argument("--seed", type=int, default=0)
    baseline.add_argument("--out", default="baseline.txt")
    baseline.add_argument("--data-dir", default=DEFAULT_DATA_DIR)
    baseline.set_defaults(func=_cmd_baseline)

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
