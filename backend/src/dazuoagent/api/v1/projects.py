"""Project (客户项目) endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from dazuoagent.api.deps import get_db
from dazuoagent.schemas.project import (
    ProjectCreate,
    ProjectLayoutResponse,
    ProjectLayoutUpdate,
    ProjectListResponse,
    ProjectRead,
    ProjectRoomsReplace,
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


@router.put(
    "/{project_id}/rooms",
    response_model=ProjectRead,
    summary="整组替换房间清单",
    description=(
        "接受平面图解析后给出的房间清单,或让用户批量修改后整组提交。会清空已有房间再插入新列表。"
    ),
)
def replace_rooms(
    project_id: int,
    payload: ProjectRoomsReplace,
    db: Annotated[Session, Depends(get_db)],
) -> ProjectRead:
    """项目不存在时返回 404。"""
    project = project_service.replace_rooms(db, project_id, payload)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="找不到该项目")
    return ProjectRead.model_validate(project)


@router.get(
    "/{project_id}/layout",
    response_model=ProjectLayoutResponse,
    summary="读取平面图布局",
    description="返回 `Project.floor_plan_layout` 解析后的房间坐标 + 旋转角。",
)
def get_layout(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> ProjectLayoutResponse:
    """布局字段为 NULL 或格式损坏时返回空 `rooms: []`。"""
    project = project_service.get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="找不到该项目")
    return ProjectLayoutResponse(rooms=project_service.parse_layout(project))


@router.put(
    "/{project_id}/layout",
    response_model=ProjectLayoutResponse,
    summary="保存平面图布局",
    description=(
        "把 FloorPlanCanvas 上房间的位置 + 旋转角持久化。"
        " 不在当前项目房间清单里的 `room_id` 会被静默丢弃。"
    ),
)
def put_layout(
    project_id: int,
    payload: ProjectLayoutUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> ProjectLayoutResponse:
    """项目不存在时返回 404。"""
    project, kept = project_service.update_layout(db, project_id, payload)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="找不到该项目")
    return ProjectLayoutResponse(rooms=kept)


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