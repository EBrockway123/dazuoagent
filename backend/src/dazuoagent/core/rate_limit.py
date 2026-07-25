"""Rate limiter shared across the FastAPI app.

`slowapi` requires both the `Limiter` object (which carries the
storage backend + key function) and an exception handler attached to
the FastAPI app. Centralising both here keeps the wiring in one place
so any router can just `@limiter.limit("...")` its endpoints.

The default key is the client IP — fine for now; swap to a user-id
key when auth lands.
"""

from __future__ import annotations

from slowapi import Limiter
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