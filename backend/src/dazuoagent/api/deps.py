"""Shared FastAPI dependencies.

Currently only `get_db` (re-exported for clarity at the call site). Add auth,
pagination, current-user, etc. here as the API grows.
"""

from dazuoagent.core.database import get_db

__all__ = ["get_db"]