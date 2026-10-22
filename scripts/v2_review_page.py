#!/usr/bin/env python
"""Write the offline review page for v2 passages (default: both drafts -> tasks/v2-pregled.html).

    PYTHONPATH=src python scripts/v2_review_page.py [out.html] [passages.jsonl ...]

The page's "Preuzmi ocene" download is read by serbeval.passage_review.parse_passage_review.
"""

import json
import sys
from pathlib import Path

from serbeval.passage_review import build_passage_review_html, review_rows

ROOT = Path(__file__).resolve().parent.parent
DEFAULT = [ROOT / "data" / "v2" / "passages-draft.jsonl", ROOT / "data" / "v2" / "passages-gov-draft.jsonl"]


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "tasks" / "v2-pregled.html"
    sources = [Path(p) for p in sys.argv[2:]] or DEFAULT
    rows = [json.loads(line) for src in sources
            for line in src.read_text(encoding="utf-8").splitlines() if line.strip()]
    out.write_text(build_passage_review_html(review_rows(rows), title="serbeval-v2-pregled"),
                   encoding="utf-8")
    print(f"OK: {len(rows)} passages -> {out}")


if __name__ == "__main__":
    main()
