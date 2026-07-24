"""Design (设计方案) and Furniture ORM models.

A `Design` is a proposed furniture layout for a project, typically produced
by the AI agent or a human designer. Each `Furniture` is an individual piece
(wardrobe, kitchen cabinet, TV stand, …) attached to a room. Pricing is
derived from `Furniture.material_id` and dimensions — the `Quotation` model
caches a snapshot of that calculation.
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
    from dazuoagent.models.material import Material
    from dazuoagent.models.project import Project, Room


class FurnitureType(str, Enum):
    """Type of built-in furniture piece."""

    WARDROBE = "wardrobe"  # 衣柜
    KITCHEN_CABINET = "kitchen_cabinet"  # 橱柜
    TV_STAND = "tv_stand"  # 电视柜
    BOOKCASE = "bookcase"  # 书柜
    SHOE_CABINET = "shoe_cabinet"  # 鞋柜
    WARDROBE_OPEN = "wardrobe_open"  # 开放式衣帽间
    OTHER = "other"


class Design(Base, TimestampMixin):
    """A proposed furniture layout for a project.

    A project may have many designs (iterations). `is_final` marks the one
    used for quotation.
    """

    __tablename__ = "designs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(128))
    summary: Mapped[str | None] = mapped_column(String, nullable=True)
    is_final: Mapped[bool] = mapped_column(default=False, server_default="0")

    project: Mapped[Project] = relationship("Project", back_populates="designs")
    furniture: Mapped[list[Furniture]] = relationship(
        "Furniture", back_populates="design", cascade="all, delete-orphan",
    )


class Furniture(Base):
    """A single built-in furniture piece."""

    __tablename__ = "furniture"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    design_id: Mapped[int] = mapped_column(ForeignKey("designs.id", ondelete="CASCADE"))
    room_id: Mapped[int | None] = mapped_column(ForeignKey("rooms.id", ondelete="SET NULL"))

    type: Mapped[FurnitureType] = mapped_column(SAEnum(FurnitureType))
    label: Mapped[str] = mapped_column(String(64))  # e.g. "主卧大衣柜"

    # Bounding box of the piece (mm). Used by both 2D rendering and material calc.
    width_mm: Mapped[float] = mapped_column(Float)
    height_mm: Mapped[float] = mapped_column(Float)
    depth_mm: Mapped[float] = mapped_column(Float)

    # Material choice — references a board SKU. Optional until the designer picks one.
    material_id: Mapped[int | None] = mapped_column(ForeignKey("materials.id"), nullable=True)

    design: Mapped[Design] = relationship("Design", back_populates="furniture")
    room: Mapped[Room | None] = relationship("Room")
    material: Mapped[Material | None] = relationship("Material")