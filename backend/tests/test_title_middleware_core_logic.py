"""Core behavior tests for TitleMiddleware."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

from langchain_core.messages import AIMessage, HumanMessage

from medrix_flow.agents.middlewares.title_middleware import TitleMiddleware
from medrix_flow.config.title_config import TitleConfig, get_title_config, set_title_config


def _clone_title_config(config: TitleConfig) -> TitleConfig:
    # Avoid mutating shared global config objects across tests.
    return TitleConfig(**config.model_dump())


def _set_test_title_config(**overrides) -> TitleConfig:
    config = _clone_title_config(get_title_config())
    for key, value in overrides.items():
        setattr(config, key, value)
    set_title_config(config)
    return config


class TestTitleMiddlewareCoreLogic:
    def setup_method(self):
        # Title config is a global singleton; snapshot and restore for test isolation.
        self._original = _clone_title_config(get_title_config())

    def teardown_method(self):
        set_title_config(self._original)

    def test_should_generate_title_for_first_complete_exchange(self):
        _set_test_title_config(enabled=True)
        middleware = TitleMiddleware()
        state = {
            "messages": [
                HumanMessage(content="帮我总结这段代码"),
                AIMessage(content="好的，我先看结构"),
            ]
        }

        assert middleware._should_generate_title(state) is True

    def test_should_not_generate_title_when_disabled_or_already_set(self):
        middleware = TitleMiddleware()

        _set_test_title_config(enabled=False)
        disabled_state = {
            "messages": [HumanMessage(content="Q"), AIMessage(content="A")],
            "title": None,
        }
        assert middleware._should_generate_title(disabled_state) is False

        _set_test_title_config(enabled=True)
        titled_state = {
            "messages": [HumanMessage(content="Q"), AIMessage(content="A")],
            "title": "Existing Title",
        }
        assert middleware._should_generate_title(titled_state) is False

    def test_regenerates_title_after_later_turn_when_existing_title_is_invalid(self):
        _set_test_title_config(enabled=True)
        middleware = TitleMiddleware()
        state = {
            "title": '<think> The user: "Generate a concise title (max 6 words) fo',
            "messages": [
                HumanMessage(content="第一问"),
                AIMessage(content="第一答"),
                HumanMessage(content="第二问"),
                AIMessage(content="第二答"),
            ]
        }

        assert middleware._should_generate_title(state) is True

    def test_generate_title_trims_quotes_and_respects_max_chars(self, monkeypatch):
        _set_test_title_config(max_chars=12)
        middleware = TitleMiddleware()
        fake_model = MagicMock()
        fake_model.ainvoke = AsyncMock(return_value=MagicMock(content='"A very long generated title"'))
        monkeypatch.setattr("medrix_flow.agents.middlewares.title_middleware.create_chat_model", lambda **kwargs: fake_model)

        state = {
            "messages": [
                HumanMessage(content="请帮我写一个脚本"),
                AIMessage(content="好的，先确认需求"),
            ]
        }
        result = asyncio.run(middleware._agenerate_title_result(state))
        title = result["title"]

        assert '"' not in title
        assert "'" not in title
        assert len(title) == 12

    def test_generate_title_normalizes_structured_message_and_response_content(self, monkeypatch):
        _set_test_title_config(max_chars=20)
        middleware = TitleMiddleware()
        fake_model = MagicMock()
        fake_model.ainvoke = AsyncMock(
            return_value=MagicMock(content=[{"type": "text", "text": '"结构总结"'}]),
        )
        monkeypatch.setattr(
            "medrix_flow.agents.middlewares.title_middleware.create_chat_model",
            lambda **kwargs: fake_model,
        )

        state = {
            "messages": [
                HumanMessage(content=[{"type": "text", "text": "请帮我总结这段代码"}]),
                AIMessage(content=[{"type": "text", "text": "好的，先看结构"}]),
            ]
        }

        result = asyncio.run(middleware._agenerate_title_result(state))
        title = result["title"]

        prompt = fake_model.ainvoke.await_args.args[0]
        assert "请帮我总结这段代码" in prompt
        assert "好的，先看结构" in prompt
        # Ensure structured message dict/JSON reprs are not leaking into the prompt.
        assert "{'type':" not in prompt
        assert "'type':" not in prompt
        assert '"type":' not in prompt
        assert title == "结构总结"

    def test_generate_title_fallback_when_model_fails(self, monkeypatch):
        _set_test_title_config(max_chars=20)
        middleware = TitleMiddleware()
        fake_model = MagicMock()
        fake_model.ainvoke = AsyncMock(side_effect=RuntimeError("LLM unavailable"))
        monkeypatch.setattr("medrix_flow.agents.middlewares.title_middleware.create_chat_model", lambda **kwargs: fake_model)

        state = {
            "messages": [
                HumanMessage(content="这是一个非常长的问题描述，需要被截断以形成fallback标题"),
                AIMessage(content="收到"),
            ]
        }
        result = asyncio.run(middleware._agenerate_title_result(state))
        title = result["title"]

        # Assert behavior (truncated fallback + ellipsis) without overfitting exact text.
        assert title.endswith("...")
        assert title.startswith("这是一个非常长的问题描述")

    def test_aafter_model_delegates_to_async_helper(self, monkeypatch):
        middleware = TitleMiddleware()

        monkeypatch.setattr(middleware, "_agenerate_title_result", AsyncMock(return_value={"title": "异步标题"}))
        result = asyncio.run(middleware.aafter_model({"messages": []}, runtime=MagicMock()))
        assert result == {"title": "异步标题"}

        monkeypatch.setattr(middleware, "_agenerate_title_result", AsyncMock(return_value=None))
        assert asyncio.run(middleware.aafter_model({"messages": []}, runtime=MagicMock())) is None

    def test_after_model_sync_delegates_to_sync_helper(self, monkeypatch):
        middleware = TitleMiddleware()

        monkeypatch.setattr(middleware, "_generate_title_result", MagicMock(return_value={"title": "同步标题"}))
        result = middleware.after_model({"messages": []}, runtime=MagicMock())
        assert result == {"title": "同步标题"}

        monkeypatch.setattr(middleware, "_generate_title_result", MagicMock(return_value=None))
        assert middleware.after_model({"messages": []}, runtime=MagicMock()) is None

    def test_sync_generate_title_with_model(self, monkeypatch):
        """Sync path calls model.invoke and produces a title."""
        _set_test_title_config(max_chars=20)
        middleware = TitleMiddleware()
        fake_model = MagicMock()
        fake_model.invoke = MagicMock(return_value=MagicMock(content='"同步生成的标题"'))
        monkeypatch.setattr("medrix_flow.agents.middlewares.title_middleware.create_chat_model", lambda **kwargs: fake_model)

        state = {
            "messages": [
                HumanMessage(content="请帮我写测试"),
                AIMessage(content="好的"),
            ]
        }
        result = middleware._generate_title_result(state)
        assert result == {"title": "同步生成的标题"}
        fake_model.invoke.assert_called_once()

    def test_empty_title_falls_back(self, monkeypatch):
        """Empty model response triggers fallback title."""
        _set_test_title_config(max_chars=50)
        middleware = TitleMiddleware()
        fake_model = MagicMock()
        fake_model.invoke = MagicMock(return_value=MagicMock(content="   "))
        monkeypatch.setattr("medrix_flow.agents.middlewares.title_middleware.create_chat_model", lambda **kwargs: fake_model)

        state = {
            "messages": [
                HumanMessage(content="空标题测试"),
                AIMessage(content="回复"),
            ]
        }
        result = middleware._generate_title_result(state)
        assert result["title"] == "空标题测试"

    def test_parse_title_strips_reasoning_blocks(self):
        _set_test_title_config(max_chars=80)
        middleware = TitleMiddleware()

        title = middleware._parse_title(
            "<think>The model should infer a concise topic title.</think>\n"
            "Title: VCFM Literature Review",
        )

        assert title == "VCFM Literature Review"

    def test_prompt_echo_title_falls_back_to_user_topic(self, monkeypatch):
        _set_test_title_config(max_chars=50)
        middleware = TitleMiddleware()
        fake_model = MagicMock()
        fake_model.invoke = MagicMock(
            return_value=MagicMock(
                content='<think> The user: "Generate a concise title (max 6 words) fo',
            ),
        )
        monkeypatch.setattr(
            "medrix_flow.agents.middlewares.title_middleware.create_chat_model",
            lambda **kwargs: fake_model,
        )

        state = {
            "messages": [
                HumanMessage(content="GNN和MLP在Virtual Cell Foundation Model中的局限与突破方向"),
                AIMessage(content="我会从文献覆盖、证据链和评估框架入手。"),
            ]
        }

        result = middleware._generate_title_result(state)

        assert result["title"].startswith("GNN和MLP在Virtual Cell Foundation Model")

    def test_existing_title_with_closed_think_block_is_normalized_without_model(self, monkeypatch):
        _set_test_title_config(max_chars=80)
        middleware = TitleMiddleware()
        fake_model = MagicMock()
        fake_model.invoke = MagicMock()
        monkeypatch.setattr(
            "medrix_flow.agents.middlewares.title_middleware.create_chat_model",
            lambda **kwargs: fake_model,
        )

        state = {
            "title": "<think>reasoning trace</think>\nTitle: Claim-Level Evidence Audit",
            "messages": [
                HumanMessage(content="请检查论文引用质量"),
                AIMessage(content="我会做质量审查。"),
            ],
        }

        result = middleware._generate_title_result(state)

        assert result == {"title": "Claim-Level Evidence Audit"}
        fake_model.invoke.assert_not_called()
