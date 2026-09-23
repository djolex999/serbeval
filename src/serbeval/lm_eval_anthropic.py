"""An lm-eval model adapter that can actually talk to current Claude models.

lm-eval 0.4.12's stock `anthropic-chat` adapter cannot evaluate Claude Opus 5, Sonnet 5,
Opus 4.8 or Opus 4.7 at all, for two independent reasons:

* it sends `temperature` on every request, and that parameter was removed on those
  models — the API answers 400 and the run dies before producing a single result;
* it reads the response as `content[0]["text"]` / `block["text"]` for every block. On a
  model with thinking enabled the first block is a thinking block with no `text` key,
  so the run dies with a KeyError instead.

Both are fixed here by registering a SEPARATE model name rather than monkeypatching the
installed package: a `pip install` must not silently revert the fix, and keeping the
stock adapter reachable means the two can be compared if a result ever looks odd.

**Thinking defaults to off.** These items ask for a single letter or one word form, and
on Opus 5 thinking is on by default — with `max_gen_toks` at 32 the model would spend
its whole budget reasoning and return nothing, scoring as `unparsed` across the board.
Pass `thinking=adaptive` (usually with `effort=low`) to measure the model as it behaves
in normal use; comparing the two settings on the same items is itself worth doing.

**Some models cannot turn thinking off.** Claude Opus 5.5 and the Fable/Mythos line answer
`thinking: {"type": "disabled"}` with a 400 at every effort level. For those, pass
`thinking=omit` (the parameter is left out and the model thinks adaptively) and steer cost
with `effort=low`. Asking for `thinking=off` on one of them fails at startup rather than
400-ing on every request of a paid run.

Whenever thinking is on, `max_tokens` is raised to at least `THINKING_MIN_TOKENS`: the task
caps are sized for a bare answer, and reasoning is billed out of the same budget.
"""

from typing import Any

from lm_eval.api.registry import register_model
from lm_eval.models.anthropic_llms import AnthropicChat

THINKING_MODES = ("off", "adaptive", "omit")
# Floor on max_tokens whenever the model thinks. The tasks cap generation at 24-32
# tokens — enough for a bare answer, nowhere near enough for reasoning plus an answer.
THINKING_MIN_TOKENS = 2048
# Models that reject `thinking: {"type": "disabled"}` outright, at every effort level.
_THINKING_ALWAYS_ON = frozenset(
    {
        "claude-opus-5-5",
        "claude-fable-5",
        "claude-fable-5-1",
        "claude-mythos-5",
        "claude-mythos-5-1",
    }
)


def check_thinking_config(model: str, thinking: str) -> None:
    """Refuse a configuration the API is known to reject, before any request is sent."""
    if thinking not in THINKING_MODES:
        raise ValueError(
            f"unknown thinking mode {thinking!r}; expected one of {', '.join(THINKING_MODES)}"
        )
    if thinking == "off" and model in _THINKING_ALWAYS_ON:
        raise ValueError(
            f"{model} cannot run with thinking disabled (the API returns 400). "
            f"Pass --model_args model={model},thinking=omit,effort=low instead."
        )


def build_payload(
    *,
    messages: list[dict[str, Any]],
    model: str,
    max_tokens: int,
    stop: list[str],
    thinking: str = "off",
    effort: str | None = None,
) -> dict[str, Any]:
    """Build a Messages API request body that current models accept.

    Notably absent: `temperature`. It is not merely optional on Opus 5 / Opus 5.5 /
    Sonnet 5 / Opus 4.8 / 4.7 — sending it is a 400.
    """
    thinking_on = thinking != "off"
    payload: dict[str, Any] = {
        "messages": messages,
        "model": model,
        "max_tokens": max(max_tokens, THINKING_MIN_TOKENS) if thinking_on else max_tokens,
    }
    if thinking == "off":
        payload["thinking"] = {"type": "disabled"}
    elif thinking == "adaptive":
        payload["thinking"] = {"type": "adaptive"}
    # "omit": no thinking parameter at all — the model's own default (adaptive) applies.
    # The API rejects whitespace-only stop sequences. Note "\n\n".strip() is empty, so
    # the tasks' `until: ["\n\n"]` is dropped here exactly as the stock adapter drops
    # it: generation runs to max_tokens rather than stopping at a blank line. That is
    # harmless for these tasks — the answer is one letter or one word form, max_tokens
    # is small, and both extractors read only the leading part of the response.
    cleaned = [s for s in stop if s and s.strip()]
    if cleaned:
        payload["stop_sequences"] = cleaned
    if effort is not None:
        # effort lives inside output_config, not at the top level.
        payload["output_config"] = {"effort": effort}
    return payload


def text_from_content(content: list[dict[str, Any]]) -> str:
    """Concatenate the text blocks of a response, ignoring every other block type.

    Thinking, tool_use and refusal blocks carry no `text` key. Returning "" for a
    response with no text at all is deliberate: the task's `unparsed` metric then
    records it as unreadable, which is the honest outcome, rather than crashing the run.
    """
    return "".join(
        block["text"]
        for block in content
        if isinstance(block, dict) and block.get("type") == "text" and "text" in block
    )


@register_model("anthropic-chat-fixed")
class AnthropicChatFixed(AnthropicChat):  # type: ignore[misc]  # lm_eval ships no stubs
    """`anthropic-chat` with the temperature and thinking-block bugs fixed."""

    def __init__(self, thinking: str = "off", effort: str | None = None, **kwargs: Any):
        # Before the parent init: it needs only the model name, and a bad config should
        # be reported even when something later in lm-eval's own setup would also fail.
        check_thinking_config(str(kwargs.get("model", "")), thinking)
        super().__init__(**kwargs)
        self.thinking = thinking
        self.effort = effort

    def _create_payload(
        self,
        messages: list[dict[str, Any]],
        *,
        generate: bool = True,
        gen_kwargs: dict[str, Any] | None = None,
        eos: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        gen_kwargs = dict(gen_kwargs or {})
        gen_kwargs.pop("do_sample", None)
        gen_kwargs.pop("temperature", None)
        max_tokens = gen_kwargs.pop("max_gen_toks", self._max_gen_toks)
        stop = gen_kwargs.pop("until", [])
        if not isinstance(stop, list):
            stop = [stop]

        payload = build_payload(
            messages=messages,
            model=self.model,
            max_tokens=max_tokens,
            stop=stop,
            thinking=self.thinking,
            effort=self.effort,
        )
        payload.update(gen_kwargs)
        return payload

    def parse_generations(
        self, outputs: dict[str, Any] | list[dict[str, Any]], **kwargs: Any
    ) -> list[str]:
        if not isinstance(outputs, list):
            outputs = [outputs]
        return [text_from_content(out.get("content", [])) for out in outputs]
