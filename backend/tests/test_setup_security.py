from __future__ import annotations

import pytest

from medrix_flow.setup.security import (
    validate_env_var_name,
    validate_optional_base_url,
    validate_setup_model_provider,
)


def test_validate_setup_model_provider_rejects_unknown_provider() -> None:
    with pytest.raises(ValueError, match="Unsupported model provider"):
        validate_setup_model_provider("os:path")


def test_validate_optional_base_url_rejects_non_http_scheme() -> None:
    with pytest.raises(ValueError, match="absolute http\\(s\\) URL"):
        validate_optional_base_url("file:///tmp/evil")


def test_validate_env_var_name_rejects_invalid_characters() -> None:
    with pytest.raises(ValueError, match="Invalid environment variable name"):
        validate_env_var_name("BAD-NAME")


def test_validate_env_var_name_rejects_unapproved_tool_key_variable() -> None:
    with pytest.raises(ValueError, match="Unsupported tool API key env var"):
        validate_env_var_name("OPENAI_API_KEY", allow_tool_key=True)
