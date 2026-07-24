"""Project service — CRUD over customer projects."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from dazuoagent.models.project import Project, Room
from dazuoagent.schemas.project import ProjectCreate


def list_projects(db: Session, *, skip: int = 0, limit: int = 50) -> tuple[list[Project], int]:
    stmt = select(Project)
    total = len(db.execute(stmt).scalars().all())
    rows = db.execute(stmt.offset(skip).limit(limit)).scalars().unique().all()
    return list(rows), total


def get_project(db: Session, project_id: int) -> Project | None:
    return db.get(Project, project_id)


def create_project(db: Session, payload: ProjectCreate) -> Project:
    project = Project(
        name=payload.name,
        customer_name=payload.customer_name,
        customer_phone=payload.customer_phone,
        address=payload.address,
        floor_plan_file=payload.floor_plan_file,
        floor_plan_layout=payload.floor_plan_layout,
        rooms=[Room(**room.model_dump()) for room in payload.rooms],
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project_id: int) -> bool:
    project = db.get(Project, project_id)
    if project is None:
        return False
    db.delete(project)
    db.commit()
    return True