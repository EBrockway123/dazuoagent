"""FastAPI application entry point.

Run locally:

    uvicorn dazuoagent.main:app --reload --port 8000

Or via the installed console script:

    dazuoagent-api
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from dazuoagent.api.v1.router import api_router
from dazuoagent.core.config import settings
from dazuoagent.core.rate_limit import limiter


def create_app() -> FastAPI:
    """Application factory.

    A factory keeps global state out of module imports — easier to test, and lets
    Alembic / scripts import submodules without side-effects.
    """
    app = FastAPI(
        title="大作家 全屋定制 Agent API",
        version="0.1.0",
        summary="客户项目 · 设计方案 · 素材库 · 报价单 · 设计助理",
        description=(
            "全屋定制家具(全屋定制)平台的后端 API。\n\n"
            "## 模块概览\n\n"
            "* **meta** — 服务元数据(健康检查)\n"
            "* **materials** — 素材库(板材 / 五金)管理\n"
            "* **projects** — 客户项目及其平面图房间清单\n"
            "* **designs** — 设计方案(含家具摆放、尺寸、材质)\n"
            "* **quotations** — 报价单(基于设计方案的快照式行项明细)\n"
            "* **agents** — AI 设计助理对话 + 平面图解析\n\n"
            "## 工作流\n\n"
            "1. 上传平面图 → `POST /agents/projects/{id}/parse-floorplan`\n"
            "2. 创建设计方案,加入家具 → `POST /designs`\n"
            "3. 让 LLM 助手对话推荐 → `POST /agents/chat`\n"
            "4. 创建报价单 → `POST /quotations`\n"
            "5. 基于设计自动算价 → `POST /quotations/{id}/generate-from-design/{design_id}`\n"
        ),
        openapi_tags=[
            {
                "name": "meta",
                "description": "服务元数据 — 健康检查、版本号等。",
            },
            {
                "name": "materials",
                "description": "素材库 — 板材、贴皮、五金的增删改查。",
            },
            {
                "name": "projects",
                "description": "客户项目 — 包含房间清单和平面图元数据。",
            },
            {
                "name": "designs",
                "description": "设计方案 — 属于某个项目的家具摆放方案。",
            },
            {
                "name": "quotations",
                "description": "报价单 — 关联设计方案,基于面板/五金自动算价。",
            },
            {
                "name": "agents",
                "description": "AI 设计助理 — 自然语言对话 + 平面图识别。",
            },
        ],
    )

    # --- Rate limiting (slowapi) ---
    # Per-IP default of 60/minute (set in `core.rate_limit`). Tighter
    # limits can be applied per-route via `@limiter.limit("10/minute")`.
    # The middleware does the actual enforcement on every request;
    # `app.state.limiter = limiter` is the lookup hook the `@limiter.limit`
    # decorator uses at request time.
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # CORS — allow the Vite dev server during development. Tighten
    # `allow_origins` and `allow_methods` for production; the wildcard
    # headers are fine while everything runs on localhost.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
    )

    app.include_router(api_router, prefix="/api/v1")

    @app.get("/health", tags=["meta"], summary="健康检查", description="活跃探针,不读数据库。")
    def health() -> dict[str, str]:
        """用于容器编排(liveness probe)和本机 curl 检查。"""
        return {"status": "ok"}

    return app


app = create_app()


def run() -> None:  # pragma: no cover - convenience entry point
    """Console-script entry point (`dazuoagent-api`)."""
    import uvicorn

    uvicorn.run(
        "dazuoagent.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
    )


if __name__ == "__main__":  # pragma: no cover
    run()
