"""Project (客户项目) and Room ORM models.

A `Project` represents a single customer's whole-house customization job. It
holds the customer contact info, an uploaded floor plan (file path), and a
collection of `Room`s parsed out of that plan. A `Design` is generated from
the project; `Quotation` rolls up the chosen design into a price.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dazuoagent.core.database import Base
from dazuoagent.models.base import TimestampMixin

if TYPE_CHECKING:
    from dazuoagent.models.design import Design
    from dazuoagent.models.quotation import Quotation


class Project(Base, TimestampMixin):
    """A customer whole-house-customization project."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    customer_name: Mapped[str] = mapped_column(String(128))
    customer_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    address: Mapped[str | None] = mapped_column(String(256), nullable=True)

    # Floor plan. Either a file path (image/PDF stored on disk) or, once parsed,
    # a serialized room layout JSON. Keep both for traceability.
    floor_plan_file: Mapped[str | None] = mapped_column(String(512), nullable=True)
    floor_plan_layout: Mapped[str | None] = mapped_column(String, nullable=True)  # JSON

    rooms: Mapped[list[Room]] = relationship(
        "Room", back_populates="project", cascade="all, delete-orphan",
    )
    designs: Mapped[list[Design]] = relationship(
        "Design", back_populates="project", cascade="all, delete-orphan",
    )
    quotations: Mapped[list[Quotation]] = relationship(
        "Quotation", back_populates="project", cascade="all, delete-orphan",
    )


class Room(Base):
    """A single room extracted from the floor plan.

    Rooms are children of a Project (cascade delete). Coordinates are in
    millimeters in the plan's local coordinate system — the floor-plan
    parser / canvas decide how to render them.
    """

    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))

    name: Mapped[str] = mapped_column(String(64))  # 主卧 / 客厅 / 厨房 ...
    width_mm: Mapped[float] = mapped_column(Float)
    length_mm: Mapped[float] = mapped_column(Float)
    area_sqm: Mapped[float] = mapped_column(Float)

    # Optional positions of doors/windows on the plan, JSON-encoded.
    openings: Mapped[str | None] = mapped_column(String, nullable=True)

    project: Mapped[Project] = relationship("Project", back_populates="rooms")