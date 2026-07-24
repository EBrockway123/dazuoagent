"""LangChain `@tool` wrappers for the agent.

These wrap the raw service functions in `agent/tools.py` with the
LangChain `@tool` decorator so they show up in the agent's tool picker.
The wrapper returns JSON text (not Python objects) because that's what
fits into the LLM context window cleanly.

Keeping the wrappers in a separate module avoids importing LangChain
from `tools.py` (which the agent and CLI paths both reach into without
needing the LLM stack loaded).
"""

from __future__ import annotations

import json

from langchain_core.tools import tool

from dazuoagent.agent.tools import get_project_rooms as _get_project_rooms
from dazuoagent.agent.tools import list_materials as _list_materials


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
