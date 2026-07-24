"""Design service."""

from __future__ import annotations

from sqlalchemy.orm import Session

from dazuoagent.models.design import Design, Furniture
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