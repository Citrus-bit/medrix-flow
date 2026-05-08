from medrix_flow.setup.service import (
    ModelSetupItem,
    SaveModelsRequest,
    get_setup_config_data,
    save_setup_config_data,
)


def test_get_setup_config_data_preserves_supports_reasoning_effort(monkeypatch):
    monkeypatch.setattr("medrix_flow.setup.service.refresh_env", lambda: None)
    monkeypatch.setattr(
        "medrix_flow.setup.service.read_raw_config",
        lambda: {
            "models": [
                {
                    "name": "gpt-5.4",
                    "use": "langchain_openai:ChatOpenAI",
                    "model": "gpt-5.4",
                    "api_key": "$OPENAI_API_KEY",
                    "supports_thinking": True,
                    "supports_reasoning_effort": True,
                    "supports_vision": True,
                }
            ]
        },
    )
    monkeypatch.setattr(
        "medrix_flow.setup.service.get_env_value",
        lambda name: "test-key" if name == "OPENAI_API_KEY" else None,
    )

    result = get_setup_config_data()

    assert len(result.models) == 1
    assert result.models[0].supports_thinking is True
    assert result.models[0].supports_reasoning_effort is True
    assert result.models[0].supports_vision is True


def test_save_setup_config_data_preserves_capability_flags(monkeypatch):
    saved_config: dict = {}
    written_env: dict[str, str] = {}

    monkeypatch.setattr("medrix_flow.setup.service.read_raw_config", lambda: {})
    monkeypatch.setattr("medrix_flow.setup.service.validate_setup_model_provider", lambda provider: None)
    monkeypatch.setattr("medrix_flow.setup.service.validate_optional_base_url", lambda base_url: None)
    monkeypatch.setattr(
        "medrix_flow.setup.service.validate_env_var_name",
        lambda env_var, allow_tool_key=False: None,
    )
    monkeypatch.setattr("medrix_flow.setup.service.set_env_value", lambda key, value: written_env.__setitem__(key, value))
    monkeypatch.setattr("medrix_flow.setup.service.write_raw_config", lambda data: saved_config.update(data))
    monkeypatch.setattr("medrix_flow.setup.service.reload_app_config", lambda: None)

    payload = SaveModelsRequest(
        models=[
            ModelSetupItem(
                name="gpt-5.4",
                provider="langchain_openai:ChatOpenAI",
                model="gpt-5.4",
                base_url=None,
                api_key="secret",
                api_key_env_var="OPENAI_API_KEY",
                max_tokens=4096,
                temperature=0.2,
                supports_thinking=True,
                supports_reasoning_effort=True,
                supports_vision=True,
            )
        ],
        tool_keys=None,
    )

    save_setup_config_data(payload)

    assert written_env["OPENAI_API_KEY"] == "secret"
    assert saved_config["models"] == [
        {
            "name": "gpt-5.4",
            "display_name": "gpt-5.4",
            "use": "langchain_openai:ChatOpenAI",
            "model": "gpt-5.4",
            "api_key": "$OPENAI_API_KEY",
            "supports_thinking": True,
            "supports_reasoning_effort": True,
            "supports_vision": True,
            "max_tokens": 4096,
            "temperature": 0.2,
        }
    ]


def test_get_setup_config_data_includes_academic_tool_keys(monkeypatch):
    monkeypatch.setattr("medrix_flow.setup.service.refresh_env", lambda: None)
    monkeypatch.setattr("medrix_flow.setup.service.read_raw_config", lambda: {"models": []})
    monkeypatch.setattr(
        "medrix_flow.setup.service.get_env_value",
        lambda name: {
            "OPENALEX_API_KEY": "oa-key",
            "SEMANTIC_SCHOLAR_API_KEY": "s2-key",
        }.get(name),
    )

    result = get_setup_config_data()

    services = {item.service: item.api_key for item in result.tool_keys}
    assert services["openalex"] == "oa-key"
    assert services["semantic-scholar"] == "s2-key"
