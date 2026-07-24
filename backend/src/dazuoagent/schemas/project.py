"""Pydantic schemas for `Project` and `Room`."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class RoomBase(BaseModel):
    name: str = Field(..., max_length=64)
    width_mm: float = Field(..., ge=0)
    length_mm: float = Field(..., ge=0)
    area_sqm: float = Field(..., ge=0)
    openings: str | None = None


class RoomCreate(RoomBase):
    pass


class RoomRead(RoomBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int


class ProjectBase(BaseModel):
    name: str
    customer_name: str
    customer_phone: str | None = None
    address: str | None = None
    floor_plan_file: str | None = None
    floor_plan_layout: str | None = None


class ProjectCreate(ProjectBase):
    rooms: list[RoomCreate] = Field(default_factory=list)


class ProjectRead(ProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rooms: list[RoomRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def _serialize_dt(self, value: datetime) -> str:
        """Emit ISO 8601 strings — matches the wire contract callers expect."""
        return value.isoformat()


class ProjectListResponse(BaseModel):
    items: list[ProjectRead]
    total: int
