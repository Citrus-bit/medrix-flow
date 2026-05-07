from __future__ import annotations

import pytest

from medrix_flow.config.app_config import AppConfig
from medrix_flow.config.sandbox_config import SandboxConfig
from medrix_flow.sandbox.security import enforce_safe_sandbox_configuration


def test_enforce_safe_sandbox_configuration_rejects_local_provider_in_production(monkeypatch) -> None:
    config = AppConfig(
        models=[],
        sandbox=SandboxConfig(use="medrix_flow.sandbox.local:LocalSandboxProvider"),
        tools=[],
        tool_groups=[],
    )
    monkeypatch.setenv("NODE_ENV", "production")

    with pytest.raises(RuntimeError, match="LocalSandboxProvider is not allowed in production"):
        enforce_safe_sandbox_configuration(config)


def test_enforce_safe_sandbox_configuration_honors_medrix_flow_env(monkeypatch) -> None:
    config = AppConfig(
        models=[],
        sandbox=SandboxConfig(use="medrix_flow.sandbox.local:LocalSandboxProvider"),
        tools=[],
        tool_groups=[],
    )
    monkeypatch.delenv("NODE_ENV", raising=False)
    monkeypatch.setenv("MEDRIX_FLOW_ENV", "production")

    with pytest.raises(RuntimeError, match="LocalSandboxProvider is not allowed in production"):
        enforce_safe_sandbox_configuration(config)
