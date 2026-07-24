"""Smoke tests for the per-panel quotation engine.

Two layers:

* Pure-Python panel-expansion tests — no DB required, verify each
  `FurnitureType` produces the expected set of panel roles.
* Hardware derivation tests — pure-Python too, verify each furniture
  type produces the correct hinge / handle / rod count from its
  panel layout.
* Integration tests — run `recompute_from_design` against an in-memory
  SQLite DB to confirm the engine → ORM → line-item wiring end-to-end,
  including hardware lookup and silent skip when no SKU is seeded.
"""

# ruff: noqa: RUF001, RUF002, RUF003  # U+00D7 multiplication sign (×) is
# intentional in Chinese-context descriptions and line-item text; the
# rule flags it as ambiguous with U+0078 'x' but in this codebase the
# glyph carries meaning.

from __future__ import annotations

from collections import Counter

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dazuoagent.core.database import Base
from dazuoagent.models.design import Design, Furniture, FurnitureType
from dazuoagent.models.material import BoardType, HardwareCategory, Material, Veneer
from dazuoagent.models.project import Project
from dazuoagent.models.quotation import Quotation, QuotationStatus
from dazuoagent.services.quotation_service import (
    _derive_hardware,
    _expand_panels,
    recompute_from_design,
    total_panel_area_sqm,
)

# ---------------------------------------------------------------------------
# Unit tests: panel expansion per furniture type (no DB)
# ---------------------------------------------------------------------------


def _make_piece(furniture_type: FurnitureType, w=2400, h=2400, d=600, label="test") -> Furniture:
    """Construct an *uncommitted* Furniture row; SQLAlchemy lets us poke at
    its attributes without a session for the pure-math tests below."""
    return Furniture(
        type=furniture_type,
        label=label,
        width_mm=w,
        height_mm=h,
        depth_mm=d,
    )


def test_panel_unit_area_conversion() -> None:
    """1m × 1m board → 1.0 sqm."""
    piece = _make_piece(FurnitureType.WARDROBE)
    side = _expand_panels(piece)[0]  # first side panel: d × h = 600 × 2400
    assert side.unit_area_sqm == pytest.approx(0.6 * 2.4)


def test_expand_wardrobe_role_counts() -> None:
    """A 2400×2400×600 wardrobe should produce all seven panel roles with
    the expected counts (2 sides, 1 each of top/bottom/back, 2 doors,
    ≥3 shelves spaced 800mm, ≥1 vertical divider)."""
    piece = _make_piece(FurnitureType.WARDROBE)
    panels = _expand_panels(piece)
    counts = Counter()
    for p in panels:
        counts[p.role] += p.count

    assert counts["侧板"] == 2
    assert counts["顶板"] == 1
    assert counts["底板"] == 1
    assert counts["背板"] == 1
    assert counts["门板"] == 2
    assert counts["层板"] >= 3  # 2400 / 800 → floor(3)
    assert counts["立板"] >= 1  # (2400 / 900) − 1 = 1
    assert set(counts.keys()) == {"侧板", "顶板", "底板", "背板", "门板", "层板", "立板"}


def test_expand_wardrobe_open_skips_doors_and_back() -> None:
    piece = _make_piece(FurnitureType.WARDROBE_OPEN)
    roles = {p.role for p in _expand_panels(piece)}
    assert "门板" not in roles
    assert "背板" not in roles


def test_expand_kitchen_cabinet_has_single_door() -> None:
    piece = _make_piece(FurnitureType.KITCHEN_CABINET, w=600, h=800, d=550)
    counts = Counter()
    for p in _expand_panels(piece):
        counts[p.role] += p.count
    assert counts["门板"] == 1  # single-door cabinet
    assert counts["背板"] == 1
    assert counts["层板"] >= 1  # 800 / 600 → 1


def test_expand_tv_stand_low_height_few_shelves() -> None:
    piece = _make_piece(FurnitureType.TV_STAND, w=2000, h=450, d=400)
    counts = Counter()
    for p in _expand_panels(piece):
        counts[p.role] += p.count
    assert counts["门板"] == 2
    assert counts["层板"] == 1  # 450 / 400 → floor(1)


def test_expand_default_other_is_minimal_box() -> None:
    piece = _make_piece(FurnitureType.OTHER, w=1000, h=1000, d=500)
    panels = _expand_panels(piece)
    # 3 distinct roles; side panel has count=2 (encoded on the dataclass).
    assert [p.role for p in panels] == ["侧板", "顶板", "底板"]
    assert panels[0].count == 2
    assert panels[1].count == 1
    assert panels[2].count == 1


def test_total_panel_area_grows_with_piece_count() -> None:
    """Two wardrobes should have double the total panel area of one."""
    one = [_make_piece(FurnitureType.WARDROBE)]
    two = [*one, _make_piece(FurnitureType.WARDROBE)]
    assert total_panel_area_sqm(two) == pytest.approx(total_panel_area_sqm(one) * 2)


# ---------------------------------------------------------------------------
# Unit tests: hardware derivation (no DB)
# ---------------------------------------------------------------------------


def test_hardware_wardrobe_two_doors_two_rods() -> None:
    piece = _make_piece(FurnitureType.WARDROBE, w=2400, h=2400, d=600)
    panels = _expand_panels(piece)
    needs = _derive_hardware(piece, panels)
    by_cat = {n.category: n.qty for n in needs}
    assert by_cat[HardwareCategory.HINGE] == 4  # 2 doors × 2
    assert by_cat[HardwareCategory.HANDLE] == 2
    assert by_cat[HardwareCategory.ROD] == 2  # floor(2400/900) = 2


def test_hardware_wardrobe_open_no_hinges_no_handles() -> None:
    piece = _make_piece(FurnitureType.WARDROBE_OPEN, w=2400, h=2400, d=600)
    needs = _derive_hardware(piece, _expand_panels(piece))
    cats = {n.category for n in needs}
    assert HardwareCategory.HINGE not in cats
    assert HardwareCategory.HANDLE not in cats
    assert HardwareCategory.ROD in cats


def test_hardware_tv_stand_two_doors_no_rod() -> None:
    piece = _make_piece(FurnitureType.TV_STAND, w=2000, h=450, d=400)
    needs = _derive_hardware(piece, _expand_panels(piece))
    by_cat = {n.category: n.qty for n in needs}
    assert by_cat[HardwareCategory.HINGE] == 4
    assert by_cat[HardwareCategory.HANDLE] == 2
    assert HardwareCategory.ROD not in by_cat


def test_hardware_bookcase_is_empty() -> None:
    piece = _make_piece(FurnitureType.BOOKCASE)
    needs = _derive_hardware(piece, _expand_panels(piece))
    assert needs == []


def test_hardware_other_is_empty() -> None:
    piece = _make_piece(FurnitureType.OTHER)
    needs = _derive_hardware(piece, _expand_panels(piece))
    assert needs == []


def test_hardware_narrow_wardrobe_rod_floor_one() -> None:
    """A wardrobe narrower than the rod-spacing still gets one rod
    (max(1, …) clamps)."""
    piece = _make_piece(FurnitureType.WARDROBE, w=800, h=2400, d=600)
    needs = _derive_hardware(piece, _expand_panels(piece))
    by_cat = {n.category: n.qty for n in needs}
    assert by_cat[HardwareCategory.ROD] == 1


# ---------------------------------------------------------------------------
# Integration tests: recompute_from_design round-trip on in-memory SQLite
# ---------------------------------------------------------------------------


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    # Ensure every model mapper is registered before create_all.
    from dazuoagent import models  # noqa: F401

    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)
    s = TestSession()
    try:
        yield s
    finally:
        s.close()


def _seed_design(session, piece_width_mm=2400, piece_height_mm=2400, piece_depth_mm=600):
    """Populate a Project / Design / Furniture / Material chain."""
    mat = Material(
        sku="TEST-WHITE-001",
        name="测试白哑光",
        board_type=BoardType.PARTICLEBOARD,
        veneer=Veneer.MELAMINE,
        thickness_mm=18,
        price=200.0,
        unit="sqm",
    )
    session.add(mat)
    session.flush()

    proj = Project(name="测试项目", customer_name="测试客户")
    session.add(proj)
    session.flush()

    design = Design(project_id=proj.id, name="主方案")
    session.add(design)
    session.flush()

    piece = Furniture(
        design_id=design.id,
        type=FurnitureType.WARDROBE,
        label="主卧大衣柜",
        width_mm=piece_width_mm,
        height_mm=piece_height_mm,
        depth_mm=piece_depth_mm,
        material_id=mat.id,
    )
    session.add(piece)
    session.flush()

    quotation = Quotation(project_id=proj.id, design_id=design.id, status=QuotationStatus.DRAFT)
    session.add(quotation)
    session.flush()
    return quotation, design, piece, mat


def _seed_hardware(session) -> None:
    """Three test SKUs across the categories the engine looks up first."""
    for sku, cat, price, name in [
        ("HW-T-HINGE", HardwareCategory.HINGE, 18.0, "测试阻尼铰链"),
        ("HW-T-HANDLE", HardwareCategory.HANDLE, 25.0, "测试长拉手"),
        ("HW-T-ROD", HardwareCategory.ROD, 35.0, "测试挂衣杆"),
    ]:
        session.add(
            Material(
                sku=sku,
                name=name,
                hardware_category=cat,
                price=price,
                unit="piece",
                supplier="test",
            ),
        )
    session.flush()


def test_recompute_emits_one_line_per_role(session) -> None:
    """Without hardware seeded, only the 7 board rows appear — verifies
    the engine doesn't break in an empty showroom."""
    quotation, design, _piece, _mat = _seed_design(session)
    result = recompute_from_design(session, quotation.id, design.id)
    assert result is not None
    assert len(result.line_items) == 7
    roles_in_lines = {line.description.split(" · ")[1] for line in result.line_items}
    assert roles_in_lines == {"侧板", "顶板", "底板", "背板", "门板", "层板", "立板"}
    assert result.subtotal == pytest.approx(sum(li.amount for li in result.line_items))
    assert result.total == pytest.approx(result.subtotal + result.labor_cost + result.tax)
    assert result.labor_cost > 0


def test_recompute_emits_placeholder_for_missing_material(session) -> None:
    """A no-material wardrobe emits one '未选板材' row (no SKU → no hardware rows)."""
    quotation, design, piece, _mat = _seed_design(session)
    piece.material_id = None
    session.flush()
    result = recompute_from_design(session, quotation.id, design.id)
    assert len(result.line_items) == 1
    assert "未选板材" in result.line_items[0].description
    assert result.line_items[0].amount == 0.0


def test_recompute_emits_panel_and_hardware_rows_together(session) -> None:
    """With hardware SKUs seeded, a 2400 wardrobe = 7 panels + 3 hardware rows."""
    quotation, design, _piece, _mat = _seed_design(session)
    _seed_hardware(session)
    result = recompute_from_design(session, quotation.id, design.id)
    assert len(result.line_items) == 10

    by_unit: dict[str, list] = {"sqm": [], "piece": []}
    for li in result.line_items:
        by_unit[li.unit].append(li)
    assert len(by_unit["sqm"]) == 7
    assert len(by_unit["piece"]) == 3

    hinge = next(li for li in by_unit["piece"] if "铰链" in li.description)
    assert hinge.quantity == 4
    assert hinge.unit_price == 18.0
    assert hinge.amount == pytest.approx(72.0)

    handle = next(li for li in by_unit["piece"] if "拉手" in li.description)
    assert handle.quantity == 2
    assert handle.amount == pytest.approx(50.0)

    rod = next(li for li in by_unit["piece"] if "挂衣杆" in li.description)
    assert rod.quantity == 2
    assert rod.amount == pytest.approx(70.0)


def test_recompute_no_material_still_emits_hardware(session) -> None:
    """A no-material wardrobe still gets hardware rows so the customer
    can preview the total project cost."""
    quotation, design, piece, _mat = _seed_design(session)
    piece.material_id = None
    _seed_hardware(session)
    session.flush()
    result = recompute_from_design(session, quotation.id, design.id)
    # 1 placeholder + 3 hardware rows
    assert len(result.line_items) == 4
    assert any("未选板材" in li.description for li in result.line_items)
    assert any("铰链" in li.description for li in result.line_items)
    assert any("挂衣杆" in li.description for li in result.line_items)


def test_recompute_skips_missing_hardware_sku_gracefully(session) -> None:
    """If a furniture type calls for hardware but the showroom has no
    matching SKU, the line is silently skipped — no crash, no orphan line."""
    quotation, design, _piece, _mat = _seed_design(session)
    # Only seed HINGE — HANDLE and ROD lookups should fail and be skipped.
    session.add(
        Material(
            sku="HW-T-HINGE-ONLY",
            name="测试铰链",
            hardware_category=HardwareCategory.HINGE,
            price=18.0,
            unit="piece",
            supplier="test",
        ),
    )
    session.flush()

    result = recompute_from_design(session, quotation.id, design.id)
    # 7 panel rows + 1 hinge (handles and rods are silently skipped).
    assert len(result.line_items) == 8
    assert any("铰链" in li.description for li in result.line_items)
    assert not any("拉手" in li.description for li in result.line_items)
    assert not any("挂衣杆" in li.description for li in result.line_items)


def test_recompute_tv_stand_hinges_no_rod(session) -> None:
    """TV stand: 4 阻尼铰链 + 2 拉手, no 挂衣杆."""
    quotation, design, piece, _mat = _seed_design(session)
    piece.type = FurnitureType.TV_STAND
    piece.width_mm, piece.height_mm, piece.depth_mm = 2000, 450, 400
    session.flush()
    _seed_hardware(session)
    result = recompute_from_design(session, quotation.id, design.id)
    descs = [li.description for li in result.line_items]
    assert any("铰链 ×4" in d for d in descs)
    assert any("拉手 ×2" in d for d in descs)
    assert not any("挂衣杆" in d for d in descs)


def test_recompute_is_idempotent(session) -> None:
    """Running `recompute_from_design` twice yields the same line items."""
    quotation, design, _piece, _mat = _seed_design(session)
    _seed_hardware(session)
    first = recompute_from_design(session, quotation.id, design.id)
    second = recompute_from_design(session, quotation.id, design.id)
    assert len(first.line_items) == len(second.line_items)
    assert [li.amount for li in first.line_items] == [li.amount for li in second.line_items]
