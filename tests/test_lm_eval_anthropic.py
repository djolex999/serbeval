
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
