import pytest

from serbeval.lm_eval_openrouter import (
    build_openrouter_payload,
    openrouter_api_key,
    text_from_chat,
)

MESSAGES = [{"role": "user", "content": "Pitanje?"}]

# --- payload ---------------------------------------------------------------


def test_payload_is_a_plain_chat_completions_body() -> None:
    body = build_openrouter_payload(messages=MESSAGES, model="google/gemma-3-12b-it",
                                    max_tokens=24, stop=["\n\n"])
    assert body["model"] == "google/gemma-3-12b-it"
    assert body["messages"] == MESSAGES
    assert body["max_tokens"] == 24
    assert body["stop"] == ["\n\n"]
    assert body["temperature"] == 0
    assert body["stream"] is False


def test_reasoning_is_off_by_default() -> None:
    # qwen3 spent its whole 24-token cloze budget thinking and answered "".
    body = build_openrouter_payload(messages=MESSAGES, model="m", max_tokens=24, stop=[])
    assert body["reasoning"] == {"effort": "none"}


def test_a_reasoning_effort_also_raises_the_token_budget() -> None:
    body = build_openrouter_payload(messages=MESSAGES, model="m", max_tokens=24, stop=[],
                                    reasoning="low")
    assert body["reasoning"] == {"effort": "low"}
    assert body["max_tokens"] >= 2048


def test_reasoning_omit_sends_no_reasoning_field() -> None:
    body = build_openrouter_payload(messages=MESSAGES, model="m", max_tokens=24, stop=[],
                                    reasoning="omit")
    assert "reasoning" not in body
    assert body["max_tokens"] >= 2048


def test_unknown_reasoning_value_is_rejected() -> None:
    with pytest.raises(ValueError, match="reasoning"):
        build_openrouter_payload(messages=MESSAGES, model="m", max_tokens=24, stop=[],
                                 reasoning="extreme")


def test_empty_stop_list_is_not_sent() -> None:
    body = build_openrouter_payload(messages=MESSAGES, model="m", max_tokens=24, stop=[])
    assert "stop" not in body


def test_provider_can_be_pinned_without_fallback() -> None:
    body = build_openrouter_payload(messages=MESSAGES, model="m", max_tokens=24, stop=[],
                                    provider="DeepInfra", quantizations="bf16|fp8")
    assert body["provider"] == {
        "order": ["DeepInfra"], "allow_fallbacks": False, "quantizations": ["bf16", "fp8"],
    }


def test_no_provider_block_unless_asked() -> None:
    body = build_openrouter_payload(messages=MESSAGES, model="m", max_tokens=24, stop=[])
    assert "provider" not in body


# --- parsing ---------------------------------------------------------------


def test_reads_the_message_text() -> None:
    assert text_from_chat({"choices": [{"message": {"content": "bašti"}}]}) == "bašti"


def test_null_content_parses_as_no_text() -> None:
    # A reasoning model that runs out of tokens returns content: null.
    assert text_from_chat({"choices": [{"message": {"content": None}}]}) == ""


def test_an_error_body_parses_as_no_text() -> None:
    assert text_from_chat({"error": {"code": 500, "message": "upstream"}}) == ""


@pytest.mark.parametrize("code", [401, 402, 403])
def test_account_errors_stop_the_run(code: int) -> None:
    with pytest.raises(RuntimeError, match=str(code)):
        text_from_chat({"error": {"code": code, "message": "no credits"}})


# --- credentials -----------------------------------------------------------


def test_only_the_openrouter_key_is_ever_read(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-real")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-real")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
        openrouter_api_key()
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-key")
    assert openrouter_api_key() == "or-key"


def test_model_is_registered_and_constructs_offline(monkeypatch: pytest.MonkeyPatch) -> None:
    from lm_eval.api.registry import MODEL_REGISTRY

    from serbeval.lm_eval_openrouter import OpenRouterChat

    assert "openrouter-chat" in MODEL_REGISTRY
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-key")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-real")
    lm = OpenRouterChat(model="google/gemma-3-12b-it")
    assert lm.header["Authorization"] == "Bearer or-key"
    assert "sk-openai-real" not in str(lm.header)


# --- end to end through the real lm_eval CLI, against a local mock ------------


@pytest.mark.slow
def test_openrouter_adapter_runs_end_to_end_against_a_mock(tmp_path: object) -> None:
    import json
    import os
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
            seen.append({"body": body, "auth": dict(self.headers)})
            data = json.dumps({"provider": "MockAI",
                               "choices": [{"message": {"content": "B"}}]}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    server = HTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    env = {**os.environ, "OPENROUTER_API_KEY": "or", "OPENAI_API_KEY": "must-not-be-sent",
           "ANTHROPIC_API_KEY": "must-not-be-sent", "PYTHONPATH": str(repo / "src")}
    try:
        done = subprocess.run(
            [sys.executable, "scripts/run_eval.py", "--model", "openrouter-chat",
             "--model_args", f"model=mock/model,base_url=http://127.0.0.1:{port}/v1/chat",
             "--tasks", "srb_cyrillic_agreement", "--include_path", "lm_eval_tasks",
             "--output_path", str(tmp_path), "--log_samples", "--limit", "2"],
            cwd=repo, env=env, capture_output=True, text=True, timeout=300,
        )
        assert done.returncode == 0, done.stderr[-2000:]
    finally:
        server.shutdown()

    assert seen
    for request in seen:
        assert "must-not-be-sent" not in json.dumps(request["auth"])
        body = request["body"]
        assert isinstance(body, dict) and body["reasoning"] == {"effort": "none"}
    [results] = list(Path(str(tmp_path)).rglob("results_*.json"))
    task = json.loads(results.read_text())["results"]["srb_cyrillic_agreement"]
    assert task["unparsed,extract_answer"] == 0.0


def test_stop_sequences_can_be_turned_off_for_models_that_break_on_them() -> None:
    # cohere/command-a-plus returns content None whenever a stop sequence is sent (its
    # reply starts with a blank line), so 229 of 355 answers came back empty.
    body = build_openrouter_payload(messages=MESSAGES, model="m", max_tokens=24,
                                    stop=["\n\n"], send_stop=False)
    assert "stop" not in body
    kept = build_openrouter_payload(messages=MESSAGES, model="m", max_tokens=24, stop=["\n\n"])
    assert kept["stop"] == ["\n\n"]


def test_stop_off_is_a_model_arg(monkeypatch: pytest.MonkeyPatch) -> None:
    from serbeval.lm_eval_openrouter import OpenRouterChat

    monkeypatch.setenv("OPENROUTER_API_KEY", "or-key")
    lm = OpenRouterChat(model="cohere/command-a-plus", stop="off")
    payload = lm._create_payload(MESSAGES, gen_kwargs={"until": ["\n\n"], "max_gen_toks": 24})
    assert "stop" not in payload
    with pytest.raises(ValueError, match="stop"):
        OpenRouterChat(model="m", stop="sometimes")
