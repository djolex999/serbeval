import pytest

from serbeval.lm_eval_kie import build_responses_payload, text_from_responses

# --- payload ---------------------------------------------------------------
#
# Kie serves gpt-6-1-sol only through `/codex/v1/responses` — OpenAI's Responses
# format (`input`, `reasoning.effort`), which lm-eval 0.4.12 has no adapter for.


def test_payload_uses_the_responses_shape() -> None:
    payload = build_responses_payload(messages="Koliko je 7 puta 8?", model="gpt-6-1-sol")
    assert payload["model"] == "gpt-6-1-sol"
    # Plain-string content: the input_text-array form returned HTTP 500 twice in a row
    # from Kie while every string-content request succeeded.
    assert payload["input"] == [{"role": "user", "content": "Koliko je 7 puta 8?"}]
    assert "messages" not in payload


def test_payload_is_non_streaming() -> None:
    assert build_responses_payload(messages="q", model="gpt-6-1-sol")["stream"] is False


def test_reasoning_effort_defaults_to_low() -> None:
    # The only cost lever this endpoint documents: it has no max-output-tokens field.
    assert build_responses_payload(messages="q", model="gpt-6-1-sol")["reasoning"] == {
        "effort": "low"
    }


def test_reasoning_effort_can_be_set() -> None:
    payload = build_responses_payload(messages="q", model="gpt-6-1-sol", effort="medium")
    assert payload["reasoning"] == {"effort": "medium"}


def test_unknown_effort_is_rejected_before_any_request() -> None:
    with pytest.raises(ValueError, match="effort"):
        build_responses_payload(messages="q", model="gpt-6-1-sol", effort="extreme")


def test_payload_sends_no_sampling_or_stop_parameters() -> None:
    # Not in Kie's schema for this model, and rejected by reasoning models generally.
    payload = build_responses_payload(messages="q", model="gpt-6-1-sol")
    for key in ("temperature", "stop", "top_p", "max_tokens", "max_completion_tokens"):
        assert key not in payload


def test_a_chat_message_list_is_converted_too() -> None:
    payload = build_responses_payload(
        messages=[{"role": "system", "content": "S"}, {"role": "user", "content": "q"}],
        model="gpt-6-1-sol",
    )
    assert [m["role"] for m in payload["input"]] == ["system", "user"]


# --- parsing ---------------------------------------------------------------


def test_reads_the_message_text_past_a_reasoning_item() -> None:
    response = {
        "output": [
            {"type": "reasoning", "id": "rs_1"},
            {
                "type": "message",
                "role": "assistant",
                "content": [{"type": "output_text", "text": "B"}],
            },
        ],
        "status": "completed",
    }
    assert text_from_responses(response) == "B"


def test_an_error_envelope_parses_as_empty_not_a_crash() -> None:
    # Kie reports some failures as {"code": ..., "msg": ...}. Empty text makes the
    # task score it `unparsed`, which is the honest outcome.
    assert text_from_responses({"code": 402, "msg": "insufficient credits"}) == ""


def test_a_data_wrapped_response_is_unwrapped() -> None:
    wrapped = {
        "code": 200,
        "data": {
            "output": [
                {"type": "message", "content": [{"type": "output_text", "text": "C"}]}
            ]
        },
    }
    assert text_from_responses(wrapped) == "C"


# --- registration and keys -------------------------------------------------


def test_model_is_registered() -> None:
    from lm_eval.api.registry import MODEL_REGISTRY

    import serbeval.lm_eval_kie  # noqa: F401

    assert "kie-responses" in MODEL_REGISTRY


def test_only_the_kie_key_is_ever_read(monkeypatch: pytest.MonkeyPatch) -> None:
    from serbeval.lm_eval_kie import kie_api_key

    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-real")
    monkeypatch.delenv("KIE_API_KEY", raising=False)
    with pytest.raises(ValueError, match="KIE_API_KEY"):
        kie_api_key()
    monkeypatch.setenv("KIE_API_KEY", "kie-key")
    assert kie_api_key() == "kie-key"


# --- construction, offline -------------------------------------------------


def test_both_adapters_construct_against_kie_without_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from serbeval.lm_eval_anthropic import AnthropicChatFixed
    from serbeval.lm_eval_kie import KieResponses

    monkeypatch.setenv("KIE_API_KEY", "kie-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-real")

    gpt = KieResponses(model="gpt-6-1-sol")
    assert gpt.header == {"Authorization": "Bearer kie-key"}

    opus = AnthropicChatFixed(
        model="claude-opus-5-5",
        base_url="https://api.kie.ai/claude/v1/messages",
        thinking="omit",
    )
    # Kie's docs say X-Api-Key; the live endpoint rejects it with HTTP 200 + code 401
    # and only accepts a Bearer token.
    assert opus.header["Authorization"] == "Bearer kie-key"
    assert "x-api-key" not in opus.header


# --- end to end through the real lm_eval CLI, against a local mock of Kie ----
#
# Every bug found so far lived in the seam between lm-eval and an adapter, where unit
# tests and the `dummy` model cannot see. This drives the real CLI over real HTTP.


@pytest.mark.slow
def test_both_kie_adapters_run_end_to_end_against_a_mock(tmp_path: object) -> None:
    import json
    import subprocess
    import sys
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from pathlib import Path

    repo = Path(__file__).resolve().parent.parent
    seen: list[dict[str, object]] = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args: object) -> None:
            pass

        def do_POST(self) -> None:
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            seen.append({"path": self.path, "body": body, "auth": dict(self.headers)})
            if self.path.startswith("/claude/"):
                out: dict[str, object] = {
                    "content": [{"type": "thinking", "thinking": ""}, {"type": "text", "text": "B"}]
                }
            else:
                out = {"output": [{"type": "reasoning"}, {"type": "message",
                       "content": [{"type": "output_text", "text": "B"}]}]}
            data = json.dumps(out).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    server = HTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    env = {**__import__("os").environ, "KIE_API_KEY": "kie", "ANTHROPIC_API_KEY": "ant",
           "OPENAI_API_KEY": "must-not-be-sent", "PYTHONPATH": str(repo / "src")}
    out_dir = Path(str(tmp_path))
    try:
        for model, args in [
            ("anthropic-chat-fixed",
             f"model=claude-opus-5-5,thinking=omit,base_url=http://127.0.0.1:{port}/claude/v1/messages"),
            ("kie-responses",
             f"model=gpt-6-1-sol,base_url=http://127.0.0.1:{port}/codex/v1/responses"),
        ]:
            done = subprocess.run(
                [sys.executable, "scripts/run_eval.py", "--model", model, "--model_args", args,
                 "--tasks", "srb_cyrillic_agreement", "--include_path", "lm_eval_tasks",
                 "--output_path", str(out_dir / model), "--log_samples", "--limit", "2"],
                cwd=repo, env=env, capture_output=True, text=True, timeout=300,
            )
            assert done.returncode == 0, done.stderr[-2000:]
    finally:
        server.shutdown()

    assert {r["path"] for r in seen} == {"/claude/v1/messages", "/codex/v1/responses"}
    for request in seen:
        body = request["body"]
        assert isinstance(body, dict)
        assert "temperature" not in body
        assert body["stream"] is False
        assert "must-not-be-sent" not in json.dumps(request["auth"])
    results = list(out_dir.rglob("results_*.json"))
    assert len(results) == 2
    for path in results:
        unparsed = json.loads(path.read_text())["results"]["srb_cyrillic_agreement"]
        assert unparsed["unparsed,extract_answer"] == 0.0



# --- error envelopes -------------------------------------------------------
#
# Kie answers an auth failure with HTTP 200 and {"code": 401, "msg": ...}. Parsed as
# "no text", every item scored unparsed and a full paid run would have finished with
# 0% and no error. Fatal account errors must stop the run instead.


@pytest.mark.parametrize("code", [401, 402, 403])
def test_fatal_envelopes_stop_the_run(code: int) -> None:
    from serbeval.lm_eval_kie import check_envelope

    with pytest.raises(RuntimeError, match=str(code)):
        check_envelope({"code": code, "msg": "nope"})


def test_a_normal_response_passes_the_envelope_check() -> None:
    from serbeval.lm_eval_kie import check_envelope

    check_envelope({"output": [], "status": "completed"})
    check_envelope({"code": 200, "data": {"output": []}})


def test_the_claude_adapter_also_stops_on_a_fatal_envelope() -> None:
    from serbeval.lm_eval_anthropic import AnthropicChatFixed

    with pytest.raises(RuntimeError, match="401"):
        AnthropicChatFixed.parse_generations(None, {"code": 401, "msg": "Unauthorized"})


def test_the_gpt_adapter_stops_on_a_fatal_envelope() -> None:
    from serbeval.lm_eval_kie import KieResponses

    with pytest.raises(RuntimeError, match="402"):
        KieResponses.parse_generations({"code": 402, "msg": "insufficient credits"})
