"""Rate limiter shared across the FastAPI app.

`slowapi` requires both the `Limiter` object (which carries the
storage backend + key function) and an exception handler attached to
the FastAPI app. Centralising both here keeps the wiring in one place
so any router can just `@limiter.limit("...")` its endpoints.

The default key is the client IP — fine for now; swap to a user-id
key when auth lands.
"""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# 60 requests/minute per IP across the whole app; tighter per-route
# limits can be added with `@limiter.limit("10/minute")` on individual
# endpoints (see agents.py).
#
# `headers_enabled=True` makes slowapi emit `X-RateLimit-*` headers on
# every response — useful for the frontend to show "已用 5/10" hints.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["60/minute"],
    headers_enabled=True,
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Friendly Chinese 429 — replaces slowapi's default English text.

    Same response shape as our other errors (`{"detail": "..."}`) so the
    frontend can render it uniformly. We also forward the X-Request-ID
    header so a frustrated user can paste it when reporting trouble.
    `exc` is kept in the signature (slowapi passes it) even though we
    don't surface its message — a future tweak might append the rate.
    """
    _ = exc  # noqa: F841  — kept for future rate-limit metadata
    rid = getattr(request.state, "request_id", None)
    headers = {"Retry-After": "60"}
    if rid:
        headers["X-Request-ID"] = rid
    return JSONResponse(
        status_code=429,
        content={"detail": "请求过于频繁,请稍后再试"},
        headers=headers,
    )