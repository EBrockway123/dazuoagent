"""LangChain `@tool` wrappers for the agent.

These wrap the raw service functions in `agent/tools.py` (read-only) and
`services/design_service.py` (write) with the LangChain `@tool` decorator
so they show up in the agent's tool picker. Wrappers return JSON text
(not Python objects) because that's what fits into the LLM context window
cleanly.

Keeping the wrappers in a separate module avoids importing LangChain
from `tools.py` (which the agent and CLI paths both reach into without
needing the LLM stack loaded).
"""

from __future__ import annotations

import json

from langchain_core.tools import tool

from dazuoagent.agent.tools import get_project_rooms as _get_project_rooms
from dazuoagent.agent.tools import list_materials as _list_materials
from dazuoagent.core.database import SessionLocal
from dazuoagent.services import design_service


@tool
def list_materials(
    keyword: str | None = None,
    board_type: str | None = None,
) -> str:
    """Search the material library (boards and 五金).

    Use this when the customer asks about available board finishes,
    specific colors, or material prices. `keyword` is fuzzy-matched
    against the SKU name (e.g. "白色", "橡木", "拉手"). `board_type`
    filters by substrate: "particleboard" / "multilayer" / "mdf" /
    "solid_wood".

    Returns a JSON array of matching material SKUs.
    """
    rows = _list_materials(keyword=keyword, board_type=board_type)
    return json.dumps(rows, ensure_ascii=False, indent=2)


@tool
def get_project_rooms(project_id: int) -> str:
    """Fetch the parsed room list for a project (used after the customer
    uploads a floor plan). Returns a JSON array of `{name, width_mm,
    length_mm, area_sqm}` dicts. Empty array if the project has no rooms
    yet or doesn't exist.
    """
    rooms = _get_project_rooms(project_id)
    return json.dumps(rooms, ensure_ascii=False, indent=2)


@tool
def list_project_designs(project_id: int) -> str:
    """List all designs (方案) belonging to a project, ordered newest first.

    Each row includes `id`, `name`, `summary`, `is_final`, and a count of
    furniture pieces. Use this to decide whether to append to an existing
    design or let the system create a fresh one.
    """
    with SessionLocal() as db:
        designs = design_service.list_project_designs(db, project_id)
        payload = [
            {
                "id": d.id,
                "name": d.name,
                "summary": d.summary,
                "is_final": d.is_final,
                "furniture_count": len(d.furniture),
            }
            for d in designs
        ]
    return json.dumps(payload, ensure_ascii=False, indent=2)


@tool
def add_furniture_to_design(
    project_id: int,
    type: str,
    label: str,
    width_mm: float,
    height_mm: float,
    depth_mm: float,
    room_name: str | None = None,
) -> str:
    """Add one piece of built-in furniture to a project's active design.

    The agent should call this whenever the customer describes a new
    piece of furniture — wardrobe / cabinet / TV stand / shoe cabinet /
    bookcase / open closet / other. Use the dimension fields in mm
    (typical wardrobe: w=2400 h=2400 d=600; typical TV stand: w=2000
    h=450 d=400). `room_name` is matched against the project's rooms
    by exact name; pass null when the customer hasn't specified a room.

    Type values:
      wardrobe / wardrobe_open / kitchen_cabinet / tv_stand /
      bookcase / shoe_cabinet / other.

    The system picks the project's most recent non-final design (auto-
    creates one named "Agent 主方案" if none exist), then appends the
    piece. Returns JSON with the new piece's id and a one-line summary.
    """
    valid_types = {
        "wardrobe", "wardrobe_open", "kitchen_cabinet",
        "tv_stand", "bookcase", "shoe_cabinet", "other",
    }
    if type not in valid_types:
        return json.dumps(
            {"ok": False, "error": f"unknown furniture type: {type!r}; valid: {sorted(valid_types)}"},
            ensure_ascii=False,
        )

    with SessionLocal() as db:
        design = design_service.get_or_create_active_design(db, project_id)
        if design is None:
            return json.dumps(
                {"ok": False, "error": f"project {project_id} not found"},
                ensure_ascii=False,
            )

        room_id = None
        if room_name:
            for r in design.project.rooms:
                if r.name == room_name:
                    room_id = r.id
                    break

        piece = design_service.add_furniture(
            db,
            design.id,
            type=type,
            label=label,
            width_mm=width_mm,
            height_mm=height_mm,
            depth_mm=depth_mm,
            room_id=room_id,
        )

    return json.dumps(
        {
            "ok": True,
            "design_id": design.id,
            "design_name": design.name,
            "piece_id": piece.id,
            "label": piece.label,
            "type": piece.type.value,
            "size_mm": {
                "width": piece.width_mm,
                "height": piece.height_mm,
                "depth": piece.depth_mm,
            },
            "room_id": room_id,
            "room_name": room_name,
        },
        ensure_ascii=False,
        indent=2,
    )