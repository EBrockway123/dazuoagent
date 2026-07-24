"""Tools the agent can call.

Each tool is a plain Python function decorated for LangChain. They take a
`Session` indirectly — passed through the closure in `agent.build_agent()`
once we wire a real agent. For now they're documented signatures.
"""

from __future__ import annotations

from dazuoagent.core.database import SessionLocal
from dazuoagent.services import material_service, project_service


def list_materials(keyword: str | None = None, board_type: str | None = None) -> list[dict]:
    """Search the material library.

    The agent calls this when the customer asks "你们有什么样的板材?" or
    "有白色的烤漆门板吗?". Results are returned as plain dicts so they
    serialise cleanly into the prompt context.
    """
    from dazuoagent.models.material import BoardType  # local import avoids cycles

    with SessionLocal() as db:
        bt = BoardType(board_type) if board_type else None
        rows, _ = material_service.list_materials(db, board_type=bt, keyword=keyword, limit=20)
    return [
        {
            "sku": m.sku,
            "name": m.name,
            "board_type": m.board_type.value if m.board_type else None,
            "veneer": m.veneer.value if m.veneer else None,
            "thickness_mm": m.thickness_mm,
            "price": m.price,
            "unit": m.unit,
        }
        for m in rows
    ]


def get_project_rooms(project_id: int) -> list[dict]:
    """Fetch the parsed rooms for a project (used after floor-plan upload)."""
    with SessionLocal() as db:
        project = project_service.get_project(db, project_id)
        if project is None:
            return []
        return [
            {"name": r.name, "width_mm": r.width_mm, "length_mm": r.length_mm, "area_sqm": r.area_sqm}
            for r in project.rooms
        ]


# The LangChain `Tool` wrapper is added in `agent.build_agent()`. Keeping the
# raw functions here lets them be unit-tested in isolation.
TOOL_REGISTRY: dict[str, callable] = {
    "list_materials": list_materials,
    "get_project_rooms": get_project_rooms,
}