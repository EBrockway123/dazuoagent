"""Rate-limit smoke test for `/api/v1/agents/chat`.

The chat endpoint is the only LLM-touching route and the most expensive
one to call. slowapi caps it to 10/minute per IP — verify by spamming
the endpoint 12 times and asserting the last call returns 429.

The agent call is monkeypatched to a no-op so this test never reaches
the LLM (cheap, deterministic).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from dazuoagent.api.v1 import agents as agents_module
from dazuoagent.main import create_app


@pytest.fixture
def mock_chat_agent(monkeypatch):
    """Bypass the real agent — return a fixed reply regardless of history."""
    monkeypatch.setattr(
        agents_module,
        "agent_chat",
        lambda *, history, project_id: {
            "reply": "mocked",
            "tool_calls": [],
            "suggested_actions": [],
        },
    )


def test_chat_endpoint_rate_limited_after_ten_calls(mock_chat_agent) -> None:
    """Hit /agents/chat 12 times in a row; the first 10 should succeed,
    the rest should be 429'd by slowapi."""
    client = TestClient(create_app())
    payload = {
        "project_id": None,
        "messages": [{"role": "user", "content": "hi"}],
    }

    statuses: list[int] = []
    for _ in range(12):
        r = client.post("/api/v1/agents/chat", json=payload)
        statuses.append(r.status_code)

    # First 10 succeed, the rest are throttled.
    assert statuses[:10] == [200] * 10
    assert all(s == 429 for s in statuses[10:]), f"expected remaining to be 429, got {statuses[10:]}"


def test_rate_limited_response_uses_friendly_chinese(mock_chat_agent) -> None:
    """The 429 body must be our localized shape so the frontend can
    render uniformly with other errors."""
    client = TestClient(create_app())
    payload = {
        "project_id": None,
        "messages": [{"role": "user", "content": "hi"}],
    }

    last = None
    for _ in range(12):
        last = client.post("/api/v1/agents/chat", json=payload)
    assert last.status_code == 429
    assert last.json() == {"detail": "请求过于频繁,请稍后再试"}
    assert "Retry-After" in last.headers
    # X-Request-ID must round-trip so users can quote it when reporting.
    assert "X-Request-ID" in last.headers


def test_request_id_round_trips_on_normal_requests() -> None:
    """Inbound X-Request-ID echoes back; absent one gets a fresh UUID."""
    client = TestClient(create_app())

    inbound = "test-rid-12345"
    r1 = client.get("/health", headers={"X-Request-ID": inbound})
    assert r1.headers["X-Request-ID"] == inbound

    r2 = client.get("/health")
    assert r2.headers["X-Request-ID"]
    assert r2.headers["X-Request-ID"] != inbound
    # UUID4 hex = 32 lowercase hex chars.
    assert len(r2.headers["X-Request-ID"]) == 32