#!/usr/bin/env python
"""Render the official leaderboard as a PNG (results/leaderboard.png), sized for social posts.

Reads the same results as scripts/leaderboard.py. Needs matplotlib, which is not a
project dependency; run it with any Python that has it:

    python3 scripts/leaderboard_chart.py [results/official] [out.png]
    python3 scripts/leaderboard_chart.py --open-weights   # -> results/leaderboard-open.png
    python3 scripts/leaderboard_chart.py --reasoning      # -> results/reasoning-compare.png
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
    "openai_gpt-6.1-sol": "GPT-6.1 Sol",
    "openai_gpt-6-sol": "GPT-6 Sol",
    "openai_gpt-6-luna": "GPT-6 Luna",
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
    "nvidia_nemotron-3-ultra-550b-a55b": "Nemotron 3 Ultra",
    "nvidia_nemotron-3.5-lightning": "Nemotron 3.5 Lightning",
    "deepseek_deepseek-v4-pro": "DeepSeek V4 Pro",
    "qwen_qwen3.6-27b": "Qwen3.6 27B",
    "minimax_minimax-m3": "MiniMax M3",
}

# Weights published on Hugging Face (license tag checked 2026-10-16). Mistral Large 4 is
# left out until its weights are actually released (announced for late October 2026).
OPEN_WEIGHTS = {
    "moonshotai_kimi-k3", "z-ai_glm-5.3", "deepseek_deepseek-v4.1-flash", "deepseek_deepseek-v4-pro",
    "deepseek_deepseek-v3.2", "google_gemma-4-31b-it", "google_gemma-3-12b-it",
    "qwen_qwen3-235b-a22b-2507", "qwen_qwen3.5-9b", "qwen_qwen3.6-27b",
    "meta-llama_llama-3.3-70b-instruct", "meta-llama_llama-3.1-8b-instruct",
    "mistralai_mistral-nemo", "cohere_command-a-plus", "minimax_minimax-m3",
    "nvidia_nemotron-3-ultra-550b-a55b", "nvidia_nemotron-3.5-lightning",
}

SURFACE = "#fcfcfb"
BAR = "#2a78d6"
BAR_LOW = "#8fb8ea"
BAR_ON = "#e0882b"
TEXT = "#0b0b0b"
TEXT_2 = "#52514e"
MUTED = "#8a8984"
GRID = "#e8e7e3"


def scores(root: Path, only: set[str] | None = None) -> list[tuple[str, float]]:
    tasks = {name: [f"{t}_official" for t in ts if not t.endswith(("_mined", "_synth"))]
             for name, ts in GROUPS.items()}
    every = [t for ts in tasks.values() for t in ts]
    rows = []
    for model_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        results = merged_results(model_dir)
        if only is not None and model_dir.name not in only:
            continue
        if not all(t in results for t in every):
            continue
        group = [sum(metric(results[t], "exact_match") for t in ts) / len(ts)
                 for ts in tasks.values()]
        rows.append((NAMES.get(model_dir.name, model_dir.name), 100 * sum(group) / len(group)))
    return sorted(rows, key=lambda r: r[1], reverse=True)


def compare(off_root: Path, out: Path) -> None:
    """Grouped bars: the same model, same provider, reasoning off / low / high."""
    # MiniMax M3 at reasoning=low left 17/355 answers empty, some from thinking through
    # the then 2048-token budget: that measures the budget, so its low bar is left out.
    excluded = {"MiniMax M3"}
    low = {n: v for n, v in scores(Path("results/official-reasoning")) if n not in excluded}
    high = dict(scores(Path("results/official-reasoning-high")))
    rows = [(name, (off, low.get(name), high[name]))
            for name, off in scores(off_root) if name in high]
    series = ((BAR, "reasoning off"), (BAR_LOW, "low"), (BAR_ON, "high"))
    fig = plt.figure(figsize=(5.4, 5.0), dpi=200, facecolor=SURFACE)
    ax = fig.add_axes((0.30, 0.12, 0.62, 0.63), facecolor=SURFACE)
    n = len(rows)
    for i, (name, values) in enumerate(rows):
        y = n - 1 - i
        for k, (value, (color, _)) in enumerate(zip(values, series, strict=True)):
            dy = 0.27 * (1 - k)
            if value is None:
                note = "excluded: empty answers" if name in excluded else "not run"
                ax.text(1.2, y + dy, note, va="center", ha="left", fontsize=6.6, color=MUTED)
                continue
            ax.barh(y + dy, value, height=0.25, color=color, zorder=2)
            ax.text(value + 1.2, y + dy, f"{value:.0f}%", va="center", ha="left",
                    fontsize=6.8, color=TEXT, zorder=3)
        ax.text(-2, y, name, va="center", ha="right", fontsize=7.6, color=TEXT)
    ax.set_xlim(0, 108)
    ax.set_ylim(-0.55, n - 0.45)
    ax.set_yticks([])
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=6.6, color=MUTED)
    ax.tick_params(axis="x", length=0, pad=4)
    ax.grid(axis="x", color=GRID, linewidth=0.6, zorder=0)
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(False)
    fig.text(0.06, 0.93, "Does thinking help with Serbian?", fontsize=12.5,
             fontweight="bold", color=TEXT, ha="left")
    fig.text(0.06, 0.885, "serbeval official set v1.2 (351 tasks), same provider and precision",
             fontsize=8.2, color=TEXT_2, ha="left")
    for x, (color, label) in zip((0.06, 0.30, 0.42), series, strict=True):
        fig.patches.append(FancyBboxPatch((x, 0.825), 0.02, 0.022, boxstyle="square,pad=0",
                                          transform=fig.transFigure, facecolor=color,
                                          edgecolor="none"))
        fig.text(x + 0.03, 0.836, label, fontsize=7.8, color=TEXT_2, va="center")
    fig.text(0.06, 0.04, "github.com/djolex999/serbeval", fontsize=7.6, color=TEXT_2, ha="left")
    fig.text(0.94, 0.04, "October 2026", fontsize=7.6, color=MUTED, ha="right")
    fig.savefig(out, dpi=200, facecolor=SURFACE)
    print(f"OK: {out} ({n} models)")


def main() -> None:
    if "--reasoning" in sys.argv:
        compare(Path("results/official"), Path("results/reasoning-compare.png"))
        return
    args = [a for a in sys.argv[1:] if a != "--open-weights"]
    open_only = len(args) < len(sys.argv) - 1
    root = Path(args[0] if args else "results/official")
    default_out = "results/leaderboard-open.png" if open_only else "results/leaderboard.png"
    out = Path(args[1] if len(args) > 1 else default_out)
    rows = scores(root, OPEN_WEIGHTS if open_only else None)

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

    title = ("How well do open-weight LLMs write Serbian?" if open_only
             else "How well do LLMs write Serbian?")
    fig.text(0.06, 0.945, title, fontsize=13.5 if not open_only else 12.5,
             fontweight="bold", color=TEXT, ha="left")
    fig.text(0.06, 0.912, "serbeval: grammar, verb forms, ijekavian, orthography, č/ć",
             fontsize=8.2, color=TEXT_2, ha="left")
    fig.text(0.06, 0.888, f"{n} {'open-weight ' if open_only else ''}models · 351 checked tasks · average accuracy, zero-shot",
             fontsize=8.2, color=TEXT_2, ha="left")
    fig.text(0.06, 0.045, "github.com/djolex999/serbeval", fontsize=7.6, color=TEXT_2, ha="left")
    fig.text(0.94, 0.045, "October 2026", fontsize=7.6, color=MUTED, ha="right")

    fig.savefig(out, dpi=200, facecolor=SURFACE)
    print(f"OK: {out} ({n} models)")


if __name__ == "__main__":
    main()
