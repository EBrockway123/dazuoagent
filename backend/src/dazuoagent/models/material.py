"""Material (素材库) ORM model.

A material represents a buildable surface — a board type with a specific
thickness and finish. The platform groups materials so designers can browse
"颗粒板 / 18mm / 三聚氰胺 / 哑光白" as a single SKU with a price.
"""

from __future__ import annotations

from enum import StrEnum

from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from dazuoagent.core.database import Base
from dazuoagent.models.base import TimestampMixin


class BoardType(StrEnum):
    """Base substrate for the panel."""

    PARTICLEBOARD = "particleboard"  # 颗粒板
    MULTILAYER = "multilayer"  # 多层板
    MDF = "mdf"  # 密度板
    SOLID_WOOD = "solid_wood"  # 实木


class Veneer(StrEnum):
    """Surface finish applied on top of the substrate."""

    MELAMINE = "melamine"  # 三聚氰胺
    PAINT = "paint"  # 烤漆
    PVC = "pvc"  # PVC 贴膜
    WOOD_VENEER = "wood_veneer"  # 实木贴皮
    WRAP = "wrap"  # 包覆


class HardwareCategory(StrEnum):
    """Categories for hardware (五金) accessories."""

    HINGE = "hinge"
    SLIDE = "slide"
    HANDLE = "handle"
    LIFT = "lift"
    ROD = "rod"  # 挂衣杆 / closet rod


class Material(Base, TimestampMixin):
    """A single sellable SKU — board, finish, and price bundled together.

    For hardware (which isn't board-shaped), leave `board_type` NULL and set
    `unit = "piece"`. `Material` therefore doubles as the "五金" entity.
    """

    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sku: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128), index=True)

    # Board attributes (nullable for hardware SKUs).
    board_type: Mapped[BoardType | None] = mapped_column(SAEnum(BoardType), nullable=True)
    thickness_mm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    veneer: Mapped[Veneer | None] = mapped_column(SAEnum(Veneer), nullable=True)

    # Hardware attribute (nullable for board SKUs).
    hardware_category: Mapped[HardwareCategory | None] = mapped_column(
        SAEnum(HardwareCategory),
        nullable=True,
    )

    color_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    supplier: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Pricing. `unit` is informational ("sqm", "piece", "meter") — converters
    # in services/ handle the math; do not bake assumptions into the schema.
    price: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(16), default="sqm", nullable=False)

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"<Material {self.sku} {self.name}>"
