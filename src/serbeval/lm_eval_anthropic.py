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
Pass `thinking=adaptive` (with a much larger `max_gen_toks`, and usually `effort=low`)
to measure the model as it behaves in normal use; comparing the two settings on the same
items is itself worth doing.
"""

from typing import Any

from lm_eval.api.registry import register_model
from lm_eval.models.anthropic_llms import AnthropicChat


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

    Notably absent: `temperature`. It is not merely optional on Opus 5 / Sonnet 5 /
    Opus 4.8 / 4.7 — sending it is a 400.
    """
    payload: dict[str, Any] = {
        "messages": messages,
        "model": model,
        "max_tokens": max_tokens,
        "thinking": {"type": "adaptive"} if thinking == "adaptive" else {"type": "disabled"},
    }
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
