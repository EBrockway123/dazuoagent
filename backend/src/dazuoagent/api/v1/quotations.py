"""Quotation (报价单) endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from dazuoagent.api.deps import get_db
from dazuoagent.schemas.quotation import QuotationCreate, QuotationRead
from dazuoagent.services import quotation_service

router = APIRouter()


@router.post(
    "",
    response_model=QuotationRead,
    status_code=status.HTTP_201_CREATED,
    summary="新建报价单",
    description=(
        "创建一个空报价单,行项由后续调用 `generate-from-design` 接口根据设计方案自动计算并填入。"
        " 也可以手工传 `line_items` 直接给(例如客户选定某些促销套餐)。"
    ),
)
def create_quotation(
    payload: QuotationCreate,
    db: Annotated[Session, Depends(get_db)],
) -> QuotationRead:
    """服务端会在保存时根据 row 重新汇总一次小计,防止前端篡改单价。"""
    quotation = quotation_service.create_quotation(db, payload)
    return QuotationRead.model_validate(quotation)


@router.get(
    "/{quotation_id}",
    response_model=QuotationRead,
    summary="查报价单",
    description="按 id 拉一条报价单,含所有行项明细和小计 / 人工 / 合计。",
)
def get_quotation(
    quotation_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> QuotationRead:
    """未找到时返回 404 + `{"detail": "找不到该报价单"}`。"""
    quotation = quotation_service.get_quotation(db, quotation_id)
    if quotation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="找不到该报价单")
    return QuotationRead.model_validate(quotation)


@router.post(
    "/{quotation_id}/generate-from-design/{design_id}",
    response_model=QuotationRead,
    summary="基于设计算价",
    description=(
        "调用报价引擎(`quotation_service.recompute_from_design`),"
        "根据 `design_id` 中的家具清单自动拆板 → 算每件行项明细 → 重算小计 / 人工 / 合计。"
        " 会清空既有行项重新生成。"
    ),
)
def generate_from_design(
    quotation_id: int,
    design_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> QuotationRead:
    """如果报价单或设计方案不存在,返回 404。"""
    quotation = quotation_service.recompute_from_design(db, quotation_id, design_id)
    if quotation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="找不到该报价单或设计方案")
    return QuotationRead.model_validate(quotation)
