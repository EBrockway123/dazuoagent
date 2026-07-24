"""Design (设计方案) endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from dazuoagent.api.deps import get_db
from dazuoagent.schemas.design import DesignCreate, DesignRead
from dazuoagent.services import design_service

router = APIRouter()


@router.post(
    "",
    response_model=DesignRead,
    status_code=status.HTTP_201_CREATED,
    summary="保存设计方案草稿",
    description=(
        "为某个项目创建一个新的设计方案,内含家具清单(尺寸 / 材质 / 房间归属)。"
        " `is_final=true` 之后该方案可以用于生成报价单。"
    ),
)
def create_design(
    payload: DesignCreate,
    db: Annotated[Session, Depends(get_db)],
) -> DesignRead:
    """一个项目可有多个设计方案 — 只有 `is_final=true` 的那个会被报价。"""
    design = design_service.create_design(db, payload)
    return DesignRead.model_validate(design)


@router.get(
    "/{design_id}",
    response_model=DesignRead,
    summary="查单个设计方案",
    description="按 id 拉一个设计方案的完整内容(含家具列表)。",
)
def get_design(
    design_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> DesignRead:
    """未找到时返回 404 + `{"detail": "找不到该设计方案"}`。"""
    design = design_service.get_design(db, design_id)
    if design is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="找不到该设计方案")
    return DesignRead.model_validate(design)
