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
