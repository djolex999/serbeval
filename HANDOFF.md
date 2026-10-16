# HANDOFF

Why every non-obvious choice was made: [DECISIONS.md](DECISIONS.md). Task list: [tasks/todo.md](tasks/todo.md).
Leaderboard: [results/LEADERBOARD.md](results/LEADERBOARD.md).

## Where we left off

serbeval is public and has been shared:
- GitHub `djolex999/serbeval`;
- Hugging Face dataset `djolex999/serbeval` (official set v1: 355 items, per-item verification
  status in MANIFEST.json);
- a 30-model official leaderboard (38–98%, five frontier models at 98%; best open-weights DeepSeek V4 Pro 95%);
- a LinkedIn post (1k+ impressions);
- a PR adding the tasks to EleutherAI's lm-evaluation-harness (#4400).

Aleksa Gordić (pretraining @ Nemotron) commented on the post. He suggested running Nemotron
3 Ultra, plotting open-weights models only, and making the benchmark harder, since Kimi K3
(91%) is close to saturating it too.

Done since (2026-10-16/17): Nemotron 3 Ultra (76%) and four more open-weights models; an
open-weights-only chart; a reasoning off/low/high comparison (no model gains more than 2 points,
Nemotron drops to 65% at high). Two adapter fixes: no stop sequence while reasoning, and a token
floor that grows with the effort.

## In flight

- PR EleutherAI/lm-evaluation-harness#4400 is open, mergeable, and waiting on the CLA signature
  and a maintainer. The branch `add-serbeval` is in the fork `djolex999/lm-evaluation-harness`.

## Blockers

- **CLA** on #4400: only the maintainer can sign it.
- **OpenRouter key** (2026-10-16) expires 2026-10-17 10:02 UTC; about $3.35 credit left on the account.

## Next session: start here

1. Send Aleksa the open-weights and reasoning charts (results/leaderboard-open.png,
   results/reasoning-compare.png).
2. Decide how to make it harder (see todo). Measure on open models before building anything.
3. Add Mistral Large 4 to the open-weights chart once its weights ship.

Working rules:
- Run models in parallel; only requests inside one run stay sequential.
- Check `unparsed` and empty answers before believing a score.
- Pin the provider and precision for open models.
- Never put Claude attribution in commits or PRs.
- Chain the gates with `&&` before any commit or push.
