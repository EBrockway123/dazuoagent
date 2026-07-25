"""Project service — CRUD over customer projects."""

from __future__ import annotations

import json
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from dazuoagent.models.project import Project, Room
from dazuoagent.schemas.project import (
    ProjectCreate,
    ProjectLayoutUpdate,
    ProjectRoomsReplace,
    RoomLayoutItem,
)

logger = logging.getLogger(__name__)


def list_projects(db: Session, *, skip: int = 0, limit: int = 50) -> tuple[list[Project], int]:
    stmt = select(Project)
    total = len(db.execute(stmt).scalars().all())
    rows = db.execute(stmt.offset(skip).limit(limit)).scalars().unique().all()
    return list(rows), total


def get_project(db: Session, project_id: int) -> Project | None:
    """Fetch a project with `rooms` and `designs` eagerly loaded.

    The 2D canvas (FloorPlanCanvas) and the 3D viewer (Design3DViewer) both
    need these relationships populated in a single round-trip; `selectinload`
    does that with two IN-queries instead of N+1.
    """
    stmt = (
        select(Project)
        .where(Project.id == project_id)
        .options(selectinload(Project.rooms), selectinload(Project.designs))
    )
    return db.execute(stmt).scalar_one_or_none()


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


def replace_rooms(db: Session, project_id: int, payload: ProjectRoomsReplace) -> Project | None:
    """Wholesale replace the project's room list.

    Used after the agent suggests rooms and the customer confirms — saves
    a round of per-room create/update/delete calls. Cascades through the
    Project → rooms relationship, so any old Room rows are dropped.
    """
    project = db.get(Project, project_id)
    if project is None:
        return None

    project.rooms.clear()
    db.flush()
    project.rooms = [Room(**room.model_dump()) for room in payload.rooms]
    db.commit()
    db.refresh(project)
    return project


def update_layout(
    db: Session, project_id: int, payload: ProjectLayoutUpdate,
) -> tuple[Project | None, list[RoomLayoutItem]]:
    """Persist room positions to `Project.floor_plan_layout` as JSON.

    Returns the saved layout items so the client can reflect any server-side
    normalisation. Returns `(None, [])` if the project doesn't exist.
    """
    project = db.get(Project, project_id)
    if project is None:
        return None, []

    # Drop layout entries whose room_id is no longer present in the project.
    valid_room_ids = {r.id for r in project.rooms}
    kept = [item for item in payload.rooms if item.room_id in valid_room_ids]
    dropped = len(payload.rooms) - len(kept)
    if dropped:
        logger.info(
            "update_layout: project=%d dropped %d stale room_id(s)",
            project_id, dropped,
        )

    project.floor_plan_layout = json.dumps(
        {"rooms": [item.model_dump() for item in kept]}, ensure_ascii=False,
    )
    db.commit()
    db.refresh(project)
    return project, kept


def parse_layout(project: Project) -> list[RoomLayoutItem]:
    """Read `floor_plan_layout` JSON back as typed items. Defensive against
    malformed/legacy payloads — returns `[]` rather than crashing."""
    if not project.floor_plan_layout:
        return []
    try:
        data = json.loads(project.floor_plan_layout)
    except (json.JSONDecodeError, TypeError):
        return []
    items = data.get("rooms", []) if isinstance(data, dict) else []
    try:
        return [RoomLayoutItem(**item) for item in items]
    except Exception:  # noqa: BLE001 — invalid shape is a soft failure
        return []