"""Project (客户项目) endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from dazuoagent.api.deps import get_db
from dazuoagent.schemas.project import (
    ProjectCreate,
    ProjectListResponse,
    ProjectRead,
)
from dazuoagent.services import project_service

router = APIRouter()


@router.get(
    "",
    response_model=ProjectListResponse,
    summary="列出客户项目",
    description="按时间倒序返回客户项目列表(含房间清单)。",
)
def list_projects(
    db: Annotated[Session, Depends(get_db)],
    skip: Annotated[int, Query(ge=0, description="分页起始位置")] = 0,
    limit: Annotated[int, Query(ge=1, le=200, description="每页最大条数")] = 50,
) -> ProjectListResponse:
    """空列表表示还没有任何项目,前端据此显示空状态。"""
    items, total = project_service.list_projects(db, skip=skip, limit=limit)
    return ProjectListResponse(items=[ProjectRead.model_validate(i) for i in items], total=total)


@router.post(
    "",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="新建客户项目",
    description="创建一个新项目。平面图文件本身通过 `/agents` 上传与解析。",
)
def create_project(
    payload: ProjectCreate,
    db: Annotated[Session, Depends(get_db)],
) -> ProjectRead:
    """`rooms` 字段可选 — 创建后还可以再上传平面图补充。"""
    project = project_service.create_project(db, payload)
    return ProjectRead.model_validate(project)


@router.get(
    "/{project_id}",
    response_model=ProjectRead,
    summary="查单个项目",
    description="按 id 查一个项目的所有房间清单、平面图元数据。",
)
def get_project(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> ProjectRead:
    """未找到时返回 404 + `{"detail": "找不到该项目"}`。"""
    project = project_service.get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="找不到该项目")
    return ProjectRead.model_validate(project)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除项目",
    description="删除项目并级联删除其房间、设计方案、报价单。",
)
def delete_project(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """未找到时返回 404。删除不可逆。"""
    if not project_service.delete_project(db, project_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="找不到该项目")
