"""Pydantic schemas — request/response shapes for the HTTP API.

Kept separate from ORM models so the wire format can evolve without touching
the database layer. Service-layer code converts ORM ↔ schemas.
"""
