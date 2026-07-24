"""Material library endpoints (素材库).

Read-heavy: list with filters, get by id. Writes (create) live here too but
should be admin-only in production — wrap with auth deps when that lands.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from dazuoagent.api.deps import get_db
from dazuoagent.models.material import BoardType, HardwareCategory, Veneer
from dazuoagent.schemas.material import (
    MaterialCreate,
    MaterialListResponse,
    MaterialRead,
)
from dazuoagent.services import material_service

router = APIRouter()


@router.get(
    "",
    response_model=MaterialListResponse,
    summary="列出素材(可筛选)",
    description="按板材类型 / 贴皮 / 五金类型 / 关键词筛选素材库。",
)
def list_materials(
    db: Annotated[Session, Depends(get_db)],
    board_type: Annotated[
        BoardType | None,
        Query(description="按板材基材筛选:颗粒板 / 多层板 / 密度板 / 实木"),
    ] = None,
    veneer: Annotated[
        Veneer | None,
        Query(description="按表面工艺筛选:三聚氰胺 / 烤漆 / PVC 贴膜 / 实木贴皮 / 包覆"),
    ] = None,
    hardware_category: Annotated[
        HardwareCategory | None,
        Query(description="按五金类型筛选:铰链 / 滑轨 / 拉手 / 气撑 / 挂衣杆"),
    ] = None,
    keyword: Annotated[
        str | None,
        Query(description="对 SKU / 名称做模糊匹配,例如输入 '白色' 或 '橡木'。"),
    ] = None,
    skip: Annotated[int, Query(ge=0, description="分页起始位置")] = 0,
    limit: Annotated[int, Query(ge=1, le=200, description="每页最大条数,默认 50,最大 200")] = 50,
) -> MaterialListResponse:
    """返回素材列表 + 命中总数。空结果时 `items=[]` 不报错。"""
    items, total = material_service.list_materials(
        db,
        board_type=board_type,
        veneer=veneer,
        hardware_category=hardware_category,
        keyword=keyword,
        skip=skip,
        limit=limit,
    )
    return MaterialListResponse(items=[MaterialRead.model_validate(i) for i in items], total=total)


@router.get(
    "/{material_id}",
    response_model=MaterialRead,
    summary="查单个素材",
    description="按 id 查一条素材的完整记录。",
)
def get_material(
    material_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> MaterialRead:
    """找不到时返回 404 + `{"detail": "找不到该素材"}`。"""
    material = material_service.get_material(db, material_id)
    if material is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="找不到该素材")
    return MaterialRead.model_validate(material)


@router.post(
    "",
    response_model=MaterialRead,
    status_code=status.HTTP_201_CREATED,
    summary="新建素材",
    description="手动录入新素材。生产环境应限制为管理员调用(后续接权限层)。",
)
def create_material(
    payload: MaterialCreate,
    db: Annotated[Session, Depends(get_db)],
) -> MaterialRead:
    """板材 / 五金共用同一张表 — `board_type` 留空表示这是五金。"""
    material = material_service.create_material(db, payload)
    return MaterialRead.model_validate(material)
