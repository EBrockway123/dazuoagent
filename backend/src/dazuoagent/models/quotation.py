"""Quotation (报价单) ORM models.

A `Quotation` is generated from a finalised `Design`. It snapshots every line
item (板材、五金、人工…) at the time of issue so later material price changes
don't mutate historical quotes.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dazuoagent.core.database import Base
from dazuoagent.models.base import TimestampMixin

if TYPE_CHECKING:
    from dazuoagent.models.design import Design
    from dazuoagent.models.project import Project


class QuotationStatus(str, Enum):
    """Lifecycle of a quotation."""

    DRAFT = "draft"
    ISSUED = "issued"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class Quotation(Base, TimestampMixin):
    """Header row for a quotation. Line items live in `QuotationLineItem`."""

    __tablename__ = "quotations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    design_id: Mapped[int | None] = mapped_column(
        ForeignKey("designs.id", ondelete="SET NULL"), nullable=True,
    )
    status: Mapped[QuotationStatus] = mapped_column(
        SAEnum(QuotationStatus), default=QuotationStatus.DRAFT, server_default="draft",
    )

    subtotal: Mapped[float] = mapped_column(Float, default=0.0)
    labor_cost: Mapped[float] = mapped_column(Float, default=0.0)
    tax: Mapped[float] = mapped_column(Float, default=0.0)
    total: Mapped[float] = mapped_column(Float, default=0.0)

    notes: Mapped[str | None] = mapped_column(String, nullable=True)

    project: Mapped[Project] = relationship("Project", back_populates="quotations")
    design: Mapped[Design | None] = relationship("Design")
    line_items: Mapped[list[QuotationLineItem]] = relationship(
        "QuotationLineItem", back_populates="quotation", cascade="all, delete-orphan",
    )


class QuotationLineItem(Base):
    """One priced line on a quotation (e.g. "颗粒板 18mm × 12.5㎡ × ¥120/㎡")."""

    __tablename__ = "quotation_line_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quotation_id: Mapped[int] = mapped_column(
        ForeignKey("quotations.id", ondelete="CASCADE"),
    )

    description: Mapped[str] = mapped_column(String(256))
    quantity: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(16))  # sqm / piece / meter / lot
    unit_price: Mapped[float] = mapped_column(Float)
    amount: Mapped[float] = mapped_column(Float)  # = quantity * unit_price, cached

    quotation: Mapped[Quotation] = relationship("Quotation", back_populates="line_items")