"""Smoke tests — verify the framework wires together.

These exercise the modules without hitting a real LLM or external services.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from dazuoagent.agent.agent import chat, parse_floorplan
from dazuoagent.main import create_app

client = TestClient(create_app())


def test_health() -> None:
    """Health endpoint works without a DB."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_agent_chat_mock() -> None:
    """Mock agent returns a non-empty reply with suggested actions."""
    result = chat(
        history=[{"role": "user", "content": "我想要简约风格,主卧一个大衣柜"}],
        project_id=None,
    )
    assert "reply" in result
    assert result["reply"]
    assert result["suggested_actions"]


def test_parse_floorplan_returns_rooms() -> None:
    """Floor-plan parser stub returns at least one room."""
    rooms = parse_floorplan(
        project_id=1, filename="plan.png", content=b"fake", mode="agent",
    )
    assert rooms
    assert {"name", "width_mm", "length_mm", "area_sqm"} <= set(rooms[0].keys())


def test_materials_endpoint_smoke() -> None:
    """GET /api/v1/materials returns a list (possibly empty before seed)."""
    response = client.get("/api/v1/materials")
    assert response.status_code == 200
    body = response.json()
    assert "items" in body and "total" in body