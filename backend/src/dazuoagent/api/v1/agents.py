"""Agent endpoints — chat with the LLM and trigger agent workflows.

The two top-level flows today:

* `POST /agents/chat` — a free-form chat turn. The agent may call tools (look
  up materials, read project rooms, etc.) and replies with a structured
  response the frontend can render.
* `POST /agents/projects/{id}/parse-floorplan` — upload a floor-plan image
  and have the agent (or a parser, depending on `mode`) extract rooms.

All endpoints stream or return JSON; we do NOT use SSE yet — once the agent's
typical response is large enough to justify it, switch `chat` to streaming.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from dazuoagent.agent.agent import chat as agent_chat
from dazuoagent.agent.agent import parse_floorplan as agent_parse_floorplan
from dazuoagent.api.deps import get_db
from dazuoagent.core.config import settings
from dazuoagent.core.rate_limit import limiter

router = APIRouter()


class ChatMessage(BaseModel):
    """A single message in the chat history."""

    role: str  # "user" | "assistant" | "system"
    content: str


class ChatRequest(BaseModel):
    project_id: int | None = None
    messages: list[ChatMessage]


class ChatResponse(BaseModel):
    reply: str
    tool_calls: list[dict] = []
    suggested_actions: list[str] = []


# Chat is the most expensive endpoint (real LLM call, possible tool
# execution). Cap to 10 turns/minute per IP — a real conversation rarely
# exceeds 1 call/sec, this just stops runaway loops and abuse.
#
# Decorator order matters: `@router.post` must be the OUTER one so the
# version registered with FastAPI is the slowapi-wrapped function.
# Otherwise FastAPI captures the bare function and the limit never
# fires.
@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="与设计助理对话(一轮)",
    description=(
        "无状态接口:前端保存历史,每次发完整消息列表。"
        "如带上 `project_id`,智能体可以调用项目级工具(查房间清单等)。"
    ),
)
@limiter.limit("10/minute")
def chat(
    request: Request,
    payload: ChatRequest,
    response: Response,  # FastAPI-injected; slowapi writes X-RateLimit-* onto it
) -> ChatResponse:
    """根据 `settings.llm_provider` 自动路由到真实 LLM 或 mock 实现。

    `request` 参数必须存在 — slowapi 靠它取客户端 IP 来做限流。
    `response` 是 FastAPI 自动注入的 Response 对象, slowapi 用它写
    `X-RateLimit-*` 响应头(剩余配额、命中上限时间)。
    """
    history = [m.model_dump() for m in payload.messages]
    result = agent_chat(history=history, project_id=payload.project_id)
    return ChatResponse(**result)


@router.post(
    "/projects/{project_id}/parse-floorplan",
    status_code=status.HTTP_202_ACCEPTED,
    summary="上传平面图并解析房间",
    description=(
        "上传一张 JPG/PNG/PDF 格式的房屋平面图,后台调用视觉模型或 OCR 解析。"
        " 返回建议的房间清单(主卧 / 客厅 / 厨房 …)。"
        " 客户端确认后,再通过 `POST /projects` 写入。"
    ),
)
async def parse_floorplan(
    project_id: int,
    file: Annotated[UploadFile, File(description="平面图文件(JPG / PNG / PDF)。")],
    mode: Annotated[
        str,
        Form(description="解析模式:`agent` = LLM 视觉(默认),`ocr` = OCR 走通模式。"),
    ] = "agent",
) -> dict:
    """文件超过 20 MB 时直接拒绝,不入队。"""
    contents = await file.read()
    if len(contents) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"平面图文件过大(> {settings.max_upload_bytes // 1024 // 1024} MB),请压缩后重传。",
        )

    suggested = agent_parse_floorplan(
        project_id=project_id,
        filename=file.filename or "plan",
        content=contents,
        mode=mode,
    )
    return {"status": "ok", "rooms": suggested}
