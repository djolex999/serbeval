#!/usr/bin/env python
"""Run lm_eval with serbeval's fixed Anthropic adapter registered.

lm-eval discovers models from its own registry, so a custom adapter has to be imported
before the CLI parses `--model`. This wrapper does exactly that and then hands over --
every lm_eval flag works unchanged.

    scripts/run_eval.py --model anthropic-chat-fixed \
      --model_args model=claude-opus-5 \
      --tasks srb_grammar --include_path lm_eval_tasks \
      --output_path results/opus-5 --log_samples

Use `--model anthropic-chat` (no wrapper needed) only for models that still accept
`temperature` -- Haiku 4.5, Sonnet 4.6, Opus 4.6. Everything newer needs this one.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from lm_eval.__main__ import cli_evaluate

import serbeval.lm_eval_anthropic
import serbeval.lm_eval_kie
import serbeval.lm_eval_openrouter  # noqa: F401  (import registers openrouter-chat)

if __name__ == "__main__":
    cli_evaluate()
