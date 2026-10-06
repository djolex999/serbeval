#!/usr/bin/env bash
# Item triage through Kie: claude-opus-5-5 + gpt-6-1-sol, then the review queue.
#
#   KIE_API_KEY=... scripts/kie_triage.sh smoke   # 3 items/task, under $0.10 — run this FIRST
#   KIE_API_KEY=... scripts/kie_triage.sh full    # 50 items/task (~230 items), ~$1-2 expected
#
# TRIAGE ONLY. Kie is a reseller: which model actually served, and whether responses
# were cached, cannot be verified. Output lands in results/triage-kie/ (gitignored) and
# must never be reported as a benchmark score.
set -euo pipefail

MODE="${1:-}"
case "$MODE" in
  smoke) LIMIT=3 ;;
  full)  LIMIT=50 ;;
  *) echo "usage: KIE_API_KEY=... $0 smoke|full" >&2; exit 2 ;;
esac
: "${KIE_API_KEY:?set KIE_API_KEY (Kie dashboard -> API keys)}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="${PYTHON:-$ROOT/.venv/bin/python}"
OUT="$ROOT/results/triage-kie"
TASKS=srb_grammar,srb_idioms,srb_cyrillic_agreement,srb_grammar_cloze,srb_grammar_cloze_mined,srb_grammar_cloze_synth
cd "$ROOT"

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

echo "== claude-opus-5-5 =="
"$PY" scripts/run_eval.py --model anthropic-chat-fixed \
  --model_args "model=claude-opus-5-5,thinking=omit,effort=low,base_url=https://api.kie.ai/claude/v1/messages" \
  --tasks "$TASKS" --include_path lm_eval_tasks \
  --output_path "$OUT/opus-5-5" --log_samples --limit "$LIMIT"

echo "== gpt-6-1-sol =="
"$PY" scripts/run_eval.py --model kie-responses \
  --model_args "model=gpt-6-1-sol,effort=low" \
  --tasks "$TASKS" --include_path lm_eval_tasks \
  --output_path "$OUT/gpt-6-1-sol" --log_samples --limit "$LIMIT"

echo
echo "== unparsed check: near 0 means the plumbing works; near 1 means stop and report back =="
"$PY" -m serbeval.cli report --results-dir "$OUT" | grep -E "^\| .*\|" | head -40
echo
echo "== review queue =="
"$PY" -m serbeval.cli triage --results-dir "$OUT"
