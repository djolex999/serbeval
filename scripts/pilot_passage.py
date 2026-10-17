#!/usr/bin/env python
"""v2 pilot, format A: multi-error passage correction on a few models via OpenRouter.

    OPENROUTER_API_KEY=... PYTHONPATH=src python scripts/pilot_passage.py run
    PYTHONPATH=src python scripts/pilot_passage.py report

`run` sends every passage in data/v2_pilot/passages.jsonl to each model (one thread per
model, requests within a model one at a time) and appends raw answers to
results/v2_pilot/<model>.jsonl, skipping passages already answered. `report` scores them.
"""

import json
import sys
import threading
from pathlib import Path

import requests

from serbeval.lm_eval_anthropic import post_with_patience
from serbeval.lm_eval_openrouter import (
    OPENROUTER_URL,
    build_openrouter_payload,
    openrouter_api_key,
    text_from_chat,
)
from serbeval.passage import extract_passage, parse_markup, score_passage

ROOT = Path(__file__).resolve().parent.parent
ITEMS = ROOT / "data" / "v2_pilot" / "passages.jsonl"
OUT = ROOT / "results" / "v2_pilot"

# Same routing as each model's official-set run.
MODELS = {
    "anthropic/claude-opus-5.5": {"reasoning": "minimal"},
    "openai/gpt-6-sol": {},
    "deepseek/deepseek-v4-pro": {"provider": "StreamLake", "quantizations": "fp8"},
    "google/gemma-4-31b-it": {"quantizations": "bf16"},
}

PROMPT = (
    "Sledeći tekst može sadržati pravopisne i gramatičke greške, a može biti i potpuno "
    "ispravan. Ispravi sve greške i ne menjaj ništa drugo: ne menjaj reči koje su "
    "ispravne, red reči ni pismo. Ako je tekst ispravan, prepiši ga bez izmena.\n\n"
    "Tekst: {text}\n\n"
    "Odgovori u obliku:\n"
    "Ispravljeno: <ceo tekst>"
)


def _items() -> list[dict[str, str]]:
    return [json.loads(line) for line in ITEMS.read_text(encoding="utf-8").splitlines() if line]


def _path(model: str) -> Path:
    return OUT / (model.replace("/", "_") + ".jsonl")


def _run_model(model: str, items: list[dict[str, str]], key: str) -> None:
    path = _path(model)
    done = set()
    if path.exists():
        done = {json.loads(line)["id"] for line in path.read_text(encoding="utf-8").splitlines()}
    args = MODELS[model]
    headers = {"Authorization": f"Bearer {key}", "X-Title": "serbeval"}
    for item in items:
        if item["id"] in done:
            continue
        source = parse_markup(item["markup"]).source
        payload = build_openrouter_payload(
            messages=[{"role": "user", "content": PROMPT.format(text=source)}],
            model=model, max_tokens=600, stop=[], **args,
        )
        body = post_with_patience(requests.post, OPENROUTER_URL, payload, headers)
        record = {"id": item["id"], "raw": text_from_chat(body),
                  "provider": body.get("provider"), "usage": body.get("usage")}
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"done: {model}", flush=True)


def run() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    key = openrouter_api_key()
    items = _items()
    threads = [threading.Thread(target=_run_model, args=(m, items, key)) for m in MODELS]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


def report() -> None:
    items = {i["id"]: i for i in _items()}
    print("| Model | Passage exact | Error passages exact | Clean left intact | Recall | "
          "Precision | False alarms | Unparsed |")
    print("|---|---|---|---|---|---|---|---|")
    for model in MODELS:
        path = _path(model)
        if not path.exists():
            continue
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        tp = fp = fn = exact = err_exact = err_n = clean_ok = clean_n = unparsed = 0
        for row in rows:
            passage = parse_markup(items[row["id"]]["markup"])
            s = score_passage(extract_passage(row["raw"]), passage)
            tp, fp, fn = tp + s.true_pos, fp + s.false_pos, fn + s.false_neg
            exact += s.exact
            unparsed += s.unparsed
            if any(not site.free for site in passage.sites):
                err_n += 1
                err_exact += s.exact
            else:
                clean_n += 1
                clean_ok += s.exact
        n = len(rows)
        recall = tp / (tp + fn) if tp + fn else 0.0
        precision = tp / (tp + fp) if tp + fp else 0.0
        print(f"| {model} | {exact}/{n} | {err_exact}/{err_n} | {clean_ok}/{clean_n} | "
              f"{recall:.0%} ({tp}/{tp + fn}) | {precision:.0%} | {fp} | {unparsed} |")


if __name__ == "__main__":
    {"run": run, "report": report}[sys.argv[1] if len(sys.argv) > 1 else "report"]()
