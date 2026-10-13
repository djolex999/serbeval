"""lm-eval adapter for models served through OpenRouter (chat-completions format).

One key reaches every tier the leaderboard needs: small and large open-weights models
in full precision, cheap commercial models, and frontier models. Unlike Kie it forwards
requests to the named provider without injecting a hidden system prompt, which is why
these runs are usable for the leaderboard — with the provider recorded, because for
open-weights models OpenRouter may route to a provider serving a quantized build.
`provider=` pins one provider with no fallback, `quantizations=bf16|fp8` restricts it.

Reasoning is OFF by default (`reasoning=none`): a thinking model given the 24-token
cloze budget spends it all thinking and answers nothing (qwen3 did exactly that through
Ollama). Models that cannot turn it off take `reasoning=low` (or `omit`), and then get
a 2048-token floor so an answer still fits after the thinking.

Credentials come only from OPENROUTER_API_KEY. The parent class reads OPENAI_API_KEY,
and a first-party key has no business being sent to a router.
"""

import copy
import logging
import os
from typing import Any

import requests
from lm_eval.api.registry import register_model
from lm_eval.models.openai_completions import LocalChatCompletion

from serbeval.lm_eval_anthropic import post_with_patience

__all__ = ["OpenRouterChat", "build_openrouter_payload", "openrouter_api_key", "text_from_chat"]

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
REASONING = ("none", "minimal", "low", "medium", "high", "xhigh", "omit")
THINKING_FLOOR = 2048
_FATAL = frozenset({401, 402, 403})

log = logging.getLogger(__name__)


def openrouter_api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise ValueError("set OPENROUTER_API_KEY (OPENAI_API_KEY is deliberately never read)")
    return key


def build_openrouter_payload(
    *,
    messages: list[dict[str, Any]],
    model: str,
    max_tokens: int,
    stop: list[str],
    reasoning: str = "none",
    provider: str | None = None,
    quantizations: str | None = None,
    send_stop: bool = True,
) -> dict[str, Any]:
    if reasoning not in REASONING:
        raise ValueError(f"unknown reasoning {reasoning!r}; expected one of {REASONING}")
    body: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens if reasoning == "none" else max(max_tokens, THINKING_FLOOR),
        "temperature": 0,
        "stream": False,
    }
    if stop and send_stop:
        body["stop"] = stop[:4]
    if reasoning != "omit":
        body["reasoning"] = {"effort": reasoning}
    if provider or quantizations:
        routing: dict[str, Any] = {}
        if provider:
            routing["order"] = [provider]
            routing["allow_fallbacks"] = False
        if quantizations:
            routing["quantizations"] = [q for q in quantizations.split("|") if q]
        body["provider"] = routing
    return body


def text_from_chat(response: dict[str, Any]) -> str:
    """The assistant text; "" for an empty or failed generation, which scores `unparsed`.

    Account-level errors (bad key, no credits) raise instead: they fail every item the
    same way, and a paid run must stop at the first one, not finish at 0%.
    """
    error = response.get("error")
    if isinstance(error, dict):
        code = error.get("code")
        if isinstance(code, int) and code in _FATAL:
            raise RuntimeError(f"OpenRouter returned {code}: {error.get('message', '')}")
        return ""
    choices = response.get("choices") or []
    if not choices:
        return ""
    content = (choices[0].get("message") or {}).get("content")
    return content if isinstance(content, str) else ""


@register_model("openrouter-chat")
class OpenRouterChat(LocalChatCompletion):  # type: ignore[misc]  # lm_eval ships no stubs
    """Chat-completions client for OpenRouter with patient retries and provenance logging."""

    def __init__(
        self,
        base_url: str = OPENROUTER_URL,
        reasoning: str = "none",
        provider: str | None = None,
        quantizations: str | None = None,
        stop: str = "on",
        **kwargs: Any,
    ):
        if reasoning not in REASONING:
            raise ValueError(f"unknown reasoning {reasoning!r}; expected one of {REASONING}")
        if stop not in ("on", "off"):
            raise ValueError(f"stop must be 'on' or 'off', got {stop!r}")
        self._resolved_key = openrouter_api_key()
        kwargs.setdefault("tokenized_requests", False)
        super().__init__(base_url=base_url, **kwargs)
        self.reasoning = reasoning
        self.provider = provider
        self.quantizations = quantizations
        # Some models break on stop sequences (cohere/command-a-plus returns content None
        # when one is sent); the answer extractor reads the first line either way.
        self.send_stop = stop == "on"
        self.providers_seen: set[str] = set()

    @property
    def api_key(self) -> str:
        return self._resolved_key

    @property
    def header(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._resolved_key}", "X-Title": "serbeval"}

    def _create_payload(
        self,
        messages: list[dict[str, Any]],
        *,
        generate: bool = True,
        gen_kwargs: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        gen = dict(gen_kwargs or {})
        budget = gen.get("max_tokens", gen.get("max_gen_toks", self._max_gen_toks))
        max_tokens = int(budget) if budget is not None else 256
        until = gen.get("until") or []
        stop = [until] if isinstance(until, str) else list(until)
        return build_openrouter_payload(
            messages=messages,
            model=self.model,
            max_tokens=max_tokens,
            stop=stop,
            reasoning=self.reasoning,
            provider=self.provider,
            quantizations=self.quantizations,
            send_stop=self.send_stop,
        )

    def model_call(
        self,
        messages: Any,
        *,
        generate: bool = True,
        gen_kwargs: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        payload = self._create_payload(
            self.create_message(messages), generate=generate, gen_kwargs=copy.deepcopy(gen_kwargs)
        )
        body = post_with_patience(
            requests.post, self.base_url, payload, self.header, verify=self.verify_certificate
        )
        served_by = body.get("provider")
        if isinstance(served_by, str) and served_by not in self.providers_seen:
            # Provenance: for open-weights models the provider decides the precision.
            self.providers_seen.add(served_by)
            log.warning("OpenRouter: %s served by %s", self.model, served_by)
        return body

    @staticmethod
    def parse_generations(
        outputs: dict[str, Any] | list[dict[str, Any]], **kwargs: Any
    ) -> list[str]:
        if not isinstance(outputs, list):
            outputs = [outputs]
        return [text_from_chat(out) for out in outputs]
