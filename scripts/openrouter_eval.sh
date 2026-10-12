#!/usr/bin/env bash
# Run the full serbeval suite against one model through OpenRouter.
#
#   OPENROUTER_API_KEY=... scripts/openrouter_eval.sh google/gemma-3-12b-it
#   OPENROUTER_API_KEY=... scripts/openrouter_eval.sh anthropic/claude-opus-5.5 reasoning=low
#   OPENROUTER_API_KEY=... scripts/openrouter_eval.sh meta-llama/llama-3.3-70b-instruct provider=DeepInfra,quantizations=bf16
#
# Extra model_args (2nd argument) go straight to the `openrouter-chat` adapter.
# Reasoning is off by default; models that cannot disable it need reasoning=low.
# The log line "served by <provider>" is the provenance — keep it with the result.
# Output: results/openrouter/<model>/ (per-sample logs are gitignored).
set -euo pipefail

MODEL="${1:-}"
EXTRA="${2:-}"
LIMIT="${LIMIT:-}"
[ -n "$MODEL" ] || { echo "usage: OPENROUTER_API_KEY=... $0 <openrouter-model-id> [model_args]" >&2; exit 2; }
: "${OPENROUTER_API_KEY:?set OPENROUTER_API_KEY (read it with: read -rs OPENROUTER_API_KEY)}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
find_python() {
  [ -n "${PYTHON:-}" ] && { echo "$PYTHON"; return; }
  local dir="$ROOT"
  while [ "$dir" != "/" ]; do
    [ -x "$dir/.venv/bin/python" ] && { echo "$dir/.venv/bin/python"; return; }
    dir="$(dirname "$dir")"
  done
  echo "no .venv found above $ROOT; set PYTHON=/path/to/python" >&2; exit 1
}
PY="$(find_python)"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
cd "$ROOT"

# TASKS=srb_official RESULTS=results/official runs the official set instead.
TASKS="${TASKS:-srb_grammar,srb_idioms,srb_cyrillic_agreement,srb_grammar_cloze,srb_grammar_cloze_mined,srb_grammar_cloze_synth,srb_probe,srb_pravopis,srb_correction}"
OUT="$ROOT/${RESULTS:-results/openrouter}/$(echo "$MODEL" | tr ':/' '__')"
mkdir -p "$(dirname "$OUT")"
ARGS="model=$MODEL${EXTRA:+,$EXTRA}"
LIMIT_ARGS=()
[ -n "$LIMIT" ] && LIMIT_ARGS=(--limit "$LIMIT")

# One request at a time: lm-eval's concurrent path (aiohttp) broke on Kie, and the full
# suite is ~1400 short requests, so sequential is still minutes, not hours.
"$PY" scripts/run_eval.py --model openrouter-chat --model_args "$ARGS" \
  --apply_chat_template \
  --tasks "$TASKS" --include_path lm_eval_tasks \
  --output_path "$OUT" --log_samples "${LIMIT_ARGS[@]+"${LIMIT_ARGS[@]}"}" 2>&1 | tee "$OUT.log"

echo
grep -h "served by" "$OUT.log" | sort -u || true
"$PY" -m serbeval.cli report --results-dir "$OUT"
