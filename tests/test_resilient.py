from typing import Any

import pytest
import requests

from serbeval.lm_eval_anthropic import TRANSIENT_FAILURE, post_with_patience


class FakeResponse:
    def __init__(self, status: int, body: dict[str, Any] | None = None) -> None:
        self.status_code = status
        self.ok = status < 400
        self._body = body or {}
        self.text = str(self._body)

    def json(self) -> dict[str, Any]:
        return self._body

    def raise_for_status(self) -> None:
        if not self.ok:
            raise requests.HTTPError(f"{self.status_code}", response=self)  # type: ignore[arg-type]


def poster(*statuses: int) -> tuple[Any, list[int]]:
    calls: list[int] = []

    def post(url: str, **kwargs: Any) -> FakeResponse:
        status = statuses[min(len(calls), len(statuses) - 1)]
        calls.append(status)
        return FakeResponse(status, {"ok": True} if status == 200 else {"error": "x"})

    return post, calls


def no_sleep(_: float) -> None:
    pass


def test_returns_the_body_on_success() -> None:
    post, calls = poster(200)
    assert post_with_patience(post, "u", {}, {}, attempts=5, sleep=no_sleep) == {"ok": True}
    assert calls == [200]


def test_rides_out_a_streak_of_server_errors() -> None:
    # Kie returned 500 six times in 35 s on one request; lm-eval's own retry gave up and
    # threw away the 17 answers already collected in that run.
    post, calls = poster(500, 500, 500, 500, 200)
    assert post_with_patience(post, "u", {}, {}, attempts=6, sleep=no_sleep) == {"ok": True}
    assert len(calls) == 5


def test_rate_limits_are_transient_too() -> None:
    post, _ = poster(429, 200)
    assert post_with_patience(post, "u", {}, {}, attempts=3, sleep=no_sleep) == {"ok": True}


def test_gives_up_on_one_item_without_killing_the_run() -> None:
    post, calls = poster(500)
    assert post_with_patience(post, "u", {}, {}, attempts=4, sleep=no_sleep) == TRANSIENT_FAILURE
    assert len(calls) == 4


def test_connection_errors_are_transient() -> None:
    attempts: list[int] = []

    def post(url: str, **kwargs: Any) -> FakeResponse:
        attempts.append(1)
        if len(attempts) < 3:
            raise requests.ConnectionError("reset")
        return FakeResponse(200, {"ok": True})

    assert post_with_patience(post, "u", {}, {}, attempts=5, sleep=no_sleep) == {"ok": True}


@pytest.mark.parametrize("status", [400, 401, 403, 404])
def test_client_errors_stop_immediately(status: int) -> None:
    # A bad request or bad credentials will fail identically on every item; retrying
    # or skipping would just burn time and hide the cause.
    post, calls = poster(status)
    with pytest.raises(requests.HTTPError):
        post_with_patience(post, "u", {}, {}, attempts=5, sleep=no_sleep)
    assert len(calls) == 1


def test_backoff_grows_and_is_capped() -> None:
    waits: list[float] = []
    post, _ = poster(500)
    post_with_patience(post, "u", {}, {}, attempts=7, sleep=waits.append)
    assert waits == sorted(waits)
    assert max(waits) <= 60
    assert len(waits) == 6


def test_a_transient_failure_parses_as_an_unreadable_answer() -> None:
    from serbeval.lm_eval_anthropic import AnthropicChatFixed, text_from_content
    from serbeval.lm_eval_kie import KieResponses

    assert AnthropicChatFixed.parse_generations(None, TRANSIENT_FAILURE) == [""]
    assert KieResponses.parse_generations(TRANSIENT_FAILURE) == [""]
    assert text_from_content([]) == ""
