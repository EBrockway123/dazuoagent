"""Request-scoped utilities: request_id propagation + JSON access logging.

Adds:

* **request_id** — every request gets a UUID4 `X-Request-ID` (or echoes
  the inbound header if the caller supplied one). It rides on
  `request.state.request_id` for in-process consumers and on the
  outbound response header for the client to see.
* **JSON access log** — middleware writes one structured line per
  request (method, path, status, duration_ms, client_ip,
  request_id). Routes that throw also produce a log entry before
  FastAPI's default 500 page kicks in.

Why not `structlog`? We're trying to stay lean; `logging` with a JSON
formatter covers the structured-shape need without a new dep.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from contextvars import ContextVar
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-ID"

# Per-request slot — populated by RequestContextMiddleware, read by
# `request_id_log_filter` so every log line emitted during the request
# gets the same id without threading it through every function.
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class JsonFormatter(logging.Formatter):
    """Emit log records as single-line JSON, with request_id injected
    from the contextvar when present."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        rid = request_id_var.get()
        if rid and rid != "-":
            payload["request_id"] = rid
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        # Extra fields attached via `logger.info(..., extra={...})`
        for k, v in record.__dict__.items():
            if k in {
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "asctime",
                "taskName",
            }:
                continue
            payload[k] = v
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: int = logging.INFO) -> None:
    """Idempotent: wire the access logger to stdout with the JSON formatter.

    Called from `main.create_app()` so the logger is in place by the
    time any request lands.
    """
    logger = logging.getLogger("dazuoagent.access")
    if getattr(logger, "_configured", False):
        return
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    logger._configured = True  # type: ignore[attr-defined]


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Stamp `X-Request-ID` on every request + emit a JSON access log line.

    Order matters: register BEFORE SlowAPIMiddleware so the request id
    is on `request.state` even when the rate limiter short-circuits the
    request with a 429.
    """

    async def dispatch(self, request: Request, call_next):
        inbound = request.headers.get(REQUEST_ID_HEADER, "").strip()
        rid = inbound or uuid.uuid4().hex
        request.state.request_id = rid
        token = request_id_var.set(rid)

        access = logging.getLogger("dazuoagent.access")
        started = time.perf_counter()
        status = 500
        try:
            response: Response = await call_next(request)
            status = response.status_code
            response.headers[REQUEST_ID_HEADER] = rid
            return response
        finally:
            duration_ms = round((time.perf_counter() - started) * 1000, 1)
            access.info(
                "request",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status": status,
                    "duration_ms": duration_ms,
                    "client_ip": _client_ip(request),
                },
            )
            request_id_var.reset(token)


def _client_ip(request: Request) -> str:
    """First entry in X-Forwarded-For (if behind a trusted proxy), else
    the socket peer. Empty string if neither is known."""
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",", 1)[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return ""