from types import SimpleNamespace
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

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
    assert request_json["generationConfig"]["responseModalities"] == ["Image"]
    assert "responseFormat" not in request_json["generationConfig"]
