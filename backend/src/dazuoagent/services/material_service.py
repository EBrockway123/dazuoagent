"""Material service — list/filter/get/create."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from dazuoagent.models.material import BoardType, HardwareCategory, Material, Veneer
from dazuoagent.schemas.material import MaterialCreate


def list_materials(
    db: Session,
    *,
    board_type: BoardType | None = None,
    veneer: Veneer | None = None,
    hardware_category: HardwareCategory | None = None,
    keyword: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[Material], int]:
    stmt = select(Material)
    if board_type is not None:
        stmt = stmt.where(Material.board_type == board_type)
    if veneer is not None:
        stmt = stmt.where(Material.veneer == veneer)
    if hardware_category is not None:
        stmt = stmt.where(Material.hardware_category == hardware_category)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(Material.name.ilike(like) | Material.sku.ilike(like))

    total = len(db.execute(stmt).scalars().all())
    rows = db.execute(stmt.offset(skip).limit(limit)).scalars().all()
    return list(rows), total


def get_material(db: Session, material_id: int) -> Material | None:
    return db.get(Material, material_id)


def create_material(db: Session, payload: MaterialCreate) -> Material:
    material = Material(**payload.model_dump())
    db.add(material)
    db.commit()
    db.refresh(material)
    return material