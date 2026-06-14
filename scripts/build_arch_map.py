"""One-shot: inject serbeval's GRAPH_DATA into the codebase-architect HTML template."""

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = Path(
    "/Users/djmarkovic999/.claude/skills/codebase-architect/assets/template.html"
)
OUT = ROOT / "docs" / "architecture-map.html"
GENERATED_AT = "2026-06-14"

n_files = len(
    subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True
    ).stdout.splitlines()
)

GRAPH_DATA = {
    "meta": {
        "name": "serbeval",
        "type": "Python eval benchmark · lm-evaluation-harness 0.4.12",
        "generated": GENERATED_AT,
        "stats": {"files": n_files, "routes": 6, "services": 5},
    },
    "layers": {
        "routes": {
            "nodes": [
                {"id": "r1", "label": "serbeval (cli)", "type": "middleware",
                 "path": "src/serbeval/cli.py",
                 "detail": "argparse dispatch — the single console entrypoint.",
                 "deps": ["r2", "r3", "r4"]},
                {"id": "r2", "label": "validate", "type": "api",
                 "path": "src/serbeval/cli.py",
                 "detail": "Schema + integrity gate over a dataset JSONL. No network.",
                 "deps": []},
                {"id": "r3", "label": "generate", "type": "api",
                 "path": "src/serbeval/cli.py",
                 "detail": "Author candidate items via Claude → candidates.jsonl.",
                 "deps": []},
                {"id": "r4", "label": "selfcheck", "type": "api",
                 "path": "src/serbeval/cli.py",
                 "detail": "Re-answer candidates 3× and keep only unanimous-correct.",
                 "deps": []},
                {"id": "r5", "label": "srb_grammar", "type": "page",
                 "path": "lm_eval_tasks/srb_grammar.yaml",
                 "detail": "lm-eval task: 50 grammar MCQs (generate_until + regex).",
                 "deps": ["r8"]},
                {"id": "r6", "label": "srb_idioms", "type": "page",
                 "path": "lm_eval_tasks/srb_idioms.yaml",
                 "detail": "lm-eval task: 30 idiom-meaning MCQs.",
                 "deps": ["r8"]},
                {"id": "r7", "label": "srb_cyrillic_agreement", "type": "page",
                 "path": "lm_eval_tasks/srb_cyrillic_agreement.yaml",
                 "detail": "15 paired-script items; custom pair_agreement metric.",
                 "deps": ["r8"]},
                {"id": "r8", "label": "utils (task helpers)", "type": "layout",
                 "path": "lm_eval_tasks/utils.py",
                 "detail": "doc_to_text / doc_to_target / process_results / pair_agreement.",
                 "deps": []},
            ],
            "edges": [
                {"from": "r1", "to": "r2"}, {"from": "r1", "to": "r3"},
                {"from": "r1", "to": "r4"},
                {"from": "r5", "to": "r8", "label": "!function"},
                {"from": "r6", "to": "r8", "label": "!function"},
                {"from": "r7", "to": "r8", "label": "!function"},
            ],
        },
        "modules": {
            "nodes": [
                {"id": "m1", "label": "schema.py", "type": "module",
                 "path": "src/serbeval/schema.py",
                 "detail": "EvalItem (pydantic v2): 4 choices, A–D, validators.",
                 "deps": []},
                {"id": "m2", "label": "data.py", "type": "module",
                 "path": "src/serbeval/data.py",
                 "detail": "JSONL load/save + validate_dataset (ids, script, pairs).",
                 "deps": ["m1"]},
                {"id": "m3", "label": "translit.py", "type": "util",
                 "path": "src/serbeval/translit.py",
                 "detail": "Digraph-aware Latin→Cyrillic transliterator.",
                 "deps": []},
                {"id": "m4", "label": "generate.py", "type": "module",
                 "path": "src/serbeval/generate.py",
                 "detail": "Claude authoring + run_generate orchestration.",
                 "deps": ["m1", "m2"]},
                {"id": "m5", "label": "selfcheck.py", "type": "module",
                 "path": "src/serbeval/selfcheck.py",
                 "detail": "Self-consistency filter + run_selfcheck orchestration.",
                 "deps": ["m1", "m2"]},
                {"id": "m6", "label": "cli.py", "type": "module",
                 "path": "src/serbeval/cli.py",
                 "detail": "argparse; lazy Anthropic client so validate needs no key.",
                 "deps": ["m2", "m4", "m5"]},
                {"id": "m7", "label": "utils.py", "type": "util",
                 "path": "lm_eval_tasks/utils.py",
                 "detail": "Harness prompt + metric helpers (self-contained extraction).",
                 "deps": []},
                {"id": "m8", "label": "ingest_seed.py", "type": "util",
                 "path": "scripts/ingest_seed.py",
                 "detail": "Workflow result → items.jsonl (dedupe, script purity).",
                 "deps": ["m1", "m2"]},
                {"id": "m9", "label": "build_cyrillic_pairs.py", "type": "util",
                 "path": "scripts/build_cyrillic_pairs.py",
                 "detail": "Base facts → 15 transliterated pairs.",
                 "deps": ["m1", "m2", "m3"]},
                {"id": "m10", "label": "seed_workflow.js", "type": "util",
                 "path": "scripts/seed_workflow.js",
                 "detail": "Multi-agent author→verify→repair orchestrator.",
                 "deps": []},
            ],
            "edges": [
                {"from": "m2", "to": "m1", "label": "imports"},
                {"from": "m4", "to": "m1"}, {"from": "m4", "to": "m2"},
                {"from": "m5", "to": "m1"}, {"from": "m5", "to": "m2"},
                {"from": "m6", "to": "m2"}, {"from": "m6", "to": "m4"},
                {"from": "m6", "to": "m5"},
                {"from": "m8", "to": "m2"}, {"from": "m9", "to": "m3"},
                {"from": "m9", "to": "m2"},
            ],
        },
        "dataflow": {
            "nodes": [
                {"id": "d1", "label": "category authoring brief", "type": "input",
                 "detail": "Per-category Serbian spec (padezi, enklitike, idioms…).",
                 "deps": ["d2"]},
                {"id": "dx", "label": "Anthropic API", "type": "external",
                 "detail": "claude-opus-4-8 for authoring/selfcheck; model-under-test for eval.",
                 "deps": ["d2", "d4", "d8"]},
                {"id": "d2", "label": "Claude authoring", "type": "transform",
                 "detail": "generate.py / seed_workflow → candidate items.",
                 "deps": ["d3"]},
                {"id": "d3", "label": "candidates.jsonl", "type": "persist",
                 "detail": "Generated, unmerged. verified:false.",
                 "deps": ["d4"]},
                {"id": "d4", "label": "self-consistency 3×", "type": "transform",
                 "detail": "Re-answer 3×; keep unanimous-correct, else discard.",
                 "deps": ["d5", "d7"]},
                {"id": "d5", "label": "discarded.jsonl", "type": "persist",
                 "detail": "Rejects + reasons (selfcheck + workflow drops).",
                 "deps": []},
                {"id": "d6", "label": "human verification", "type": "input",
                 "detail": "Native speaker flips verified:true. PENDING — gate before publish.",
                 "deps": ["d7"]},
                {"id": "d7", "label": "items.jsonl", "type": "persist",
                 "detail": "Curated dataset (50+30+30). Currently all verified:false.",
                 "deps": ["d8"]},
                {"id": "d8", "label": "lm-eval harness", "type": "transform",
                 "detail": "doc_to_text → model → regex filter → metric.",
                 "deps": ["d9"]},
                {"id": "d9", "label": "results JSON", "type": "output",
                 "detail": "exact_match per task + pair_agreement (cyrillic).",
                 "deps": []},
            ],
            "edges": [
                {"from": "d1", "to": "d2"}, {"from": "dx", "to": "d2", "label": "messages.parse"},
                {"from": "d2", "to": "d3"}, {"from": "d3", "to": "d4"},
                {"from": "dx", "to": "d4", "label": "messages.create"},
                {"from": "d4", "to": "d5", "label": "rejects"},
                {"from": "d4", "to": "d7", "label": "survivors"},
                {"from": "d6", "to": "d7", "label": "verify"},
                {"from": "d7", "to": "d8", "label": "data_files"},
                {"from": "dx", "to": "d8", "label": "model-under-test"},
                {"from": "d8", "to": "d9"},
            ],
        },
        "services": {
            "nodes": [
                {"id": "s1", "label": "Anthropic API", "type": "ai",
                 "detail": "Authoring + selfcheck (opus) and model-under-test. NO KEY on dev machine.",
                 "deps": ["s2"]},
                {"id": "s2", "label": "lm-evaluation-harness", "type": "other",
                 "detail": "Pinned 0.4.12. Eval engine; anthropic-chat adapter.",
                 "deps": ["s3"]},
                {"id": "s3", "label": "HF datasets (json)", "type": "database",
                 "detail": "Loads data/<task>/items.jsonl via relative data_files.",
                 "deps": []},
                {"id": "s4", "label": "pydantic v2", "type": "other",
                 "detail": "EvalItem schema validation across all tooling.",
                 "deps": []},
                {"id": "s5", "label": "pytest · mypy · ruff", "type": "monitoring",
                 "detail": "Quality gates: 50 tests, strict typing, lint — all green.",
                 "deps": []},
            ],
            "edges": [
                {"from": "s1", "to": "s2", "label": "model under test"},
                {"from": "s2", "to": "s3", "label": "loads"},
            ],
        },
    },
}

template = TEMPLATE.read_text(encoding="utf-8")
html = (
    template.replace("__GRAPH_DATA__", json.dumps(GRAPH_DATA, ensure_ascii=False, indent=2))
    .replace("__PROJECT_NAME__", "serbeval")
    .replace("__GENERATED_AT__", GENERATED_AT)
)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(html, encoding="utf-8")
print(f"wrote {OUT.relative_to(ROOT)} ({len(html)} bytes, {n_files} tracked files)")
