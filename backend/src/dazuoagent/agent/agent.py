"""Agent runtime.

`chat()` and `parse_floorplan()` are the two entry points the API calls.

The chat flow dispatches on `settings.llm_provider`:

* `"mock"` (default) — deterministic mock reply. Used when no provider key
  is configured, in CI, and in unit tests.
* `"openai"` / `"anthropic"` / `"deepseek"` — real LangChain LLM call with
  the registered tools. DeepSeek uses the OpenAI-compatible surface
  (`https://api.deepseek.com/v1`) so the same `ChatOpenAI` class drives it.

The HTTP contract from `api/v1/agents.py` does not depend on which provider
runs underneath.
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from dazuoagent.agent.prompts import FLOORPLAN_PARSER_PROMPT, SYSTEM_PROMPT
from dazuoagent.core.config import settings


def chat(*, history: list[dict], project_id: int | None = None) -> dict[str, Any]:
    """Run one agent turn. Returns a dict compatible with `ChatResponse`.

    The structure (`reply`, `tool_calls`, `suggested_actions`) is the
    stable contract; the LLM provider behind it is swappable.
    """
    if settings.llm_provider == "mock":
        return _mock_chat(history, project_id)
    return _langchain_chat(history, project_id)


def parse_floorplan(
    *,
    project_id: int,
    filename: str,
    content: bytes,
    mode: str = "agent",
) -> list[dict]:
    """Return a list of suggested rooms extracted from the upload.

    Two modes:

    * `"agent"` (default) — ask the LLM to read the image and emit JSON.
      Currently a stub that returns a single placeholder room. Replace with
      a real vision-capable model call once the agent stack lands.
    * `"ocr"` — run an OCR-only pipeline (tesseract / paddleocr). Not
      implemented yet; reserved for the deterministic fallback.
    """
    if mode == "ocr":
        return _stub_ocr_rooms()

    # Default agent mode — vision + reasoning stub.
    return [
        {"name": "客厅", "width_mm": 4200, "length_mm": 5800, "area_sqm": 24.4},
        {"name": "主卧", "width_mm": 3600, "length_mm": 4500, "area_sqm": 16.2},
    ]


# ---------------------------------------------------------------------------
# Mock implementation
# ---------------------------------------------------------------------------


def _mock_chat(history: list[dict], project_id: int | None) -> dict[str, Any]:
    """Deterministic mock — used when no API key is configured.

    Echoes a short reply and suggests the next sensible action so the
    frontend chat widget has something to render.
    """
    last_user = next((m for m in reversed(history) if m.get("role") == "user"), None)
    user_text = (last_user or {}).get("content", "").strip()

    reply = (
        f"我已收到你的需求:「{user_text[:80]}」。"
        "目前我处在 mock 模式——设置 LLM_PROVIDER=openai/anthropic/deepseek 并配置对应 API key 即可启用真实对话。"
    )
    suggested = [
        "浏览素材库",
        "上传平面图",
        "查看示例报价",
    ]
    return {
        "reply": reply,
        "tool_calls": [],
        "suggested_actions": suggested,
    }


# ---------------------------------------------------------------------------
# Real LLM (LangChain + LangGraph)
# ---------------------------------------------------------------------------


def _langchain_chat(history: list[dict], project_id: int | None) -> dict[str, Any]:
    """Drive one conversational turn through the real LLM.

    Flow:

    1. Build a LangGraph ReAct agent (`create_react_agent`) with the LLM
       from the configured provider and the registered `list_materials`
       and `get_project_rooms` tools.
    2. Translate the wire-format chat history into LangChain messages,
       prepending `SYSTEM_PROMPT`.
    3. Invoke the agent and collect tool calls from intermediate messages.
    4. Return `{reply, tool_calls, suggested_actions}` matching the API contract.
    """
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

    from dazuoagent.agent.langchain_tools import list_materials, get_project_rooms

    agent = _build_agent()

    messages: list = [SystemMessage(content=SYSTEM_PROMPT)]
    for m in history:
        role = m.get("role")
        content = m.get("content", "") or ""
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
        elif role == "system":
            messages.append(SystemMessage(content=content))
        # Unknown roles are silently dropped — keep the contract defensive.

    result = agent.invoke({"messages": messages})

    tool_calls, last_ai_content = _extract_tool_calls(result["messages"])

    return {
        "reply": last_ai_content,
        "tool_calls": tool_calls,
        "suggested_actions": _suggested_actions(tool_calls),
    }


def _build_agent():
    """Build a ReAct agent bound to the configured LLM + tools.

    Cached at import time so each chat call doesn't pay the tool-binding
    cost; the agent itself is stateless across calls.
    """
    from langgraph.prebuilt import create_react_agent

    from dazuoagent.agent.langchain_tools import (
        add_furniture_to_design,
        get_project_rooms,
        list_materials,
        list_project_designs,
    )

    llm = _build_llm()
    return create_react_agent(
        llm,
        [
            list_materials,
            get_project_rooms,
            list_project_designs,
            add_furniture_to_design,
        ],
    )


@lru_cache(maxsize=1)
def _build_llm():
    """Instantiate the LLM based on `settings.llm_provider`.

    Returns a LangChain chat model (any object exposing `.invoke(messages)`)
    so the agent-building code stays provider-agnostic.
    """
    from langchain_openai import ChatOpenAI

    provider = settings.llm_provider
    if provider == "openai":
        if not settings.openai_api_key:
            raise RuntimeError("LLM_PROVIDER=openai but OPENAI_API_KEY is not set")
        return ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.4,
        )

    if provider == "deepseek":
        if not settings.deepseek_api_key:
            raise RuntimeError("LLM_PROVIDER=deepseek but DEEPSEEK_API_KEY is not set")
        # DeepSeek exposes an OpenAI-compatible surface — same client.
        return ChatOpenAI(
            model=settings.deepseek_model,
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            temperature=0.4,
        )

    if provider == "anthropic":
        if not settings.anthropic_api_key:
            raise RuntimeError("LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY is not set")
        # Imported lazily so the SDK is only required for that provider.
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=settings.anthropic_model,
            api_key=settings.anthropic_api_key,
            temperature=0.4,
        )

    raise RuntimeError(f"Unknown llm_provider {provider!r}")


def _extract_tool_calls(messages: list) -> tuple[list[dict], str]:
    """Pull every tool invocation from a LangGraph result and the final reply.

    LangGraph returns `{messages: [...]}` whose tail is the AI's final answer;
    intermediate `AIMessage` rows carry `tool_calls` describing what was
    invoked, while `ToolMessage` rows carry the actual returned payloads.
    """
    tool_calls: list[dict] = []
    for msg in messages:
        tc = getattr(msg, "tool_calls", None) or []
        for call in tc:
            tool_calls.append(
                {
                    "name": call.get("name") if isinstance(call, dict) else getattr(call, "name", None),
                    "args": call.get("args") if isinstance(call, dict) else getattr(call, "args", None),
                },
            )

    last = messages[-1]
    last_content = getattr(last, "content", "")
    if isinstance(last_content, list):
        # Chat models can return content blocks; flatten to plain text.
        last_content = "".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in last_content
        )
    return tool_calls, str(last_content or "")


def _suggested_actions(tool_calls: list[dict]) -> list[str]:
    """Heuristic follow-up chips based on what the agent just did.

    Real product later: ask the LLM to emit a `next_actions` list as
    structured output. For now, drive it off observed tool calls.
    """
    names = {tc.get("name") for tc in tool_calls}
    suggestions: list[str] = []
    if "list_materials" in names:
        suggestions.append("选用这种板材生成报价")
    if "get_project_rooms" in names:
        suggestions.append("为每个房间推荐家具配置")
    if not suggestions:
        suggestions = ["浏览素材库", "上传平面图", "查看示例报价"]
    return suggestions


# ---------------------------------------------------------------------------
# Floor-plan helpers (still stubs)
# ---------------------------------------------------------------------------


def _stub_ocr_rooms() -> list[dict]:
    return [
        {"name": "待 OCR 解析", "width_mm": None, "length_mm": None, "area_sqm": None},
    ]


# Public so tests can build payloads programmatically.
__all__ = ["chat", "parse_floorplan", "SYSTEM_PROMPT", "FLOORPLAN_PARSER_PROMPT", "json"]


# ruff: noqa: RUF001, RUF002, RUF003  # The "×" glyph that appears in
# product line-item descriptions also shows up in mock-chat punctuation.
