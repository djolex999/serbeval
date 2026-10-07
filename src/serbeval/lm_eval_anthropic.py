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

import copy
import logging
import os
import time
from collections.abc import Callable
from typing import Any
from urllib.parse import urlparse

import requests
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


Messages = str | list[dict[str, Any]]


def normalize_messages(messages: Messages) -> tuple[str | None, list[dict[str, Any]]]:
    """Return (system prompt, turns) for either shape lm-eval may pass.

    Without --apply_chat_template lm-eval hands over the prompt as a plain string; with
    it, a list of role/content dicts that may open with a system message. The stock
    adapter crashes on the string, so both shapes are accepted here and the documented
    commands work whether or not the flag is given.
    """
    if isinstance(messages, str):
        return None, [{"role": "user", "content": messages}]
    turns = [{"role": m["role"], "content": m["content"]} for m in messages]
    if turns and turns[0]["role"] == "system":
        return str(turns[0]["content"]), turns[1:]
    return None, turns


def resolve_api_key(base_url: str) -> str:
    """Pick the credential for wherever requests are actually going.

    The stock adapter always reads ANTHROPIC_API_KEY. Pointing `base_url` at a reseller
    such as Kie would then ship a first-party key to a third party, so any host other
    than api.anthropic.com reads KIE_API_KEY instead — and never falls back.
    """
    host = urlparse(base_url).hostname or ""
    if host.endswith("kie.ai"):
        key = os.environ.get("KIE_API_KEY")
        if not key:
            raise ValueError(f"base_url points at Kie ({host}); set KIE_API_KEY")
        return key
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise ValueError("ANTHROPIC_API_KEY is not set")
    return key


log = logging.getLogger(__name__)

# Returned in place of a response body when a request keeps failing transiently. It
# parses as "no text", so that ONE item scores `unparsed` and the run carries on.
TRANSIENT_FAILURE: dict[str, Any] = {"serbeval_transient_failure": True, "content": []}
_TRANSIENT_STATUS = frozenset({408, 409, 425, 429, 500, 502, 503, 504})
PATIENT_ATTEMPTS = 8
_MAX_WAIT = 60.0
# (connect, read) seconds. Without a timeout, a connection the provider accepts but never
# answers blocks forever — a Kie run once sat on one request for two hours. The read limit
# is generous because Kie's GPT endpoint legitimately takes up to ~70 s.
REQUEST_TIMEOUT = (15.0, 180.0)


def post_with_patience(
    post: Callable[..., Any],
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    *,
    attempts: int = PATIENT_ATTEMPTS,
    sleep: Callable[[float], None] = time.sleep,
    verify: bool = True,
) -> dict[str, Any]:
    """POST with a long backoff on transient failures; never let one item end the run.

    lm-eval's own retry gives up after ~35 s and then raises, which aborts the whole
    task: on Kie, one request hitting a streak of 500s threw away 17 answers already
    collected. Here 5xx, 429 and dropped connections back off up to a minute between
    tries, and if they never clear, TRANSIENT_FAILURE is returned so that item scores
    `unparsed` — visible in the report — while everything else is kept. Other 4xx
    (bad request, bad credentials) raise at once: they fail the same way every time.
    """
    wait = 2.0
    for attempt in range(1, attempts + 1):
        try:
            response = post(
                url, json=payload, headers=headers, verify=verify, timeout=REQUEST_TIMEOUT
            )
        except (requests.ConnectionError, requests.Timeout) as exc:
            reason = f"connection: {exc}"
        else:
            if response.ok:
                body: dict[str, Any] = response.json()
                return body
            if response.status_code not in _TRANSIENT_STATUS:
                response.raise_for_status()
            reason = f"HTTP {response.status_code}: {response.text[:200]}"
        if attempt == attempts:
            log.warning("giving up on one item after %d attempts (%s)", attempts, reason)
            return copy.deepcopy(TRANSIENT_FAILURE)
        log.warning("transient failure, retry %d/%d in %.0fs (%s)", attempt, attempts, wait, reason)
        sleep(wait)
        wait = min(wait * 2, _MAX_WAIT)
    return copy.deepcopy(TRANSIENT_FAILURE)


# Account-level failures. Kie reports them with HTTP 200 and an error envelope, so
# lm-eval's HTTP retry logic never sees them.
_FATAL_ENVELOPE_CODES = frozenset({401, 402, 403})


def check_envelope(response: dict[str, Any]) -> None:
    """Stop the run on an auth or billing failure disguised as a successful response.

    Kie answered a wrong auth header with HTTP 200 and {"code": 401, "msg": ...}. Read as
    "no text", every item scored unparsed and a full paid run would have ended at 0%
    without a single error. Other envelope codes still degrade to unparsed per item.
    """
    code = response.get("code")
    if isinstance(code, int) and code in _FATAL_ENVELOPE_CODES:
        raise RuntimeError(f"provider returned {code}: {response.get('msg', '')}")


def _is_kie(base_url: str) -> bool:
    return (urlparse(base_url).hostname or "").endswith("kie.ai")


def build_payload(
    *,
    messages: Messages,
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
    system, turns = normalize_messages(messages)
    payload: dict[str, Any] = {
        "messages": turns,
        "model": model,
        "max_tokens": max(max_tokens, THINKING_MIN_TOKENS) if thinking_on else max_tokens,
        # The Anthropic API defaults to non-streaming; Kie's Claude endpoint defaults to
        # streaming, which returns SSE this adapter cannot parse. Always say so.
        "stream": False,
    }
    if system is not None:
        payload["system"] = system
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
        # Resolve once, at startup: a missing or misrouted key fails before any request.
        self._resolved_key = resolve_api_key(self.base_url)
        self.thinking = thinking
        self.effort = effort

    @property
    def api_key(self) -> str:
        return self._resolved_key

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
        return post_with_patience(
            requests.post, self.base_url, payload, self.header, verify=self.verify_certificate
        )

    @property
    def header(self) -> dict[str, str]:
        if _is_kie(self.base_url):
            # Kie's docs say X-Api-Key; the live endpoint rejects it (HTTP 200, code 401)
            # and accepts only a Bearer token.
            return {
                "Authorization": f"Bearer {self._resolved_key}",
                "anthropic-version": self.anthropic_version,
            }
        return {"x-api-key": self._resolved_key, "anthropic-version": self.anthropic_version}

    def _create_payload(
        self,
        messages: Messages,
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
        for out in outputs:
            check_envelope(out)
        return [text_from_content(out.get("content", [])) for out in outputs]
