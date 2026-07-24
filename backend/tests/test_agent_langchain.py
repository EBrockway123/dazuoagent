"""LangChain agent wiring tests.

Three layers:

* **Pure** — `_extract_tool_calls` and `_suggested_actions` over
  LangChain message history (no API calls).
* **Provider routing** — `_build_llm()` returns the right client class
  per `llm_provider` setting, with the configured key + base_url.
* **Real DeepSeek** — gated on `DEEPSEEK_API_KEY` in `.env`. Skipped in
  CI; run manually when verifying a new model release.
"""

from __future__ import annotations

from langchain_core.messages import AIMessage, ToolMessage

from dazuoagent.agent.agent import _extract_tool_calls, _suggested_actions


# ---------------------------------------------------------------------------
# Pure: extractor + suggestions
# ---------------------------------------------------------------------------


def test_extract_tool_calls_pulls_calls_and_final_reply() -> None:
    # Plain dicts with `id` — LangChain 1.x wraps them through
    # `create_tool_call` internally; this keeps the test free of internal
    # helpers that move between versions.
    tc_dict = {"name": "list_materials", "args": {"keyword": "白"}, "id": "call-1"}
    messages = [
        AIMessage(content="thinking...", tool_calls=[tc_dict]),
        ToolMessage(content='[{"sku": "PB-18-MLM-WHITE"}]', tool_call_id="call-1"),
        AIMessage(content="推荐使用颗粒板白色."),
    ]
    calls, last = _extract_tool_calls(messages)
    assert len(calls) == 1
    assert calls[0]["name"] == "list_materials"
    assert calls[0]["args"] == {"keyword": "白"}
    assert last == "推荐使用颗粒板白色."


def test_extract_tool_calls_handles_no_tool_calls() -> None:
    calls, last = _extract_tool_calls([AIMessage(content="你好,有什么可以帮你?")])
    assert calls == []
    assert last == "你好,有什么可以帮你?"


def test_extract_tool_calls_handles_list_content() -> None:
    """Some chat models return content as a list of content-blocks; flatten to text."""
    calls, last = _extract_tool_calls(
        [AIMessage(content=[{"type": "text", "text": "块1 "}, {"type": "text", "text": "块2"}])],
    )
    assert calls == []
    assert last == "块1 块2"


def test_suggested_actions_reflect_tool_call_history() -> None:
    """`_suggested_actions` looks at which tools were invoked and surfaces
    the matching follow-up chip; falls back to the generic three."""
    assert "浏览素材库" in _suggested_actions([])
    actions = _suggested_actions([{"name": "list_materials", "args": {}}])
    assert "选用这种板材生成报价" in actions


# ---------------------------------------------------------------------------
# Provider routing: `_build_llm()`
# ---------------------------------------------------------------------------


def test_build_llm_deepseek_uses_openai_client(monkeypatch) -> None:
    """DeepSeek must use `ChatOpenAI` with the configured base_url + key."""
    from langchain_openai import ChatOpenAI

    from dazuoagent.agent import agent as agent_module
    from dazuoagent.core.config import settings

    # Force-cleaned cache so the test sees fresh routing decisions.
    agent_module._build_llm.cache_clear()

    captured: dict = {}
    real_init = ChatOpenAI.__init__

    def spy_init(self, **kwargs):
        captured.update(kwargs)

        # Don't actually build a real OpenAI client (no network in CI).
        # Bypass pydantic validation by direct-init on the BaseModel parent.
        object.__setattr__(self, "__pydantic_fields_set__", set(kwargs))

    monkeypatch.setattr(ChatOpenAI, "__init__", spy_init)
    # Make sure the provider is deepseek regardless of the user's .env.
    monkeypatch.setattr(settings, "llm_provider", "deepseek")
    monkeypatch.setattr(settings, "deepseek_api_key", "sk-test-key")
    monkeypatch.setattr(settings, "deepseek_base_url", "https://api.deepseek.com/v1")
    monkeypatch.setattr(settings, "deepseek_model", "deepseek-v4-flash")

    try:
        agent_module._build_llm()
    finally:
        # Restore the real __init__ so the lru_cache doesn't trap us.
        monkeypatch.setattr(ChatOpenAI, "__init__", real_init)
        agent_module._build_llm.cache_clear()

    assert captured["base_url"] == "https://api.deepseek.com/v1"
    assert captured["model"] == "deepseek-v4-flash"
    # `api_key` is forwarded to the OpenAI client as a plain string;
    # LangChain's `ChatOpenAI` doesn't wrap it in pydantic.SecretStr.
    assert captured["api_key"] == "sk-test-key"
    assert captured["temperature"] == 0.4


def test_build_llm_missing_deepseek_key_raises(monkeypatch) -> None:
    """No DEEPSEEK_API_KEY + provider=deepseek → clear runtime error."""
    from dazuoagent.agent import agent as agent_module
    from dazuoagent.core.config import settings

    agent_module._build_llm.cache_clear()
    monkeypatch.setattr(settings, "llm_provider", "deepseek")
    monkeypatch.setattr(settings, "deepseek_api_key", None)

    with pytest.raises(RuntimeError, match="DEEPSEEK_API_KEY"):
        agent_module._build_llm()


def test_build_llm_unknown_provider_raises(monkeypatch) -> None:
    from dazuoagent.agent import agent as agent_module
    from dazuoagent.core.config import settings

    agent_module._build_llm.cache_clear()
    monkeypatch.setattr(settings, "llm_provider", "make-believe")

    with pytest.raises(RuntimeError, match="Unknown llm_provider"):
        agent_module._build_llm()


# ---------------------------------------------------------------------------
# Real DeepSeek — gated, skipped unless the user has a key in .env
# ---------------------------------------------------------------------------


def _has_deepseek_key() -> bool:
    from dazuoagent.core.config import settings

    return bool(settings.deepseek_api_key) and settings.llm_provider == "deepseek"


import pytest


@pytest.mark.skipif(
    not _has_deepseek_key(),
    reason="DEEPSEEK_API_KEY not set in .env (or LLM_PROVIDER != 'deepseek')",
)
def test_real_deepseek_smoke() -> None:
    """Real call to DeepSeek — one short prompt. ~1s, sub-¥0.01 per run.

    Skipped unless `LLM_PROVIDER=deepseek` and `DEEPSEEK_API_KEY` are set.
    Run manually after upgrading `deepseek-v4-flash` to verify the model
    still answers.
    """
    from dazuoagent.agent.agent import chat

    result = chat(
        history=[{"role": "user", "content": "用一句话回复: 你好?"}],
        project_id=None,
    )
    assert result["reply"]
    assert isinstance(result["reply"], str)
    assert len(result["reply"]) > 0
