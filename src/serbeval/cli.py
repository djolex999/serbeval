"""serbeval command-line interface."""

import argparse
import sys
from collections.abc import Sequence

from serbeval.data import load_items, validate_dataset


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="serbeval")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="validate a dataset JSONL file")
    validate.add_argument("path", help="path to items.jsonl")
    validate.set_defaults(func=_cmd_validate)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result: int = args.func(args)
    return result


if __name__ == "__main__":
    sys.exit(main())
