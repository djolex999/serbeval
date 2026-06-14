# serbeval — Architecture
*Generated: 2026-06-14*

## 1. Project Overview

serbeval is a Serbian-language evaluation benchmark for LLMs, built on EleutherAI's
lm-evaluation-harness (pinned to `0.4.12`). It ships three multiple-choice tasks — grammar,
idioms, and Cyrillic/Latin script agreement — plus Python tooling to author, validate, and
self-filter dataset items via the Claude API. It targets the things models actually get wrong in
Serbian (case government, clitic placement, verbal aspect, paukal agreement, script consistency)
that generic multilingual benchmarks miss. Current state: **v0.1 + v0.2 complete and green**, but
every item is `verified: false` pending a native-speaker pass, and no live eval has run (no API key
on the build machine). One-line identity: a pydantic-typed Python package + harness task configs,
local-only, no published artifacts.

## 2. Technology Stack

| Layer | Technology | Version | Notes |
| --- | --- | --- | --- |
| Language | Python | 3.11+ (dev on 3.13) | strict typing throughout `src/` |
| Eval engine | lm-evaluation-harness | `0.4.12` (pinned) | hard pin; task YAMLs target its schema |
| LLM SDK | anthropic | ≥0.69 | used by `generate` + `selfcheck`; never called live yet |
| Validation | pydantic | v2 | `EvalItem` is the single source of truth |
| Dataset loading | HF `datasets` (via harness) | transitive | `json` loader, relative `data_files` |
| Testing | pytest | ≥8 | 50 tests; lm-eval integration test marked `slow` |
| Typing | mypy (strict) | ≥1.10 | scoped to `src/` |
| Lint/format | ruff | ≥0.6 | ignores RUF001/2/3 (intentional Cyrillic) |
| Packaging | setuptools (`src/` layout) | — | console script `serbeval` |
| CI/CD | none | — | gates run locally; see §12 |
| Hosting | none | — | local-only by design (no HF Hub / PyPI) |

## 3. Directory Structure

```
serbeval/
├── src/serbeval/            # the installable package (the only typed surface)
│   ├── schema.py            # EvalItem pydantic model + validators
│   ├── data.py              # JSONL IO + validate_dataset (integrity checks)
│   ├── translit.py          # digraph-aware Latin→Cyrillic transliterator
│   ├── generate.py          # Claude candidate authoring + run_generate
│   ├── selfcheck.py         # self-consistency filter + run_selfcheck
│   └── cli.py               # argparse entrypoint (validate/generate/selfcheck)
├── lm_eval_tasks/           # harness task configs (loaded via --include_path)
│   ├── srb_grammar.yaml     # } generate_until + regex letter extraction
│   ├── srb_idioms.yaml      # }
│   ├── srb_cyrillic_agreement.yaml  # + custom pair_agreement metric
│   └── utils.py             # !function helpers: prompt build, metrics
├── data/<task>/             # datasets (not under typing/lint)
│   ├── items.jsonl          # curated (verified:false until human pass)
│   ├── candidates.jsonl     # generated, unmerged (created on demand)
│   └── discarded.jsonl      # selfcheck + workflow rejects, with reasons
├── scripts/                 # one-shot builders (E501-exempt data tables)
│   ├── seed_workflow.js     # multi-agent author→verify→repair orchestrator
│   ├── ingest_seed.py       # workflow result → items.jsonl
│   ├── build_cyrillic_pairs.py  # base facts → paired items
│   └── build_arch_map.py    # this map's generator
├── tests/                   # 50 tests mirroring src/ + a slow harness test
├── results/                 # eval outputs (README = commands; no real numbers yet)
└── DECISIONS.md · HANDOFF.md · CONTRIBUTING.md · devlog.md   # project log
```

## 4. Route Map

Not a web app — "routes" are the two execution surfaces: the CLI and the harness tasks. No auth
applies (local tooling).

### CLI commands (`serbeval ...`)
| Command | Args | File | Network | Purpose |
| --- | --- | --- | --- | --- |
| `validate` | `<path>` | `cli.py:_cmd_validate` | no | Schema + integrity gate; exit 1 on any problem |
| `generate` | `--task --category -n --model --data-dir` | `cli.py:_cmd_generate` | **yes** | Author candidates → `candidates.jsonl` |
| `selfcheck` | `--task --runs --model --data-dir` | `cli.py:_cmd_selfcheck` | **yes** | 3× re-answer filter; partition keep/discard |

### Harness tasks (`lm_eval --tasks ... --include_path lm_eval_tasks`)
| Task | File | Items | Metrics |
| --- | --- | --- | --- |
| `srb_grammar` | `srb_grammar.yaml` | 50 | `exact_match` |
| `srb_idioms` | `srb_idioms.yaml` | 30 | `exact_match` |
| `srb_cyrillic_agreement` | `srb_cyrillic_agreement.yaml` | 30 (15 pairs) | `exact_match` + `pair_agreement` |

## 5. Module Architecture

Business logic lives in `src/serbeval/`, with a strict dependency spine and no cycles:

```
cli.py ──┬─→ data.py ───→ schema.py
         ├─→ generate.py ─→ {data, schema}
         └─→ selfcheck.py ─→ {data, schema}

scripts/  ingest_seed.py ─→ {data, schema}
          build_cyrillic_pairs.py ─→ {data, schema, translit}

lm_eval_tasks/utils.py  (standalone; imported by harness via !function, not by the package)
```

`schema.py` is the foundation (depended on by everything, depends on nothing). `data.py` is the IO +
integrity layer. `generate.py` and `selfcheck.py` each expose a pure, unit-tested core (mockable
Anthropic client) plus a `run_*` orchestration helper that wires the core to on-disk files. `cli.py`
is a thin dispatcher that constructs the Anthropic client lazily — so `validate` works with no API
key. `lm_eval_tasks/utils.py` is deliberately decoupled from the package (the harness loads it by
path), so it re-implements letter extraction rather than importing it.

## 6. Data Model

No database. The data model is one pydantic schema, `EvalItem` (`schema.py`), serialized as JSONL.

| Field | Type | Notes |
| --- | --- | --- |
| `id` | str | `<task-slug>-<category>-NNNN` (+`-lat`/`-cyr` for pairs) |
| `task`, `category` | str | non-blank |
| `question` | str | self-contained Serbian prompt |
| `choices` | list[str] | exactly 4, unique, non-blank |
| `answer_index` | int | 0–3 |
| `explanation` | str | why the gold answer is correct |
| `script` | `"latin" \| "cyrillic"` | text must match the declared script |
| `pair_id` | str \| None | links the two scripts of a cyrillic-agreement item |
| `source` | str | `handwritten-*` / `generated-claude-<model>` |
| `verified` | bool | **always `false` today** — publish gate |
| `license` | str | `CC-BY-4.0` |

`validate_dataset()` enforces cross-item invariants: unique ids, no duplicate question text within a
script, script-consistency (Cyrillic codepoints only in Cyrillic items; A–D labels stay Latin and
are added at prompt time), and pair integrity (each `pair_id` has exactly one Latin + one Cyrillic
item with identical `answer_index` and category).

## 7. Data Flow

**Flow: item lifecycle (authoring → score)**
```
category brief ─→ Claude authoring (generate.py / seed_workflow)   [Anthropic API]
  → candidates.jsonl (verified:false)
  → selfcheck: re-answer 3×                                         [Anthropic API]
      → disagree / wrong  → discarded.jsonl (+reason)
      → unanimous-correct → survivors
  → HUMAN VERIFICATION (pending) → items.jsonl (verified:true)
  → lm-eval: doc_to_text → model → regex \b([ABCD])\b → exact_match [model under test]
  → results JSON
```

**Flow: cyrillic pair scoring**
```
items.jsonl (pair) → harness runs both scripts independently
  → utils.process_results_pair → (pair_id, correct) per item
  → utils.pair_agreement aggregates → fraction of pairs that scored identically
```
The agreement metric is script-consistency, decoupled from accuracy: a pair "agrees" when the model
is right on both scripts or wrong on both. Verified end-to-end with the harness `dummy` model
(exact_match 0, pair_agreement 1.0 — consistent wrongness).

**Steps with no error handling by design:** `generate`/`selfcheck` let Anthropic SDK exceptions
propagate (CLI is the right layer to fail loudly); `validate` catches IO/parse errors and returns
exit 1.

## 8. External Services

| Service | Purpose | SDK | Credentials | Risk |
| --- | --- | --- | --- | --- |
| Anthropic API | Item authoring + self-consistency + model-under-test | `anthropic` | `ANTHROPIC_API_KEY` env (absent on dev machine) | **High** — core to generation & live eval |
| lm-evaluation-harness | The eval engine | `lm-eval==0.4.12` | none | **Critical** — pinned; task schema is version-coupled |
| HF `datasets` | Loads JSONL via `json` loader | transitive | none | Medium — relative paths require repo-root cwd |

No payments, email, storage, auth, or monitoring services — out of scope for a local benchmark.

## 9. Authentication & Authorization

Not applicable. serbeval is local CLI + config tooling with no server, no users, no sessions. The
only secret is `ANTHROPIC_API_KEY`, read from the environment by the SDK and never written to disk
or code (`.gitignore` covers `.env*`). `validate` and the harness tasks require no credentials.

## 10. Deployment

No deployment. Everything runs locally from the repo root (mandatory — task YAMLs use relative
`data_files`). Install: `pip install -e ".[dev]"` into `.venv/`. The only environment variable is
`ANTHROPIC_API_KEY` (one, env-only). By maintainer policy there are **no** HF Hub pushes, no PyPI
publish, and no upstream PRs — publishing is a manual, human-gated step. Eval outputs land under
`results/`; raw per-sample logs (`results/**/raw/`) are gitignored, summary JSON is committable.

## 11. Patterns & Conventions

- **TDD throughout** — every `src/` module has a mirror test; tests use a mocked Anthropic client,
  never the network. The one live-dependency test (loads lm-eval) is marked `slow`.
- **Schema-centric** — `EvalItem` is the single contract; tooling and validation both derive from it.
- **Testable core + thin orchestration** — `generate_candidates`/`selfcheck_item` are pure and
  unit-tested; `run_generate`/`run_selfcheck` add file IO; `cli.py` only parses args.
- **No-logprob design** — all tasks are `generate_until` + regex extraction, so any chat API works.
- **Script discipline** — A/B/C/D labels are Latin even in Cyrillic items, keeping the extraction
  regex script-independent; `validate_dataset` enforces script purity.
- **Decision log** — `DECISIONS.md` records every non-obvious choice one line each; `HANDOFF.md`
  leads with what needs human eyes.
- **Consistent gates** — `pytest` · `mypy src` · `ruff check` must all be green before "done".

Minor inconsistency (intentional, documented): `lm_eval_tasks/utils.py` duplicates letter-extraction
logic instead of importing `serbeval` (the harness loads it standalone by path).

## 12. Risks & Recommendations

### [DO NOW] Items are unverified — do not publish any numbers
**Observation**: all 110 items carry `verified: false`; they were authored and cross-checked only by
LLM agents.
**Risk**: publishing benchmark results on model-verified items would mislabel them as human-quality
and could embed subtle normative errors (the agents themselves dropped 20 ambiguous items).
**Action**: native-speaker review per `HANDOFF.md`, flipping `verified: true` only on items that
pass. Block any results release until then.

### [DO NOW] No live pipeline run has happened
**Observation**: no `ANTHROPIC_API_KEY` on the machine; `generate`/`selfcheck` and the eval have only
been mock- or dummy-tested.
**Risk**: first real run may surface adapter/arg mismatches (model id, `--apply_chat_template`) not
caught by mocks.
**Action**: run the documented haiku-4-5 smoke command in `results/README.md` against the real API,
then commit the summary JSON.

### [DO LATER] No CI
**Observation**: gates (`pytest`/`mypy`/`ruff`) run only locally.
**Risk**: regressions slip in once others contribute; CONTRIBUTING promises green gates with nothing
enforcing them.
**Action**: add a GitHub Actions workflow running the three gates on PRs (the `.github/` dir already
holds issue templates).

### [DO LATER] Thin and uneven category coverage
**Observation**: `glagolski-vid` survived verification with only 4 items; categories range 4–11.
**Risk**: per-category scores will be noisy; the grammar task underweights aspect.
**Action**: `serbeval generate --task srb_grammar --category glagolski-vid -n 8`, then selfcheck +
human-verify. Aim for a per-category floor (e.g. ≥8).

### [DO LATER] lm-eval version is a hard, brittle pin
**Observation**: task YAMLs (custom `process_results`, filter schema) are coupled to 0.4.12; one
deprecation already surfaced (`load_task_or_group`).
**Risk**: upgrading the harness later is a migration, not a bump.
**Action**: keep the pin, but add a one-line note in `results/README.md` documenting why, and re-run
the `slow` test as the canary when ever bumping.

### [DO IF IT BREAKS] Transliterator morpheme-boundary edge cases
**Observation**: `translit.py` can't tell `nadž`/`inj` digraph-vs-boundary cases apart; the current
base vocabulary avoids them.
**Risk**: a future contributor adds a base item like "nadživeti" and gets a wrong Cyrillic rendering.
**Action**: if expanding the cyrillic set, spot-check renders, or add a small exceptions table to
`translit.py`.
