from types import SimpleNamespace
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
import requests

from app.gateway.routers import setup


def test_setup_test_tool_key_supports_openalex() -> None:
    app = FastAPI()
    app.include_router(setup.router)

    with patch("app.gateway.routers.setup.refresh_env", lambda: None):
        with patch("requests.get", return_value=SimpleNamespace(status_code=200)) as mock_get:
            with TestClient(app) as client:
                response = client.post(
                    "/api/setup/test-tool-key",
                    json={"service": "openalex", "api_key": "oa-key"},
                )

    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "OpenAlex API key is valid."}
    mock_get.assert_called_once()


def test_setup_test_tool_key_supports_semantic_scholar() -> None:
    app = FastAPI()
    app.include_router(setup.router)

    with patch("app.gateway.routers.setup.refresh_env", lambda: None):
        with patch("requests.get", return_value=SimpleNamespace(status_code=200)) as mock_get:
            with TestClient(app) as client:
                response = client.post(
                    "/api/setup/test-tool-key",
                    json={"service": "semantic-scholar", "api_key": "s2-key"},
                )

    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "Semantic Scholar API key is valid."}
    mock_get.assert_called_once()


def test_setup_test_tool_key_supports_google_ai_studio() -> None:
    app = FastAPI()
    app.include_router(setup.router)

    fake_payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "inlineData": {
                                "mimeType": "image/png",
                                "data": "ZmFrZQ==",
                            }
                        }
                    ]
                }
            }
        ]
    }

    class FakeResponse:
        status_code = 200

        @staticmethod
        def json():
            return fake_payload

    with patch("app.gateway.routers.setup.refresh_env", lambda: None):
        with patch("requests.post", return_value=FakeResponse()) as mock_post:
            with TestClient(app) as client:
                response = client.post(
                    "/api/setup/test-tool-key",
                    json={"service": "google-ai-studio", "api_key": "google-key"},
                )

    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "Google AI Studio API key is valid for image generation."}
    mock_post.assert_called_once()
    request_json = mock_post.call_args.kwargs["json"]
    assert request_json == setup.build_google_image_smoke_request(model=setup.GOOGLE_IMAGE_SMOKE_MODEL)
    assert request_json["generationConfig"]["imageConfig"]["aspectRatio"] == "1:1"
    assert request_json["generationConfig"]["imageConfig"]["imageSize"] == "1K"


def test_setup_test_image_provider_supports_google_ai_studio() -> None:
    app = FastAPI()
    app.include_router(setup.router)

    fake_payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "inlineData": {
                                "mimeType": "image/png",
                                "data": "ZmFrZQ==",
                            }
                        }
                    ]
                }
            }
        ]
    }

    class FakeResponse:
        status_code = 200

        @staticmethod
        def json():
            return fake_payload

    with patch("app.gateway.routers.setup.refresh_env", lambda: None):
        with patch("app.gateway.routers.setup.requests.post", return_value=FakeResponse()) as mock_post:
            with TestClient(app) as client:
                response = client.post(
                    "/api/setup/test-image-provider",
                    json={
                        "provider": "google-ai-studio",
                        "model": "gemini-3-pro-image-preview",
                        "api_key": "google-key",
                    },
                )

    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "Google AI Studio API key is valid for image generation."}
    mock_post.assert_called_once()
    assert mock_post.call_args.args[0].endswith("/models/gemini-3-pro-image-preview:generateContent")
    request_json = mock_post.call_args.kwargs["json"]
    assert request_json["generationConfig"]["imageConfig"]["aspectRatio"] == "1:1"
    assert request_json["generationConfig"]["imageConfig"]["imageSize"] == "1K"


def test_setup_test_image_provider_surfaces_google_response_summary_when_no_image_is_returned() -> None:
    app = FastAPI()
    app.include_router(setup.router)

    class FakeResponse:
        status_code = 200

        @staticmethod
        def json():
            return {
                "candidates": [
                    {
                        "finishReason": "STOP",
                        "content": {
                            "parts": [
                                {
                                    "text": "The model returned text instead of an image.",
                                }
                            ]
                        },
                    }
                ]
            }

    with patch("app.gateway.routers.setup.refresh_env", lambda: None):
        with patch("app.gateway.routers.setup.requests.post", return_value=FakeResponse()):
            with TestClient(app) as client:
                response = client.post(
                    "/api/setup/test-image-provider",
                    json={
                        "provider": "google-ai-studio",
                        "model": "gemini-3-pro-image-preview",
                        "api_key": "google-key",
                    },
                )

    assert response.status_code == 200
    assert response.json()["success"] is False
    assert "finish_reason=STOP" in response.json()["message"]
    assert "returned text instead of an image" in response.json()["message"]


def test_setup_test_image_provider_surfaces_google_503_as_upstream_availability_issue() -> None:
    app = FastAPI()
    app.include_router(setup.router)

    class FakeResponse:
        status_code = 503

        @staticmethod
        def json():
            return {}

    with patch("app.gateway.routers.setup.refresh_env", lambda: None):
        with patch("medrix_flow.utils.google_image.time.sleep", lambda *_args, **_kwargs: None):
            with patch("app.gateway.routers.setup.requests.post", return_value=FakeResponse()):
                with TestClient(app) as client:
                    response = client.post(
                        "/api/setup/test-image-provider",
                        json={
                            "provider": "google-ai-studio",
                            "model": "gemini-3-pro-image-preview",
                            "api_key": "google-key",
                        },
                    )

    assert response.status_code == 200
    assert response.json()["success"] is False
    assert "status 503" in response.json()["message"]
    assert "temporarily unavailable or overloaded" in response.json()["message"]


def test_setup_test_image_provider_surfaces_google_invalid_argument_details() -> None:
    app = FastAPI()
    app.include_router(setup.router)

    class FakeResponse:
        status_code = 400

        @staticmethod
        def json():
            return {
                "error": {
                    "code": 400,
                    "message": "Invalid JSON payload received. Unknown name 'responseFormat' at 'generation_config'.",
                }
            }

    with patch("app.gateway.routers.setup.refresh_env", lambda: None):
        with patch("app.gateway.routers.setup.requests.post", return_value=FakeResponse()) as mock_post:
            with TestClient(app) as client:
                response = client.post(
                    "/api/setup/test-image-provider",
                    json={
                        "provider": "google-ai-studio",
                        "model": "gemini-3-pro-image-preview",
                        "api_key": "google-key",
                    },
                )

    assert response.status_code == 200
    assert response.json()["success"] is False
    assert "status 400" in response.json()["message"]
    assert "Unknown name 'responseFormat'" in response.json()["message"]
    assert mock_post.call_count == 1


def test_setup_test_image_provider_retries_google_503_then_succeeds() -> None:
    app = FastAPI()
    app.include_router(setup.router)

    success_payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "inlineData": {
                                "mimeType": "image/png",
                                "data": "ZmFrZQ==",
                            }
                        }
                    ]
                }
            }
        ]
    }

    class FakeUnavailableResponse:
        status_code = 503

        @staticmethod
        def json():
            return {
                "error": {
                    "code": 503,
                    "message": "This model is currently experiencing high demand.",
                }
            }

    class FakeSuccessResponse:
        status_code = 200

        @staticmethod
        def json():
            return success_payload

    with patch("app.gateway.routers.setup.refresh_env", lambda: None):
        with patch("medrix_flow.utils.google_image.time.sleep", lambda *_args, **_kwargs: None):
            with patch(
                "app.gateway.routers.setup.requests.post",
                side_effect=[FakeUnavailableResponse(), FakeSuccessResponse()],
            ) as mock_post:
                with TestClient(app) as client:
                    response = client.post(
                        "/api/setup/test-image-provider",
                        json={
                            "provider": "google-ai-studio",
                            "model": "gemini-3-pro-image-preview",
                            "api_key": "google-key",
                        },
                    )

    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "Google AI Studio API key is valid for image generation."}
    assert mock_post.call_count == 2


def test_setup_test_image_provider_retries_google_timeout_then_succeeds() -> None:
    app = FastAPI()
    app.include_router(setup.router)

    success_payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "inlineData": {
                                "mimeType": "image/png",
                                "data": "ZmFrZQ==",
                            }
                        }
                    ]
                }
            }
        ]
    }

    class FakeSuccessResponse:
        status_code = 200

        @staticmethod
        def json():
            return success_payload

    with patch("app.gateway.routers.setup.refresh_env", lambda: None):
        with patch("medrix_flow.utils.google_image.time.sleep", lambda *_args, **_kwargs: None):
            with patch(
                "app.gateway.routers.setup.requests.post",
                side_effect=[requests.exceptions.Timeout("timed out"), FakeSuccessResponse()],
            ) as mock_post:
                with TestClient(app) as client:
                    response = client.post(
                        "/api/setup/test-image-provider",
                        json={
                            "provider": "google-ai-studio",
                            "model": "gemini-3-pro-image-preview",
                            "api_key": "google-key",
                        },
                    )

    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "Google AI Studio API key is valid for image generation."}
    assert mock_post.call_count == 2


def test_setup_test_image_provider_retries_google_503_then_fails() -> None:
    app = FastAPI()
    app.include_router(setup.router)

    class FakeUnavailableResponse:
        status_code = 503

        @staticmethod
        def json():
            return {
                "error": {
                    "code": 503,
                    "message": "This model is currently experiencing high demand.",
                }
            }

    with patch("app.gateway.routers.setup.refresh_env", lambda: None):
        with patch("medrix_flow.utils.google_image.time.sleep", lambda *_args, **_kwargs: None):
            with patch(
                "app.gateway.routers.setup.requests.post",
                side_effect=[FakeUnavailableResponse(), FakeUnavailableResponse(), FakeUnavailableResponse()],
            ) as mock_post:
                with TestClient(app) as client:
                    response = client.post(
                        "/api/setup/test-image-provider",
                        json={
                            "provider": "google-ai-studio",
                            "model": "gemini-3-pro-image-preview",
                            "api_key": "google-key",
                        },
                    )

    assert response.status_code == 200
    assert response.json()["success"] is False
    assert "status 503" in response.json()["message"]
    assert "temporarily unavailable or overloaded" in response.json()["message"]
    assert mock_post.call_count == 3


def test_setup_test_image_provider_supports_openai_compatible_b64_json() -> None:
    app = FastAPI()
    app.include_router(setup.router)

    class FakeResponse:
        status_code = 200

        @staticmethod
        def json():
            return {"data": [{"b64_json": "ZmFrZQ=="}]}

    with patch("app.gateway.routers.setup.refresh_env", lambda: None):
        with patch("app.gateway.routers.setup.requests.post", return_value=FakeResponse()) as mock_post:
            with TestClient(app) as client:
                response = client.post(
                    "/api/setup/test-image-provider",
                    json={
                        "provider": "openai-compatible",
                        "model": "gpt-image-1",
                        "api_key": "openai-key",
                        "base_url": "https://images.example.com/v1/",
                    },
                )

    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "OpenAI-compatible image provider is valid for image generation."}
    mock_post.assert_called_once()
    assert mock_post.call_args.args[0] == "https://images.example.com/v1/images/generations"


def test_setup_test_image_provider_supports_openai_compatible_url_result() -> None:
    app = FastAPI()
    app.include_router(setup.router)

    class FakeResponse:
        status_code = 200

        @staticmethod
        def json():
            return {"data": [{"url": "https://cdn.example.com/output.png"}]}

    with patch("app.gateway.routers.setup.refresh_env", lambda: None):
        with patch("app.gateway.routers.setup.requests.post", return_value=FakeResponse()):
            with TestClient(app) as client:
                response = client.post(
                    "/api/setup/test-image-provider",
                    json={
                        "provider": "openai-compatible",
                        "model": "gpt-image-1",
                        "api_key": "openai-key",
                        "base_url": "https://images.example.com/v1",
                    },
                )

    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "OpenAI-compatible image provider is valid for image generation."}
