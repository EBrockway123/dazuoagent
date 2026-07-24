"""Aggregator for v1 routers.

Mounted at `/api/v1` in `main.py`. To add a new endpoint, create a module
under `api/v1/` and `include_router` it here.
"""

from __future__ import annotations

from fastapi import APIRouter

from dazuoagent.api.v1 import agents, designs, materials, projects, quotations

api_router = APIRouter()
api_router.include_router(materials.router, prefix="/materials", tags=["素材库 / materials"])
api_router.include_router(projects.router, prefix="/projects", tags=["客户项目 / projects"])
api_router.include_router(designs.router, prefix="/designs", tags=["设计方案 / designs"])
api_router.include_router(quotations.router, prefix="/quotations", tags=["报价单 / quotations"])
api_router.include_router(agents.router, prefix="/agents", tags=["AI 设计助理 / agents"])
