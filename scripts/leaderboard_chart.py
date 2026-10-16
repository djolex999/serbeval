#!/usr/bin/env python
"""Render the official leaderboard as a PNG (results/leaderboard.png), sized for social posts.

Reads the same results as scripts/leaderboard.py. Needs matplotlib, which is not a
project dependency; run it with any Python that has it:

    python3 scripts/leaderboard_chart.py [results/official] [out.png]
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from leaderboard import GROUPS, merged_results, metric

NAMES = {
    "anthropic_claude-opus-5.5": "Claude Opus 5.5",
    "google_gemini-3.8-flash": "Gemini 3.8 Flash",
    "openai_gpt-5.6-sol": "GPT-5.6 Sol",
    "anthropic_claude-sonnet-5.5": "Claude Sonnet 5.5",
    "x-ai_grok-4.7": "Grok 4.7",
    "google_gemini-3.5-flash-lite": "Gemini 3.5 Flash-Lite",
    "openai_gpt-5.6-luna": "GPT-5.6 Luna",
    "moonshotai_kimi-k3": "Kimi K3",
    "z-ai_glm-5.3": "GLM-5.3",
    "deepseek_deepseek-v4.1-flash": "DeepSeek V4.1 Flash",
    "google_gemma-4-31b-it": "Gemma 4 31B",
    "deepseek_deepseek-v3.2": "DeepSeek V3.2",
    "mistralai_mistral-large-4-0": "Mistral Large 4",
    "qwen_qwen3-235b-a22b-2507": "Qwen3 235B",
    "openai_gpt-5-mini": "GPT-5 mini",
    "anthropic_claude-haiku-5.5": "Claude Haiku 5.5",
    "meta-llama_llama-3.3-70b-instruct": "Llama 3.3 70B",
    "google_gemma-3-12b-it": "Gemma 3 12B",
    "qwen_qwen3.5-9b": "Qwen3.5 9B",
    "mistralai_mistral-nemo": "Mistral Nemo",
    "meta-llama_llama-3.1-8b-instruct": "Llama 3.1 8B",
    "cohere_command-a-plus": "Command A+",
}

SURFACE = "#fcfcfb"
BAR = "#2a78d6"
TEXT = "#0b0b0b"
TEXT_2 = "#52514e"
MUTED = "#8a8984"
GRID = "#e8e7e3"


def scores(root: Path) -> list[tuple[str, float]]:
    tasks = {name: [f"{t}_official" for t in ts if not t.endswith(("_mined", "_synth"))]
             for name, ts in GROUPS.items()}
    every = [t for ts in tasks.values() for t in ts]
    rows = []
    for model_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        results = merged_results(model_dir)
        if not all(t in results for t in every):
            continue
        group = [sum(metric(results[t], "exact_match") for t in ts) / len(ts)
                 for ts in tasks.values()]
        rows.append((NAMES.get(model_dir.name, model_dir.name), 100 * sum(group) / len(group)))
    return sorted(rows, key=lambda r: r[1], reverse=True)


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "results/official")
    out = Path(sys.argv[2] if len(sys.argv) > 2 else "results/leaderboard.png")
    rows = scores(root)

    fig = plt.figure(figsize=(5.4, 6.75), dpi=200, facecolor=SURFACE)
    ax = fig.add_axes((0.30, 0.115, 0.62, 0.70), facecolor=SURFACE)
    n = len(rows)
    thickness = 0.62
    for i, (name, value) in enumerate(rows):
        y = n - 1 - i
        ax.add_patch(FancyBboxPatch(
            (0, y - thickness / 2), value, thickness,
            boxstyle="round,pad=0,rounding_size=0.18", mutation_aspect=1 / 9,
            facecolor=BAR, edgecolor="none", zorder=2,
        ))
        ax.text(value + 1.2, y, f"{value:.0f}%", va="center", ha="left",
                fontsize=7.2, color=TEXT, zorder=3)
        ax.text(-2, y, name, va="center", ha="right", fontsize=7.6, color=TEXT)

    ax.set_xlim(0, 108)
    ax.set_ylim(-0.7, n - 0.3)
    ax.set_yticks([])
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=6.6, color=MUTED)
    ax.tick_params(axis="x", length=0, pad=4)
    ax.grid(axis="x", color=GRID, linewidth=0.6, zorder=0)
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(False)

    fig.text(0.06, 0.945, "How well do LLMs write Serbian?", fontsize=13.5,
             fontweight="bold", color=TEXT, ha="left")
    fig.text(0.06, 0.912, "serbeval: grammar, verb forms, ijekavian, orthography, č/ć",
             fontsize=8.2, color=TEXT_2, ha="left")
    fig.text(0.06, 0.888, f"{n} models · 355 checked tasks · average accuracy, zero-shot",
             fontsize=8.2, color=TEXT_2, ha="left")
    fig.text(0.06, 0.045, "github.com/djolex999/serbeval", fontsize=7.6, color=TEXT_2, ha="left")
    fig.text(0.94, 0.045, "October 2026", fontsize=7.6, color=MUTED, ha="right")

    fig.savefig(out, dpi=200, facecolor=SURFACE)
    print(f"OK: {out} ({n} models)")


if __name__ == "__main__":
    main()
