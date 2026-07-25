"""Design service tests — covers `get_or_create_active_design` and
`add_furniture` which back the agent's `add_furniture_to_design` tool."""

from __future__ import annotations

from collections.abc import Callable

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from dazuoagent.core.database import Base
from dazuoagent.models.design import FurnitureType
from dazuoagent.models.project import Project, Room
from dazuoagent.schemas.design import DesignCreate
from dazuoagent.services import design_service


# ---------------------------------------------------------------------------
# Fixtures: in-memory SQLite with StaticPool so a tool-wrapper-created
# Session can see rows seeded by the test session (they share one
# connection).
# ---------------------------------------------------------------------------


@pytest.fixture
def db_pair():
    """Yields `(session, session_factory)` backed by a shared
    in-memory SQLite. Tests that exercise the LangChain tool wrapper
    need the factory so the tool's SessionLocal() call sees the same
    engine as the test session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    import dazuoagent.models  # noqa: F401  -- registers all mappers

    Base.metadata.create_all(engine)
    TestSession = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    s: Session = TestSession()

    def factory() -> Session:
        return TestSession()

    try:
        yield s, factory
    finally:
        s.close()


@pytest.fixture
def session(db_pair):
    """Convenience: just the session."""
    s, _ = db_pair
    return s


def _seed_project(session, *, rooms: list[tuple[str, int, int]] | None = None) -> Project:
    proj = Project(name="测试项目", customer_name="客户甲")
    session.add(proj)
    session.flush()
    for name, w, l in rooms or []:
        session.add(
            Room(
                project_id=proj.id,
                name=name,
                width_mm=w,
                length_mm=l,
                area_sqm=(w * l) / 1_000_000,
            ),
        )
    session.flush()
    return proj


# ---------------------------------------------------------------------------
# get_or_create_active_design
# ---------------------------------------------------------------------------


def test_active_design_creates_when_none_exists(session) -> None:
    proj = _seed_project(session)

    design = design_service.get_or_create_active_design(session, proj.id)

    assert design is not None
    assert design.project_id == proj.id
    assert design.name == "Agent 主方案"
    assert design.is_final is False
    assert design.furniture == []


def test_active_design_prefers_draft_over_final(session) -> None:
    """When both a draft and a final design exist, the active one is the draft."""
    proj = _seed_project(session)

    design_service.create_design(
        session,
        DesignCreate(project_id=proj.id, name="final方案", is_final=True),
    )
    draft = design_service.create_design(
        session,
        DesignCreate(project_id=proj.id, name="draft方案", is_final=False),
    )
    draft_id = draft.id  # capture before subsequent session ops might evict it

    active = design_service.get_or_create_active_design(session, proj.id)
    assert active is not None
    assert active.id == draft_id
    assert active.is_final is False
    assert active.name == "draft方案"


def test_active_design_returns_none_for_missing_project(session) -> None:
    assert design_service.get_or_create_active_design(session, 9999) is None


# ---------------------------------------------------------------------------
# add_furniture
# ---------------------------------------------------------------------------


def test_add_furniture_appends_row(session) -> None:
    proj = _seed_project(session, rooms=[("主卧", 3600, 4500)])
    design = design_service.get_or_create_active_design(session, proj.id)

    piece = design_service.add_furniture(
        session,
        design.id,
        type="wardrobe",
        label="主卧大衣柜",
        width_mm=2400,
        height_mm=2400,
        depth_mm=600,
        room_id=proj.rooms[0].id,
    )

    assert piece.id is not None
    assert piece.type == FurnitureType.WARDROBE
    assert piece.label == "主卧大衣柜"
    assert piece.room_id == proj.rooms[0].id

    session.refresh(design)
    assert len(design.furniture) == 1
    assert design.furniture[0].id == piece.id


def test_add_furniture_rejects_unknown_type(session) -> None:
    proj = _seed_project(session)
    design = design_service.get_or_create_active_design(session, proj.id)

    with pytest.raises(ValueError):
        design_service.add_furniture(
            session,
            design.id,
            type="made-up-type",
            label="x",
            width_mm=1,
            height_mm=1,
            depth_mm=1,
        )


# ---------------------------------------------------------------------------
# add_furniture_to_design tool wrapper — JSON contract
# ---------------------------------------------------------------------------


def test_tool_wrapper_returns_json_with_piece_id(
    db_pair, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The LangChain @tool wrapper round-trips design_service, returning
    JSON that the LLM can read. We swap SessionLocal to a factory bound
    to the same in-memory engine the test seeds, so seeded rows are
    visible to the tool's session."""
    session, factory = db_pair
    proj = _seed_project(session, rooms=[("主卧", 3600, 4500)])
    session.commit()  # flush + commit so factory-opened sessions see the rows

    from dazuoagent.agent import langchain_tools

    monkeypatch.setattr(langchain_tools, "SessionLocal", factory)

    raw = langchain_tools.add_furniture_to_design.func  # type: ignore[attr-defined]
    import json as _json

    result_raw = raw(
        project_id=proj.id,
        type="wardrobe",
        label="主卧大衣柜",
        width_mm=2400,
        height_mm=2400,
        depth_mm=600,
        room_name="主卧",
    )
    payload = _json.loads(result_raw)

    assert payload["ok"] is True
    assert payload["room_name"] == "主卧"
    assert payload["size_mm"]["width"] == 2400
    assert payload["piece_id"] is not None
    assert payload["design_id"] is not None


def test_tool_wrapper_unknown_type_returns_error_json() -> None:
    from dazuoagent.agent import langchain_tools
    import json as _json

    result_raw = langchain_tools.add_furniture_to_design.func(  # type: ignore[attr-defined]
        project_id=1,
        type="not-a-real-type",
        label="x",
        width_mm=1,
        height_mm=1,
        depth_mm=1,
    )
    payload = _json.loads(result_raw)
    assert payload["ok"] is False
    assert "unknown furniture type" in payload["error"]


def test_tool_wrapper_missing_project_returns_error_json() -> None:
    """If `project_id` doesn't exist, the tool responds cleanly without
    raising — so the LLM can recover."""
    from dazuoagent.agent import langchain_tools
    import json as _json

    result_raw = langchain_tools.add_furniture_to_design.func(  # type: ignore[attr-defined]
        project_id=999_999,
        type="wardrobe",
        label="x",
        width_mm=1,
        height_mm=1,
        depth_mm=1,
    )
    payload = _json.loads(result_raw)
    assert payload["ok"] is False
    assert "not found" in payload["error"]