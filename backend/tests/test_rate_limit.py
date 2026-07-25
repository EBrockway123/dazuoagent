"""Rate-limit smoke test for `/api/v1/agents/chat`.

The chat endpoint is the only LLM-touching route and the most expensive
one to call. slowapi caps it to 10/minute per IP — verify by spamming
the endpoint 12 times and asserting the last call returns 429.

The agent call is monkeypatched to a no-op so this test never reaches
the LLM (cheap, deterministic).
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from dazuoagent.api.v1 import agents as agents_module
from dazuoagent.main import create_app


def test_chat_endpoint_rate_limited_after_ten_calls(monkeypatch) -> None:
    """Hit /agents/chat 12 times in a row; the first 10 should succeed,
    the rest should be 429'd by slowapi."""
    # Bypass the real agent — return a fixed reply regardless of history.
    monkeypatch.setattr(
        agents_module,
        "agent_chat",
        lambda *, history, project_id: {
            "reply": "mocked",
            "tool_calls": [],
            "suggested_actions": [],
        },
    )

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