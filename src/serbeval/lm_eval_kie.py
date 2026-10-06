"""lm-eval adapter for GPT models served by Kie through the Responses format.

Kie serves `gpt-6-1-sol` only at `/codex/v1/responses`, in OpenAI's Responses shape:
`input` instead of `messages`, `reasoning.effort`, and text under
`output[].content[].text`. lm-eval 0.4.12 has no adapter for that format at all —
`openai-chat-completions` posts a chat-completions body to a chat-completions URL.

**This is for item triage only, never for reported scores.** A reseller cannot be
verified to have served the model it names, uncached and with parameters intact.

The endpoint documents no max-output-tokens field, so the only per-request cost lever
is `reasoning.effort`, which defaults to `low`. The hard budget cap is Kie's prepaid
credit balance.

Credentials come only from KIE_API_KEY. The parent class reads OPENAI_API_KEY, and a
real OpenAI key has no business being sent to a reseller.
"""

import os
from typing import Any

from lm_eval.api.registry import register_model
from lm_eval.models.openai_completions import LocalChatCompletion

from serbeval.lm_eval_anthropic import Messages, normalize_messages

KIE_RESPONSES_URL = "https://api.kie.ai/codex/v1/responses"
EFFORTS = ("low", "medium", "high", "xhigh")


def kie_api_key() -> str:
    key = os.environ.get("KIE_API_KEY")
    if not key:
        raise ValueError("set KIE_API_KEY (OPENAI_API_KEY is deliberately never read here)")
    return key


def build_responses_payload(
    *, messages: Messages, model: str, effort: str = "low"
) -> dict[str, Any]:
    """A Responses-format body: no sampling parameters, no stop, no token cap.

    None of those appear in Kie's schema for this model, and reasoning models reject
    `temperature` and `stop` in general.
    """
    if effort not in EFFORTS:
        raise ValueError(f"unknown reasoning effort {effort!r}; expected one of {EFFORTS}")
    system, turns = normalize_messages(messages)
    if system is not None:
        turns = [{"role": "system", "content": system}, *turns]
    return {
        "model": model,
        "input": [
            {"role": t["role"], "content": [{"type": "input_text", "text": str(t["content"])}]}
            for t in turns
        ],
        "stream": False,
        "reasoning": {"effort": effort},
    }


def text_from_responses(response: dict[str, Any]) -> str:
    """Concatenate every `output_text` in the response's message items.

    Reasoning items carry no text and are skipped. A Kie error envelope
    (`{"code": ..., "msg": ...}`) has no output and yields "", which the task then
    scores as `unparsed` — the honest result — instead of crashing the run.
    """
    data = response.get("data")
    body: dict[str, Any] = data if isinstance(data, dict) else response
    texts: list[str] = []
    for item in body.get("output", []) or []:
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        for part in item.get("content", []) or []:
            if isinstance(part, dict) and part.get("type") == "output_text":
                texts.append(str(part.get("text", "")))
    return "".join(texts)


@register_model("kie-responses")
class KieResponses(LocalChatCompletion):  # type: ignore[misc]  # lm_eval ships no stubs
    """Responses-format client for GPT models on Kie. Triage only."""

    def __init__(self, effort: str = "low", base_url: str = KIE_RESPONSES_URL, **kwargs: Any):
        if effort not in EFFORTS:
            raise ValueError(f"unknown reasoning effort {effort!r}; expected one of {EFFORTS}")
        self._resolved_key = kie_api_key()
        super().__init__(base_url=base_url, **kwargs)
        self.effort = effort

    @property
    def api_key(self) -> str:
        return self._resolved_key

    @property
    def header(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._resolved_key}"}

    def _create_payload(
        self,
        messages: Messages,
        *,
        generate: bool = True,
        gen_kwargs: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return build_responses_payload(messages=messages, model=self.model, effort=self.effort)

    @staticmethod
    def parse_generations(
        outputs: dict[str, Any] | list[dict[str, Any]], **kwargs: Any
    ) -> list[str]:
        if not isinstance(outputs, list):
            outputs = [outputs]
        return [text_from_responses(out) for out in outputs]
