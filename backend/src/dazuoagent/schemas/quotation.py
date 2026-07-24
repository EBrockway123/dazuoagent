"""Pydantic schemas for `Quotation` and `QuotationLineItem`."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from dazuoagent.models.quotation import QuotationStatus


class QuotationLineItemBase(BaseModel):
    description: str
    quantity: float = Field(..., ge=0)
    unit: str
    unit_price: float = Field(..., ge=0)
    amount: float = Field(..., ge=0)


class QuotationLineItemCreate(QuotationLineItemBase):
    pass


class QuotationLineItemRead(QuotationLineItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class QuotationBase(BaseModel):
    project_id: int
    design_id: int | None = None
    status: QuotationStatus = QuotationStatus.DRAFT
    labor_cost: float = 0.0
    tax: float = 0.0
    notes: str | None = None


class QuotationCreate(QuotationBase):
    line_items: list[QuotationLineItemCreate] = Field(default_factory=list)


class QuotationRead(QuotationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subtotal: float
    total: float
    line_items: list[QuotationLineItemRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def _serialize_dt(self, value: datetime) -> str:
        """Emit ISO 8601 strings — matches the wire contract callers expect."""
        return value.isoformat()
