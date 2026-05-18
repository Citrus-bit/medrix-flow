from __future__ import annotations

import asyncio

import httpx
import pytest
from langchain.agents.middleware.types import ModelResponse
from langchain_core.messages import AIMessage
from langgraph.errors import GraphBubbleUp
from openai import APIError, APIStatusError, APITimeoutError, InternalServerError

from medrix_flow.agents.middlewares.model_provider_error_middleware import (
    ModelProviderErrorMiddleware,
    is_transient_model_provider_error,
)


def _provider_response(status_code: int, body: dict) -> httpx.Response:
    request = httpx.Request("POST", "https://tok.fan/v1/chat/completions")
    return httpx.Response(status_code, request=request, json=body)


def _provider_response_with_headers(status_code: int, body: dict, headers: dict[str, str]) -> httpx.Response:
    request = httpx.Request("POST", "https://tok.fan/v1/chat/completions")
    return httpx.Response(status_code, request=request, json=body, headers=headers)


def _overload_error() -> InternalServerError:
    body = {
        "error": {
            "message": "system cpu overloaded",
            "type": "x_api_error",
            "code": "system_cpu_overloaded",
        }
    }
    response = _provider_response(503, body)
    return InternalServerError("Error code: 503", response=response, body=body)


def test_model_provider_overload_retries_until_success(monkeypatch):
    middleware = ModelProviderErrorMiddleware()
    sleeps: list[float] = []
    events: list[dict] = []
    calls = 0
    success = ModelResponse(result=[AIMessage(content="done")])

    def _handler(_request):
        nonlocal calls
        calls += 1
        if calls <= 2:
            raise _overload_error()
        return success

    monkeypatch.setattr("medrix_flow.agents.middlewares.model_provider_error_middleware.time.sleep", sleeps.append)
    monkeypatch.setattr("medrix_flow.agents.middlewares.model_provider_error_middleware.get_stream_writer", lambda: events.append)

    response = middleware.wrap_model_call(object(), _handler)

    assert response is success
    assert calls == 3
    assert sleeps == [2.0, 4.0]
    assert [event["type"] for event in events] == ["model_retry", "model_retry"]
    assert events[0] == {
        "type": "model_retry",
        "attempt": 1,
        "delay_seconds": 2.0,
        "error_class": "InternalServerError",
        "status_code": 503,
        "provider_code": "system_cpu_overloaded",
        "retry_at": events[0]["retry_at"],
    }


def test_generic_api_error_with_concurrency_limit_is_transient():
    request = httpx.Request("POST", "https://tok.fan/v1/chat/completions")
    error = APIError(
        "Concurrency limit exceeded for account, please retry later",
        request,
        body=None,
    )

    assert is_transient_model_provider_error(error) is True


def test_generic_api_error_with_concurrency_limit_retries_until_success(monkeypatch):
    middleware = ModelProviderErrorMiddleware()
    request = httpx.Request("POST", "https://tok.fan/v1/chat/completions")
    error = APIError(
        "Concurrency limit exceeded for account, please retry later",
        request,
        body=None,
    )
    success = ModelResponse(result=[AIMessage(content="done")])
    calls = 0

    def _handler(_request):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise error
        return success

    monkeypatch.setattr("medrix_flow.agents.middlewares.model_provider_error_middleware.time.sleep", lambda _delay: None)

    response = middleware.wrap_model_call(object(), _handler)

    assert response is success
    assert calls == 2


def test_async_model_provider_overload_retries_until_success(monkeypatch):
    middleware = ModelProviderErrorMiddleware()
    sleeps: list[float] = []
    calls = 0
    success = ModelResponse(result=[AIMessage(content="done")])

    async def _handler(_request):
        nonlocal calls
        calls += 1
        if calls <= 2:
            raise _overload_error()
        return success

    async def _sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr("medrix_flow.agents.middlewares.model_provider_error_middleware.asyncio.sleep", _sleep)

    response = asyncio.run(middleware.awrap_model_call(object(), _handler))

    assert response is success
    assert calls == 3
    assert sleeps == [2.0, 4.0]


def test_retry_after_header_controls_retry_delay(monkeypatch):
    middleware = ModelProviderErrorMiddleware()
    sleeps: list[float] = []
    body = {
        "error": {
            "message": "temporarily unavailable",
            "code": "temporarily_unavailable",
        }
    }
    response = _provider_response_with_headers(503, body, {"Retry-After": "7"})
    error = InternalServerError("Error code: 503", response=response, body=body)
    success = ModelResponse(result=[AIMessage(content="done")])
    calls = 0

    def _handler(_request):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise error
        return success

    monkeypatch.setattr("medrix_flow.agents.middlewares.model_provider_error_middleware.time.sleep", sleeps.append)

    assert middleware.wrap_model_call(object(), _handler) is success
    assert sleeps == [7.0]


def test_retry_after_header_is_capped(monkeypatch):
    middleware = ModelProviderErrorMiddleware()
    sleeps: list[float] = []
    body = {
        "error": {
            "message": "temporarily unavailable",
            "code": "temporarily_unavailable",
        }
    }
    response = _provider_response_with_headers(503, body, {"Retry-After": "120"})
    error = InternalServerError("Error code: 503", response=response, body=body)
    success = ModelResponse(result=[AIMessage(content="done")])
    calls = 0

    def _handler(_request):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise error
        return success

    monkeypatch.setattr("medrix_flow.agents.middlewares.model_provider_error_middleware.time.sleep", sleeps.append)

    assert middleware.wrap_model_call(object(), _handler) is success
    assert sleeps == [30.0]


def test_retry_event_writer_failure_does_not_stop_retry(monkeypatch):
    middleware = ModelProviderErrorMiddleware()
    calls = 0
    success = ModelResponse(result=[AIMessage(content="done")])

    def _handler(_request):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise _overload_error()
        return success

    def _failing_writer(_event):
        raise RuntimeError("stream closed")

    monkeypatch.setattr("medrix_flow.agents.middlewares.model_provider_error_middleware.time.sleep", lambda _delay: None)
    monkeypatch.setattr("medrix_flow.agents.middlewares.model_provider_error_middleware.get_stream_writer", lambda: _failing_writer)

    assert middleware.wrap_model_call(object(), _handler) is success
    assert calls == 2


def test_generic_api_error_without_transient_signal_is_not_swallowed():
    middleware = ModelProviderErrorMiddleware()
    request = httpx.Request("POST", "https://tok.fan/v1/chat/completions")
    error = APIError("provider returned malformed JSON", request, body=None)

    def _handler(_request):
        raise error

    with pytest.raises(APIError, match="malformed JSON"):
        middleware.wrap_model_call(object(), _handler)


def test_timeout_is_classified_as_transient_provider_error():
    request = httpx.Request("POST", "https://example.invalid/v1/chat/completions")
    error = APITimeoutError(request=request)

    assert is_transient_model_provider_error(error) is True


def test_httpx_503_status_error_is_classified_as_transient_provider_error():
    request = httpx.Request("POST", "https://example.invalid/v1/responses")
    response = httpx.Response(503, request=request, json={"error": "model unavailable"})
    error = httpx.HTTPStatusError("service unavailable", request=request, response=response)

    assert is_transient_model_provider_error(error) is True


def test_httpx_401_status_error_is_not_classified_as_transient_provider_error():
    request = httpx.Request("POST", "https://example.invalid/v1/responses")
    response = httpx.Response(401, request=request, json={"error": "unauthorized"})
    error = httpx.HTTPStatusError("unauthorized", request=request, response=response)

    assert is_transient_model_provider_error(error) is False


def test_non_transient_provider_error_is_not_swallowed():
    middleware = ModelProviderErrorMiddleware()
    body = {"error": {"message": "bad request", "code": "bad_request"}}
    response = _provider_response(400, body)
    error = APIStatusError("Error code: 400", response=response, body=body)

    def _handler(_request):
        raise error

    with pytest.raises(APIStatusError):
        middleware.wrap_model_call(object(), _handler)


def test_non_provider_error_is_not_swallowed():
    middleware = ModelProviderErrorMiddleware()

    def _handler(_request):
        raise ValueError("local code bug")

    with pytest.raises(ValueError, match="local code bug"):
        middleware.wrap_model_call(object(), _handler)


def test_graph_bubble_up_is_not_retried(monkeypatch):
    middleware = ModelProviderErrorMiddleware()
    calls = 0

    def _handler(_request):
        nonlocal calls
        calls += 1
        raise GraphBubbleUp()

    monkeypatch.setattr("medrix_flow.agents.middlewares.model_provider_error_middleware.time.sleep", lambda _delay: None)

    with pytest.raises(GraphBubbleUp):
        middleware.wrap_model_call(object(), _handler)

    assert calls == 1
