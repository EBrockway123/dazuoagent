"""Pydantic schemas for `Material`."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from dazuoagent.models.material import BoardType, HardwareCategory, Veneer


class MaterialBase(BaseModel):
    sku: str = Field(..., max_length=64)
    name: str = Field(..., max_length=128)
    board_type: BoardType | None = None
    thickness_mm: int | None = Field(default=None, ge=0, le=100)
    veneer: Veneer | None = None
    hardware_category: HardwareCategory | None = None
    color_code: str | None = None
    image_url: str | None = None
    supplier: str | None = None
    price: float = Field(..., ge=0)
    unit: str = Field(default="sqm", max_length=16)


class MaterialCreate(MaterialBase):
    pass


class MaterialRead(MaterialBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def _serialize_dt(self, value: datetime) -> str:
        """Emit ISO 8601 strings — matches the wire contract callers expect."""
        return value.isoformat()


class MaterialListResponse(BaseModel):
    items: list[MaterialRead]
    total: int
