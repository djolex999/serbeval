import pytest

from serbeval.lm_eval_anthropic import build_payload, text_from_content

# --- payload ---------------------------------------------------------------


def test_payload_never_sends_temperature() -> None:
    # `temperature` was removed on Opus 5 / Sonnet 5 / Opus 4.8 / 4.7 and returns a
    # 400. lm-eval's stock adapter sends it unconditionally, so those models cannot
    # be evaluated with it at all.
    payload = build_payload(
        messages=[{"role": "user", "content": "q"}],
        model="claude-opus-5",
        max_tokens=32,
        stop=["\n\n"],
    )
    assert "temperature" not in payload


def test_payload_carries_the_basics() -> None:
    payload = build_payload(
        messages=[{"role": "user", "content": "q"}],
        model="claude-opus-5",
        max_tokens=32,
        stop=["\n\n"],
    )
    assert payload["model"] == "claude-opus-5"
    assert payload["max_tokens"] == 32
    assert payload["messages"] == [{"role": "user", "content": "q"}]


def test_thinking_is_off_by_default() -> None:
    # These items want a single letter. Thinking is on by default on Opus 5, and with
    # max_tokens at 32 it would consume the budget before producing an answer.
    payload = build_payload(messages=[], model="claude-opus-5", max_tokens=32, stop=[])
    assert payload["thinking"] == {"type": "disabled"}


def test_adaptive_thinking_can_be_requested() -> None:
    payload = build_payload(
        messages=[], model="claude-opus-5", max_tokens=2048, stop=[], thinking="adaptive"
    )
    assert payload["thinking"] == {"type": "adaptive"}


def test_effort_is_sent_inside_output_config() -> None:
    payload = build_payload(
        messages=[], model="claude-opus-5", max_tokens=2048, stop=[], effort="low"
    )
    assert payload["output_config"] == {"effort": "low"}


def test_effort_is_omitted_when_not_asked_for() -> None:
    payload = build_payload(messages=[], model="claude-opus-5", max_tokens=32, stop=[])
    assert "output_config" not in payload


def test_whitespace_only_stop_sequences_are_dropped() -> None:
    # The API rejects whitespace-only stop sequences, and "\n\n".strip() is empty — so
    # the tasks' `until: ["\n\n"]` never reaches the API. Generation therefore runs to
    # max_tokens instead of stopping at a blank line. Harmless here: the answer is a
    # letter or one word form, max_tokens is small, and both extractors read only the
    # leading part of the response.
    payload = build_payload(
        messages=[], model="claude-opus-5", max_tokens=32, stop=["\n\n", "", "  "]
    )
    assert "stop_sequences" not in payload


def test_a_real_stop_sequence_survives() -> None:
    payload = build_payload(
        messages=[], model="claude-opus-5", max_tokens=32, stop=["END", ""]
    )
    assert payload["stop_sequences"] == ["END"]


# --- response parsing ------------------------------------------------------


def test_reads_text_past_a_leading_thinking_block() -> None:
    # The stock adapter does choices["text"] on every block, so a thinking block
    # raises KeyError and the whole run dies.
    content = [
        {"type": "thinking", "thinking": "razmišljam..."},
        {"type": "text", "text": "B"},
    ]
    assert text_from_content(content) == "B"


def test_joins_multiple_text_blocks() -> None:
    content = [{"type": "text", "text": "B"}, {"type": "text", "text": ")"}]
    assert text_from_content(content) == "B)"


def test_content_without_any_text_block_is_empty_not_an_error() -> None:
    # A refusal or a thinking-only response must score as unparsed, not crash.
    assert text_from_content([{"type": "thinking", "thinking": "..."}]) == ""


def test_missing_content_is_empty() -> None:
    assert text_from_content([]) == ""


def test_blocks_without_a_text_key_are_skipped() -> None:
    content = [{"type": "tool_use", "id": "x", "input": {}}, {"type": "text", "text": "C"}]
    assert text_from_content(content) == "C"


# --- registration ----------------------------------------------------------


def test_model_is_registered_under_its_own_name() -> None:
    from lm_eval.api.registry import MODEL_REGISTRY

    import serbeval.lm_eval_anthropic  # noqa: F401

    assert "anthropic-chat-fixed" in MODEL_REGISTRY


def test_stock_adapter_is_left_alone() -> None:
    # Registering a new name, not monkeypatching the installed package: a pip
    # reinstall must not silently revert the fix, and the stock behaviour stays
    # available for comparison.
    from lm_eval.api.registry import MODEL_REGISTRY

    assert MODEL_REGISTRY["anthropic-chat"] is not MODEL_REGISTRY["anthropic-chat-fixed"]


# --- models where thinking cannot be turned off ----------------------------
#
# Claude Opus 5.5 (and the Fable/Mythos line) reject `thinking: {"type": "disabled"}`
# with a 400 at every effort level. The adapter's default would fail on every request.


def test_omit_mode_sends_no_thinking_parameter() -> None:
    payload = build_payload(messages=[], model="claude-opus-5-5", max_tokens=32, stop=[],
                            thinking="omit")
    assert "thinking" not in payload


def test_thinking_off_on_a_model_that_forbids_it_fails_fast_with_guidance() -> None:
    # A clear error at startup beats 1102 identical 400s halfway through a paid run.
    from serbeval.lm_eval_anthropic import check_thinking_config

    with pytest.raises(ValueError, match="model=claude-opus-5-5,thinking=omit"):
        check_thinking_config("claude-opus-5-5", "off")


@pytest.mark.parametrize(
    ("model", "thinking"),
    [
        ("claude-opus-5-5", "omit"),
        ("claude-opus-5-5", "adaptive"),
        ("claude-opus-5", "off"),
        ("claude-haiku-4-5", "off"),
    ],
)
def test_supported_thinking_configs_pass(model: str, thinking: str) -> None:
    from serbeval.lm_eval_anthropic import check_thinking_config

    check_thinking_config(model, thinking)


def test_unknown_thinking_mode_is_rejected() -> None:
    from serbeval.lm_eval_anthropic import check_thinking_config

    with pytest.raises(ValueError, match="thinking"):
        check_thinking_config("claude-opus-5", "sometimes")


def test_thinking_models_get_room_beyond_the_tasks_short_answer_cap() -> None:
    # The tasks cap generation at 24-32 tokens, sized for a bare answer. With thinking
    # on, reasoning is billed out of the same max_tokens and would exhaust it before
    # the answer, scoring every item unparsed.
    payload = build_payload(messages=[], model="claude-opus-5-5", max_tokens=32, stop=[],
                            thinking="omit")
    assert payload["max_tokens"] >= 2048


def test_short_cap_is_kept_when_thinking_is_off() -> None:
    payload = build_payload(messages=[], model="claude-opus-5", max_tokens=32, stop=[])
    assert payload["max_tokens"] == 32


def test_a_larger_explicit_cap_is_not_lowered() -> None:
    payload = build_payload(messages=[], model="claude-opus-5-5", max_tokens=8000, stop=[],
                            thinking="omit")
    assert payload["max_tokens"] == 8000


def test_project_declares_lm_evals_api_extra() -> None:
    # Without `lm-eval[api]`, tenacity and tiktoken are missing and EVERY API-backed
    # model — the stock adapter included — dies with ModuleNotFoundError. The dummy
    # model does not need them, so no dummy-based test could ever notice.
    import tomllib
    from pathlib import Path

    pyproject = tomllib.loads(
        (Path(__file__).resolve().parent.parent / "pyproject.toml").read_text(encoding="utf-8")
    )
    deps = pyproject["project"]["dependencies"]
    assert any(d.replace(" ", "").startswith("lm-eval[api]") for d in deps)
