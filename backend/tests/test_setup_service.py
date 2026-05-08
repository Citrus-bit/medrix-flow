from medrix_flow.setup.service import (
    DEFAULT_GOOGLE_IMAGE_MODEL,
    IMAGE_PROVIDER_GOOGLE,
    IMAGE_PROVIDER_OPENAI,
    ImageGenerationConfig,
    ImageProviderConfig,
    ModelSetupItem,
    SaveModelsRequest,
    get_setup_config_data,
    normalize_model_env_var_name,
    save_setup_config_data,
)


def _make_image_generation_config(
    *,
    active_provider: str = IMAGE_PROVIDER_GOOGLE,
    google_model: str = DEFAULT_GOOGLE_IMAGE_MODEL,
    google_api_key: str | None = "gemini-key",
    openai_model: str | None = None,
    openai_base_url: str | None = None,
    openai_api_key: str | None = None,
) -> ImageGenerationConfig:
    return ImageGenerationConfig(
        active_provider=active_provider,
        google_ai_studio=ImageProviderConfig(
            provider=IMAGE_PROVIDER_GOOGLE,
            enabled=active_provider == IMAGE_PROVIDER_GOOGLE,
            model=google_model,
            api_key=google_api_key,
            api_key_env_var="GEMINI_API_KEY",
        ),
        openai_compatible=ImageProviderConfig(
            provider=IMAGE_PROVIDER_OPENAI,
            enabled=active_provider == IMAGE_PROVIDER_OPENAI,
            model=openai_model,
            base_url=openai_base_url,
            api_key=openai_api_key,
            api_key_env_var="IMAGE_GEN_OPENAI_API_KEY",
        ),
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
        image_generation=None,
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
            "GEMINI_API_KEY": "gemini-key",
            "OPENALEX_API_KEY": "oa-key",
            "SEMANTIC_SCHOLAR_API_KEY": "s2-key",
            "IMAGE_GEN_ACTIVE_PROVIDER": IMAGE_PROVIDER_GOOGLE,
        }.get(name),
    )

    result = get_setup_config_data()

    services = {item.service: item.api_key for item in result.tool_keys}
    assert services["openalex"] == "oa-key"
    assert services["semantic-scholar"] == "s2-key"
    assert result.image_generation.active_provider == IMAGE_PROVIDER_GOOGLE
    assert result.image_generation.google_ai_studio.api_key == "gemini-key"


def test_save_setup_config_data_syncs_google_ai_studio_alias_env_vars(monkeypatch):
    written_env: dict[str, str] = {}

    monkeypatch.setattr("medrix_flow.setup.service.read_raw_config", lambda: {"models": []})
    monkeypatch.setattr("medrix_flow.setup.service.write_raw_config", lambda data: None)
    monkeypatch.setattr("medrix_flow.setup.service.reload_app_config", lambda: None)
    monkeypatch.setattr("medrix_flow.setup.service.validate_setup_model_provider", lambda provider: None)
    monkeypatch.setattr("medrix_flow.setup.service.validate_optional_base_url", lambda base_url: None)
    monkeypatch.setattr("medrix_flow.setup.service.validate_env_var_name", lambda env_var, allow_tool_key=False: None)
    monkeypatch.setattr("medrix_flow.setup.service.set_env_value", lambda key, value: written_env.__setitem__(key, value))

    payload = SaveModelsRequest(
        models=[],
        tool_keys=[
            {
                "service": "google-ai-studio",
                "api_key": "google-studio-key",
                "env_var": "GEMINI_API_KEY",
            }
        ],
        image_generation=None,
    )

    save_setup_config_data(payload)

    assert written_env["GEMINI_API_KEY"] == "google-studio-key"
    assert written_env["GOOGLE_API_KEY"] == "google-studio-key"


def test_normalize_model_env_var_name_replaces_legacy_dots() -> None:
    assert normalize_model_env_var_name("MINIMAX_M2.7_API_KEY") == "MINIMAX_M2_7_API_KEY"
    assert normalize_model_env_var_name("gpt-5.4") == "GPT_5_4_API_KEY"


def test_get_setup_config_data_normalizes_legacy_model_env_var_names(monkeypatch):
    monkeypatch.setattr("medrix_flow.setup.service.refresh_env", lambda: None)
    monkeypatch.setattr(
        "medrix_flow.setup.service.read_raw_config",
        lambda: {
            "models": [
                {
                    "name": "MiniMax-M2.7",
                    "use": "langchain_openai:ChatOpenAI",
                    "model": "MiniMax-M2.7",
                    "api_key": "$MINIMAX_M2.7_API_KEY",
                }
            ]
        },
    )
    monkeypatch.setattr(
        "medrix_flow.setup.service.get_env_value",
        lambda name: "legacy-key" if name == "MINIMAX_M2.7_API_KEY" else None,
    )

    result = get_setup_config_data()

    assert result.models[0].api_key_env_var == "MINIMAX_M2_7_API_KEY"
    assert result.models[0].api_key == "legacy-key"


def test_save_setup_config_data_migrates_legacy_model_env_var_names(monkeypatch):
    written_env: dict[str, str] = {}
    saved_config: dict = {}

    monkeypatch.setattr("medrix_flow.setup.service.read_raw_config", lambda: {})
    monkeypatch.setattr("medrix_flow.setup.service.write_raw_config", lambda data: saved_config.update(data))
    monkeypatch.setattr("medrix_flow.setup.service.reload_app_config", lambda: None)
    monkeypatch.setattr("medrix_flow.setup.service.validate_setup_model_provider", lambda provider: None)
    monkeypatch.setattr("medrix_flow.setup.service.validate_optional_base_url", lambda base_url: None)
    monkeypatch.setattr("medrix_flow.setup.service.set_env_value", lambda key, value: written_env.__setitem__(key, value))

    payload = SaveModelsRequest(
        models=[
            ModelSetupItem(
                name="MiniMax-M2.7",
                provider="langchain_openai:ChatOpenAI",
                model="MiniMax-M2.7",
                api_key="secret",
                api_key_env_var="MINIMAX_M2.7_API_KEY",
            )
        ],
        tool_keys=[],
        image_generation=None,
    )

    save_setup_config_data(payload)

    assert written_env["MINIMAX_M2_7_API_KEY"] == "secret"
    assert saved_config["models"][0]["api_key"] == "$MINIMAX_M2_7_API_KEY"


def test_get_setup_config_data_loads_image_generation_config(monkeypatch):
    monkeypatch.setattr("medrix_flow.setup.service.refresh_env", lambda: None)
    monkeypatch.setattr(
        "medrix_flow.setup.service.read_raw_config",
        lambda: {
            "models": [],
            "image_generation": {
                "active_provider": IMAGE_PROVIDER_OPENAI,
                "google_ai_studio": {"model": "gemini-3-pro-image-preview"},
                "openai_compatible": {
                    "model": "gpt-image-1",
                    "base_url": "https://images.example.com/v1/",
                },
            },
        },
    )
    monkeypatch.setattr(
        "medrix_flow.setup.service.get_env_value",
        lambda name: {
            "GEMINI_API_KEY": "gemini-key",
            "IMAGE_GEN_OPENAI_API_KEY": "openai-image-key",
        }.get(name),
    )

    result = get_setup_config_data()

    assert result.image_generation.active_provider == IMAGE_PROVIDER_OPENAI
    assert result.image_generation.google_ai_studio.model == "gemini-3-pro-image-preview"
    assert result.image_generation.openai_compatible.model == "gpt-image-1"
    assert result.image_generation.openai_compatible.base_url == "https://images.example.com/v1"
    assert result.image_generation.openai_compatible.api_key == "openai-image-key"


def test_save_setup_config_data_persists_image_generation_config(monkeypatch):
    written_env: dict[str, str] = {}
    saved_config: dict = {}

    monkeypatch.setattr("medrix_flow.setup.service.read_raw_config", lambda: {"models": []})
    monkeypatch.setattr("medrix_flow.setup.service.write_raw_config", lambda data: saved_config.update(data))
    monkeypatch.setattr("medrix_flow.setup.service.reload_app_config", lambda: None)
    monkeypatch.setattr("medrix_flow.setup.service.validate_setup_model_provider", lambda provider: None)
    monkeypatch.setattr("medrix_flow.setup.service.validate_optional_base_url", lambda base_url: None)
    monkeypatch.setattr("medrix_flow.setup.service.validate_env_var_name", lambda env_var, allow_tool_key=False: None)
    monkeypatch.setattr("medrix_flow.setup.service.set_env_value", lambda key, value: written_env.__setitem__(key, value))

    payload = SaveModelsRequest(
        models=[],
        tool_keys=[],
        image_generation=_make_image_generation_config(
            active_provider=IMAGE_PROVIDER_OPENAI,
            openai_model="gpt-image-1",
            openai_base_url="https://images.example.com/v1/",
            openai_api_key="openai-image-key",
        ),
    )

    save_setup_config_data(payload)

    assert saved_config["image_generation"] == {
        "active_provider": IMAGE_PROVIDER_OPENAI,
        "google_ai_studio": {"model": DEFAULT_GOOGLE_IMAGE_MODEL},
        "openai_compatible": {
            "model": "gpt-image-1",
            "base_url": "https://images.example.com/v1",
        },
    }
    assert written_env["IMAGE_GEN_ACTIVE_PROVIDER"] == IMAGE_PROVIDER_OPENAI
    assert written_env["IMAGE_GEN_GOOGLE_MODEL"] == DEFAULT_GOOGLE_IMAGE_MODEL
    assert written_env["IMAGE_GEN_OPENAI_MODEL"] == "gpt-image-1"
    assert written_env["IMAGE_GEN_OPENAI_BASE_URL"] == "https://images.example.com/v1"
    assert written_env["IMAGE_GEN_OPENAI_API_KEY"] == "openai-image-key"


def test_save_setup_config_data_requires_active_image_provider_fields(monkeypatch):
    monkeypatch.setattr("medrix_flow.setup.service.read_raw_config", lambda: {"models": []})
    monkeypatch.setattr("medrix_flow.setup.service.write_raw_config", lambda data: None)
    monkeypatch.setattr("medrix_flow.setup.service.reload_app_config", lambda: None)
    monkeypatch.setattr("medrix_flow.setup.service.validate_setup_model_provider", lambda provider: None)
    monkeypatch.setattr("medrix_flow.setup.service.validate_optional_base_url", lambda base_url: None)
    monkeypatch.setattr("medrix_flow.setup.service.validate_env_var_name", lambda env_var, allow_tool_key=False: None)
    monkeypatch.setattr("medrix_flow.setup.service.set_env_value", lambda key, value: None)

    payload = SaveModelsRequest(
        models=[],
        tool_keys=[],
        image_generation=_make_image_generation_config(active_provider=IMAGE_PROVIDER_OPENAI),
    )

    try:
        save_setup_config_data(payload)
        assert False, "Expected active image provider validation to fail"
    except ValueError as exc:
        assert "requires a model" in str(exc)
