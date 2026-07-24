"""Seed the database with sample materials.

Run from the backend directory:

    python -m dazuoagent.db.seed

Idempotent: re-running won't duplicate rows. Materials are keyed on `sku`.
"""

from __future__ import annotations

from sqlalchemy import select

from dazuoagent.core.database import SessionLocal, init_db
from dazuoagent.models.material import (
    BoardType,
    HardwareCategory,
    Material,
    Veneer,
)

SAMPLE_MATERIALS: list[dict] = [
    # --- 板材 (boards) ---
    {
        "sku": "PB-18-MLM-WHITE",
        "name": "颗粒板 18mm 三聚氰胺 哑光白",
        "board_type": BoardType.PARTICLEBOARD,
        "thickness_mm": 18,
        "veneer": Veneer.MELAMINE,
        "color_code": "#F5F4EF",
        "price": 120.0,
        "unit": "sqm",
        "supplier": "示例供应商A",
    },
    {
        "sku": "PB-18-MLM-OAK",
        "name": "颗粒板 18mm 三聚氰胺 橡木纹",
        "board_type": BoardType.PARTICLEBOARD,
        "thickness_mm": 18,
        "veneer": Veneer.MELAMINE,
        "color_code": "#A77B4D",
        "price": 135.0,
        "unit": "sqm",
        "supplier": "示例供应商A",
    },
    {
        "sku": "ML-18-PNT-WHITE",
        "name": "多层板 18mm 烤漆 亮白",
        "board_type": BoardType.MULTILAYER,
        "thickness_mm": 18,
        "veneer": Veneer.PAINT,
        "color_code": "#FFFFFF",
        "price": 280.0,
        "unit": "sqm",
        "supplier": "示例供应商B",
    },
    {
        "sku": "MDF-25-PVC-GREY",
        "name": "密度板 25mm PVC 灰色",
        "board_type": BoardType.MDF,
        "thickness_mm": 25,
        "veneer": Veneer.PVC,
        "color_code": "#9AA0A6",
        "price": 195.0,
        "unit": "sqm",
        "supplier": "示例供应商C",
    },
    {
        "sku": "SW-18-WV-WALNUT",
        "name": "实木 18mm 实木贴皮 胡桃",
        "board_type": BoardType.SOLID_WOOD,
        "thickness_mm": 18,
        "veneer": Veneer.WOOD_VENEER,
        "color_code": "#5B3A29",
        "price": 680.0,
        "unit": "sqm",
        "supplier": "示例供应商D",
    },
    # --- 五金 (hardware) ---
    {
        "sku": "HW-HINGE-SOFT",
        "name": "阻尼铰链",
        "hardware_category": HardwareCategory.HINGE,
        "price": 18.0,
        "unit": "piece",
        "supplier": "示例供应商E",
    },
    {
        "sku": "HW-SLIDE-450",
        "name": "抽屉滑轨 450mm",
        "hardware_category": HardwareCategory.SLIDE,
        "price": 65.0,
        "unit": "piece",
        "supplier": "示例供应商E",
    },
    {
        "sku": "HW-HANDLE-BAR-128",
        "name": "长拉手 128mm",
        "hardware_category": HardwareCategory.HANDLE,
        "price": 25.0,
        "unit": "piece",
        "supplier": "示例供应商E",
    },
    {
        "sku": "HW-LIFT",
        "name": "上翻门气撑",
        "hardware_category": HardwareCategory.LIFT,
        "price": 120.0,
        "unit": "piece",
        "supplier": "示例供应商E",
    },
    {
        "sku": "HW-ROD-900",
        "name": "衣柜挂衣杆 900mm",
        "hardware_category": HardwareCategory.ROD,
        "price": 35.0,
        "unit": "piece",
        "supplier": "示例供应商E",
    },
]


def seed() -> None:
    init_db()
    with SessionLocal() as db:
        existing = {row.sku for row in db.execute(select(Material)).scalars()}
        added = 0
        for spec in SAMPLE_MATERIALS:
            if spec["sku"] in existing:
                continue
            db.add(Material(**spec))
            added += 1
        db.commit()
        print(f"Seeded {added} new material(s); {len(SAMPLE_MATERIALS) - added} already existed.")


if __name__ == "__main__":  # pragma: no cover
    seed()
