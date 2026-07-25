"""Design service."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from dazuoagent.models.design import Design, Furniture, FurnitureType
from dazuoagent.models.project import Project
from dazuoagent.schemas.design import DesignCreate


def get_design(db: Session, design_id: int) -> Design | None:
    return db.get(Design, design_id)


def create_design(db: Session, payload: DesignCreate) -> Design:
    if db.get(Project, payload.project_id) is None:
        raise ValueError(f"project {payload.project_id} does not exist")

    design = Design(
        project_id=payload.project_id,
        name=payload.name,
        summary=payload.summary,
        is_final=payload.is_final,
        furniture=[
            Furniture(**furniture.model_dump(exclude_none=True))
            for furniture in payload.furniture
        ],
    )
    db.add(design)
    db.commit()
    db.refresh(design)
    return design


def list_project_designs(db: Session, project_id: int) -> list[Design]:
    stmt = (
        select(Design)
        .where(Design.project_id == project_id)
        .order_by(Design.created_at.desc())
    )
    return list(db.execute(stmt).scalars().unique().all())


def get_or_create_active_design(
    db: Session, project_id: int, *, default_name: str = "Agent 主方案",
) -> Design | None:
    """Return the design the agent should be appending to.

    Pick the most recent non-final design if any exist; otherwise fall
    back to the most recent of any kind. If the project has no designs
    yet, create one named `default_name`. Returns None if the project
    itself doesn't exist.
    """
    if db.get(Project, project_id) is None:
        return None

    designs = list_project_designs(db, project_id)
    drafts = [d for d in designs if not d.is_final]
    if drafts:
        return drafts[0]
    if designs:
        return designs[0]

    design = Design(
        project_id=project_id,
        name=default_name,
        summary="由 Agent 自动创建的方案,可继续编辑。",
        is_final=False,
    )
    db.add(design)
    db.commit()
    db.refresh(design)
    return design


def add_furniture(
    db: Session,
    design_id: int,
    *,
    type: str,
    label: str,
    width_mm: float,
    height_mm: float,
    depth_mm: float,
    room_id: int | None = None,
    material_id: int | None = None,
) -> Furniture:
    """Append a Furniture row to an existing design.

    Used by the LangChain tool after the agent decides what to add.
    Validates the enum against `FurnitureType` so a bad string from
    the LLM doesn't corrupt the row.
    """
    furniture = Furniture(
        design_id=design_id,
        type=FurnitureType(type),
        label=label,
        width_mm=width_mm,
        height_mm=height_mm,
        depth_mm=depth_mm,
        room_id=room_id,
        material_id=material_id,
    )
    db.add(furniture)
    db.commit()
    db.refresh(furniture)
    return furniture