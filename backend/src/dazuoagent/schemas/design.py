"""Pydantic schemas for `Design` and `Furniture`."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from dazuoagent.models.design import FurnitureType


class FurnitureBase(BaseModel):
    type: FurnitureType
    label: str
    width_mm: float = Field(..., ge=0)
    height_mm: float = Field(..., ge=0)
    depth_mm: float = Field(..., ge=0)
    material_id: int | None = None
    room_id: int | None = None


class FurnitureCreate(FurnitureBase):
    pass


class FurnitureRead(FurnitureBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    design_id: int


class DesignBase(BaseModel):
    name: str
    summary: str | None = None
    is_final: bool = False


class DesignCreate(DesignBase):
    project_id: int
    furniture: list[FurnitureCreate] = Field(default_factory=list)


class DesignRead(DesignBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    furniture: list[FurnitureRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def _serialize_dt(self, value: datetime) -> str:
        """Emit ISO 8601 strings — matches the wire contract callers expect."""
        return value.isoformat()
