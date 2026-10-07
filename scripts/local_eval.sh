#!/usr/bin/env bash
# Run serbeval against a local open-weights model served by Ollama.
#
#   scripts/local_eval.sh qwen2.5:7b          # 50 items per core task; probe/pravopis/correction in full
#   scripts/local_eval.sh qwen2.5:7b 10       # quicker look
#
# Free and first-party (the weights run here), but QUANTIZED — say which quantization when
# quoting a number, and remember items are unverified: these are preliminary results.
# Output: results/local/<model>/ (per-sample logs are gitignored).
set -euo pipefail

MODEL="${1:-}"
LIMIT="${2:-50}"
[ -n "$MODEL" ] || { echo "usage: $0 <ollama-model> [limit]" >&2; exit 2; }
OLLAMA="${OLLAMA_URL:-http://localhost:11434}"
curl -sf -m 5 "$OLLAMA/api/version" >/dev/null || { echo "Ollama is not running at $OLLAMA" >&2; exit 1; }

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

TASKS=srb_grammar,srb_idioms,srb_cyrillic_agreement,srb_grammar_cloze,srb_grammar_cloze_mined,srb_grammar_cloze_synth,srb_probe,srb_pravopis,srb_correction
OUT="$ROOT/results/local/$(echo "$MODEL" | tr ':/' '__')"

# Extra generation fields go straight into the request body. Thinking models must have
# thinking off: qwen3 spends the whole 24-token cloze budget reasoning and returns "".
GEN_KWARGS="${GEN_KWARGS:-}"
case "$MODEL" in
  qwen3*|*deepseek-r1*) GEN_KWARGS="${GEN_KWARGS:-reasoning_effort=none}" ;;
esac
GEN_ARGS=()
[ -n "$GEN_KWARGS" ] && GEN_ARGS=(--gen_kwargs "$GEN_KWARGS")

# One request at a time: Ollama serves one generation at a time anyway, and lm-eval's
# concurrent path (aiohttp) is the one that broke on Kie.
"$PY" scripts/run_eval.py --model local-chat-completions \
  --model_args "model=$MODEL,base_url=$OLLAMA/v1/chat/completions,num_concurrent=1,max_retries=3,tokenized_requests=False" \
  --apply_chat_template "${GEN_ARGS[@]+"${GEN_ARGS[@]}"}" \
  --tasks "$TASKS" --include_path lm_eval_tasks \
  --output_path "$OUT" --log_samples --limit "$LIMIT"

echo
"$PY" -m serbeval.cli report --results-dir "$OUT"
