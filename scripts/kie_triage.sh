#!/usr/bin/env bash
# Item triage through Kie: claude-opus-5-5 + gpt-6-1-sol, then the review queue.
#
#   KIE_API_KEY=... scripts/kie_triage.sh smoke   # 3 items/task, under $0.10 — run this FIRST
#   KIE_API_KEY=... scripts/kie_triage.sh full    # 50 items/task (~230 items), ~$1-2 expected
#   KIE_API_KEY=... scripts/kie_triage.sh probe   # difficulty probe: 6 phenomena x 20 = 120 items
#   KIE_API_KEY=... scripts/kie_triage.sh pravopis  # pravopis set, ~80 items, Opus only
#
# TRIAGE ONLY. Kie is a reseller: which model actually served, and whether responses
# were cached, cannot be verified. Output lands in results/triage-kie/ (gitignored) and
# must never be reported as a benchmark score.
set -euo pipefail

MODE="${1:-}"
case "$MODE" in
  smoke) LIMIT=3 ;;
  full)  LIMIT=50 ;;
  probe) LIMIT=20 ;;
  pravopis) LIMIT=100 ;;
  *) echo "usage: KIE_API_KEY=... $0 smoke|full|probe|pravopis" >&2; exit 2 ;;
esac
: "${KIE_API_KEY:?set KIE_API_KEY (Kie dashboard -> API keys)}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# The venv may live above ROOT: inside a git worktree, ROOT is the worktree and the
# venv belongs to the main checkout. Walk up until one is found.
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
# Run against THIS checkout's code even if the venv's editable install points elsewhere.
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
OUT="$ROOT/results/triage-kie"
TASKS=srb_grammar,srb_idioms,srb_cyrillic_agreement,srb_grammar_cloze,srb_grammar_cloze_mined,srb_grammar_cloze_synth
if [ "$MODE" = probe ]; then
  # Separate output dir: the probe is a different question (which phenomena are hard),
  # and mixing it into the main triage results would blur both review queues.
  OUT="$ROOT/results/triage-kie-probe"
  TASKS=srb_probe
fi
if [ "$MODE" = pravopis ]; then
  OUT="$ROOT/results/triage-kie-pravopis"
  TASKS=srb_pravopis
fi
cd "$ROOT"

if [ "$MODE" = probe ]; then
  cat <<'EST'
Probe run: 120 cloze items per model (short answers).
  claude-opus-5-5  ~3k hidden Kie prompt/request  -> expected ~$0.10-0.30, worst ~$0.70
  gpt-6-1-sol      ~4.2k hidden prompt, effort=low -> expected ~$0.20-0.40
Expected total ~$0.30-0.70; worst case ~$1.10. Kie credits are prepaid, so the balance is a hard cap.
EST
  read -r -p "Proceed? [y/N] " ok
  [ "$ok" = y ] || { echo "aborted"; exit 1; }
fi

if [ "$MODE" = pravopis ]; then
  cat <<'EST'
Pravopis run: ~80 cloze items, claude-opus-5-5 ONLY (Kie's GPT endpoint returned 500 on most
probe requests). Expected ~$0.10-0.30, worst ~$0.50.
EST
  read -r -p "Proceed? [y/N] " ok
  [ "$ok" = y ] || { echo "aborted"; exit 1; }
fi

if [ "$MODE" = full ]; then
  cat <<'EST'
Full run: ~230 items per model.
  claude-opus-5-5  $1.60 / $8 per 1M   max_tokens floored at 2048  -> worst ~$3.80
  gpt-6-1-sol      $0.60 / $3 per 1M   effort=low, no token cap    -> expected ~$0.20-1.40
Expected total ~$1-2; worst case ~$5-6. Kie credits are prepaid, so the balance is a hard cap.
EST
  read -r -p "Proceed? [y/N] " ok
  [ "$ok" = y ] || { echo "aborted"; exit 1; }
fi

# Requests are sent one at a time on purpose. With num_concurrent > 1 lm-eval switches
# to aiohttp, which rejects Kie's JSON because Kie sends it with an EMPTY Content-Type
# ("unexpected mimetype"), and Kie answers 429 at just 4 parallel requests anyway.
echo "== claude-opus-5-5 =="
"$PY" scripts/run_eval.py --model anthropic-chat-fixed \
  --model_args "model=claude-opus-5-5,thinking=omit,effort=low,base_url=https://api.kie.ai/claude/v1/messages" \
  --tasks "$TASKS" --include_path lm_eval_tasks \
  --output_path "$OUT/opus-5-5" --log_samples --limit "$LIMIT"

if [ "$MODE" != pravopis ]; then
echo "== gpt-6-1-sol =="
"$PY" scripts/run_eval.py --model kie-responses \
  --model_args "model=gpt-6-1-sol,effort=low" \
  --tasks "$TASKS" --include_path lm_eval_tasks \
  --output_path "$OUT/gpt-6-1-sol" --log_samples --limit "$LIMIT"
fi

echo
echo "== unparsed check: near 0 means the plumbing works; near 1 means stop and report back =="
"$PY" -m serbeval.cli report --results-dir "$OUT" | grep -E "^\| .*\|" | head -40
echo
echo "== review queue =="
"$PY" -m serbeval.cli triage --results-dir "$OUT"
