"""Quotation service — pricing engine lives here.

`recompute_from_design` walks every `Furniture` on a design, expands each
piece into its constituent panels (sides, top, bottom, back, doors,
shelves, dividers), looks up the chosen material, and emits one
`QuotationLineItem` per piece × panel role. It also derives hardware
requirements from the panel layout (hinges per door, rods per wardrobe
width, …) and resolves them to whatever SKU was seeded for that
category.

This is the only place to change pricing rules — the agent and the UI
both call into here.

Panel layout conventions:

* `w`, `h`, `d` are the bounding-box dimensions of the furniture piece
  (all in mm). Internal panels do not subtract board thickness — for the
  MVP that's noise; tighten if board thickness > 25 mm starts to bite.
* Roles carry Chinese labels because the line-item description is shown
  to end customers on the quotation page.
"""

# ruff: noqa: RUF001, RUF002, RUF003  # U+00D7 multiplication sign (×) is the
# on-the-wire quantity glyph in line-item descriptions (e.g.
# "主卧大衣柜 · 阻尼铰链 ×4") — the rule flags it as ambiguous with U+0078
# 'x' but in this codebase the glyph carries meaning.

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from dazuoagent.models.design import Design, Furniture, FurnitureType
from dazuoagent.models.material import HardwareCategory, Material
from dazuoagent.models.quotation import Quotation, QuotationLineItem, QuotationStatus
from dazuoagent.schemas.quotation import QuotationCreate

# ---------------------------------------------------------------------------
# Pricing constants — tune here, no magic numbers in the calc functions.
# ---------------------------------------------------------------------------
DEFAULT_LABOR_RATE: float = 80.0  # ¥/㎡  加工费 / sqm of expanded panel surface
DEFAULT_TAX_RATE: float = 0.0  # 0% for now; toggle per project later
HARDWARE_LABOR_MULTIPLIER: float = 1.1  # 安装 / 五金加成

# Vertical spacing target between shelf panels (mm). A 2400 mm wardrobe
# gets 3 层板 by this rule.
SHELF_SPACING: dict[FurnitureType, int] = {
    FurnitureType.WARDROBE: 800,
    FurnitureType.WARDROBE_OPEN: 400,
    FurnitureType.KITCHEN_CABINET: 600,
    FurnitureType.TV_STAND: 400,
    FurnitureType.BOOKCASE: 320,
    FurnitureType.SHOE_CABINET: 350,
}
HORIZONTAL_DIVIDER_SPACING: int = 900  # 立板间距, 没有的不算
CLOSET_ROD_SPACING: int = 900  # 挂衣杆间距 (衣柜宽度方向)

# Chinese labels per hardware category — used in line-item descriptions.
HARDWARE_LABELS: dict[HardwareCategory, str] = {
    HardwareCategory.HINGE: "阻尼铰链",
    HardwareCategory.SLIDE: "抽屉滑轨",
    HardwareCategory.HANDLE: "拉手",
    HardwareCategory.LIFT: "上翻门气撑",
    HardwareCategory.ROD: "挂衣杆",
}


@dataclass(frozen=True)
class Panel:
    """One board in a furniture piece.

    `count` of identical panels (e.g. 2 side panels) — we keep them as one
    dataclass so the line-item aggregation can sum `count * area` per
    role cleanly.
    """

    role: str  # 侧板 / 顶板 / 底板 / 背板 / 门板 / 层板 / 立板
    width_mm: float
    height_mm: float
    count: int = 1

    @property
    def unit_area_sqm(self) -> float:
        return self.width_mm * self.height_mm / 1_000_000

    @property
    def total_area_sqm(self) -> float:
        return self.unit_area_sqm * self.count


@dataclass(frozen=True)
class HardwareNeed:
    """A hardware requirement derived from a furniture piece."""

    category: HardwareCategory
    qty: int


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_quotation(db: Session, quotation_id: int) -> Quotation | None:
    return db.get(Quotation, quotation_id)


def create_quotation(db: Session, payload: QuotationCreate) -> Quotation:
    subtotal = sum(item.quantity * item.unit_price for item in payload.line_items)
    total = subtotal + payload.labor_cost + payload.tax

    quotation = Quotation(
        project_id=payload.project_id,
        design_id=payload.design_id,
        status=payload.status,
        labor_cost=payload.labor_cost,
        tax=payload.tax,
        notes=payload.notes,
        subtotal=subtotal,
        total=total,
        line_items=[QuotationLineItem(**item.model_dump()) for item in payload.line_items],
    )
    db.add(quotation)
    db.commit()
    db.refresh(quotation)
    return quotation


def recompute_from_design(
    db: Session,
    quotation_id: int,
    design_id: int,
) -> Quotation | None:
    """Recompute every line item on `quotation_id` from the latest design.

    Snapshot semantics: quotes are immutable snapshots of the design +
    material price at issue time. We wipe and rebuild on every recompute
    so callers can iterate without leaving detritus behind.
    """
    quotation = db.get(Quotation, quotation_id)
    design = db.get(Design, design_id)
    if quotation is None or design is None:
        return None

    quotation.line_items.clear()
    db.flush()

    for piece in design.furniture:
        _price_furniture(db, quotation, piece)

    quotation.subtotal = sum(item.amount for item in quotation.line_items)
    quotation.labor_cost = _estimate_labor(design)
    quotation.tax = round(quotation.subtotal * DEFAULT_TAX_RATE, 2)
    quotation.total = quotation.subtotal + quotation.labor_cost + quotation.tax

    if quotation.status == QuotationStatus.DRAFT:
        # Don't auto-promote beyond draft — explicit POST /issue handles that.
        pass

    db.commit()
    db.refresh(quotation)
    return quotation


# ---------------------------------------------------------------------------
# Panel expansion — the heart of the pricing engine.
# ---------------------------------------------------------------------------


_PANEL_EXPANSION: dict[FurnitureType, Callable[[Furniture], list[Panel]]] = {}


def _expand_panels(piece: Furniture) -> list[Panel]:
    """Dispatch by furniture type to its panel-breakdown rules."""
    expansion = _PANEL_EXPANSION.get(piece.type, _expand_default)
    return expansion(piece)


def _register_expansion(
    furniture_type: FurnitureType,
) -> Callable[[Callable[[Furniture], list[Panel]]], Callable[[Furniture], list[Panel]]]:
    """Decorator that wires `_expand_*` into the dispatch table at import time."""

    def decorator(fn: Callable[[Furniture], list[Panel]]) -> Callable[[Furniture], list[Panel]]:
        _PANEL_EXPANSION[furniture_type] = fn
        return fn

    return decorator


def _shelf_count(height_mm: float, furniture_type: FurnitureType) -> int:
    """How many horizontal shelf panels fit at the recommended spacing."""
    spacing = SHELF_SPACING.get(furniture_type, 0)
    if spacing <= 0:
        return 0
    return max(1, int(height_mm / spacing))


def _divider_count(width_mm: float) -> int:
    """How many vertical dividers fit between the side panels."""
    if width_mm <= 0:
        return 0
    return max(0, int(width_mm / HORIZONTAL_DIVIDER_SPACING) - 1)


@_register_expansion(FurnitureType.WARDROBE)
def _expand_wardrobe(piece: Furniture) -> list[Panel]:
    """Closed wardrobe with two hinged doors.

    For a 2400×2400×600 piece: 2 sides, top+bottom (1+1), back (1),
    2 doors, 3 shelves, 1 vertical divider.
    """
    w, h, d = piece.width_mm, piece.height_mm, piece.depth_mm
    return [
        Panel("侧板", d, h, 2),
        Panel("顶板", w, d),
        Panel("底板", w, d),
        Panel("背板", w, h),
        Panel("门板", w / 2, h, 2),
        Panel("层板", w, d, _shelf_count(h, FurnitureType.WARDROBE)),
        Panel("立板", d, h, _divider_count(w)),
    ]


@_register_expansion(FurnitureType.WARDROBE_OPEN)
def _expand_wardrobe_open(piece: Furniture) -> list[Panel]:
    """Walk-in closet: no doors, no back, dense shelving."""
    w, h, d = piece.width_mm, piece.height_mm, piece.depth_mm
    return [
        Panel("侧板", d, h, 2),
        Panel("顶板", w, d),
        Panel("底板", w, d),
        Panel("层板", w, d, _shelf_count(h, FurnitureType.WARDROBE_OPEN)),
        Panel("立板", d, h, _divider_count(w)),
    ]


@_register_expansion(FurnitureType.KITCHEN_CABINET)
def _expand_kitchen_cabinet(piece: Furniture) -> list[Panel]:
    """Base kitchen cabinet — narrower, single door, fewer shelves."""
    w, h, d = piece.width_mm, piece.height_mm, piece.depth_mm
    return [
        Panel("侧板", d, h, 2),
        Panel("顶板", w, d),
        Panel("底板", w, d),
        Panel("背板", w, h),
        Panel("门板", w, h),
        Panel("层板", w, d, _shelf_count(h, FurnitureType.KITCHEN_CABINET)),
    ]


@_register_expansion(FurnitureType.TV_STAND)
def _expand_tv_stand(piece: Furniture) -> list[Panel]:
    """Low TV console — short, two doors, a couple of shelves."""
    w, h, d = piece.width_mm, piece.height_mm, piece.depth_mm
    return [
        Panel("侧板", d, h, 2),
        Panel("顶板", w, d),
        Panel("底板", w, d),
        Panel("背板", w, h),
        Panel("门板", w / 2, h, 2),
        Panel("层板", w, d, _shelf_count(h, FurnitureType.TV_STAND)),
    ]


@_register_expansion(FurnitureType.BOOKCASE)
def _expand_bookcase(piece: Furniture) -> list[Panel]:
    """Open-backed bookcase — many shelves, back panel for stiffness."""
    w, h, d = piece.width_mm, piece.height_mm, piece.depth_mm
    return [
        Panel("侧板", d, h, 2),
        Panel("顶板", w, d),
        Panel("底板", w, d),
        Panel("背板", w, h),
        Panel("层板", w, d, _shelf_count(h, FurnitureType.BOOKCASE)),
        Panel("立板", d, h, _divider_count(w)),
    ]


@_register_expansion(FurnitureType.SHOE_CABINET)
def _expand_shoe_cabinet(piece: Furniture) -> list[Panel]:
    """Shoe storage — shallow depth, dense horizontal shelves."""
    w, h, d = piece.width_mm, piece.height_mm, piece.depth_mm
    return [
        Panel("侧板", d, h, 2),
        Panel("顶板", w, d),
        Panel("底板", w, d),
        Panel("背板", w, h),
        Panel("门板", w, h),
        Panel("层板", w, d, _shelf_count(h, FurnitureType.SHOE_CABINET)),
    ]


def _expand_default(piece: Furniture) -> list[Panel]:
    """Fallback for `FurnitureType.OTHER`: just a closed box, no doors/shelves."""
    w, h, d = piece.width_mm, piece.height_mm, piece.depth_mm
    return [
        Panel("侧板", d, h, 2),
        Panel("顶板", w, d),
        Panel("底板", w, d),
    ]


# ---------------------------------------------------------------------------
# Hardware derivation — turn a piece's panel layout into a list of needs.
# ---------------------------------------------------------------------------


def _derive_hardware(piece: Furniture, panels: list[Panel]) -> list[HardwareNeed]:
    """Per-piece hardware requirements.

    Reads panel info (e.g. door count) so the rules stay consistent when
    panel layouts change. Returns an empty list for furniture types that
    take no hardware (bookcase, other).
    """
    doors = sum(p.count for p in panels if p.role == "门板")
    width_mm = piece.width_mm
    needs: list[HardwareNeed] = []

    if piece.type == FurnitureType.WARDROBE:
        if doors > 0:
            needs.append(HardwareNeed(HardwareCategory.HINGE, doors * 2))
            needs.append(HardwareNeed(HardwareCategory.HANDLE, doors))
        needs.append(HardwareNeed(HardwareCategory.ROD, max(1, int(width_mm / CLOSET_ROD_SPACING))))
    elif piece.type == FurnitureType.WARDROBE_OPEN:
        needs.append(HardwareNeed(HardwareCategory.ROD, max(1, int(width_mm / CLOSET_ROD_SPACING))))
    elif piece.type in (
        FurnitureType.KITCHEN_CABINET,
        FurnitureType.TV_STAND,
        FurnitureType.SHOE_CABINET,
    ):
        if doors > 0:
            needs.append(HardwareNeed(HardwareCategory.HINGE, doors * 2))
            needs.append(HardwareNeed(HardwareCategory.HANDLE, doors))
    # BOOKCASE / OTHER: nothing.

    return needs


def _default_hardware_for(db: Session, category: HardwareCategory) -> Material | None:
    """Resolve the standard SKU for a hardware category.

    Returns the lowest-id SKU of that category (stable order via the
    deterministic seed). Returns None if the showroom has no SKU of
    this category yet — callers should then skip the line.
    """
    return db.execute(
        select(Material)
        .where(Material.hardware_category == category)
        .order_by(Material.id)
        .limit(1)
    ).scalar_one_or_none()


# ---------------------------------------------------------------------------
# Pricing helpers — turn the panel list into line items + labor estimate.
# ---------------------------------------------------------------------------


def _price_furniture(db: Session, quotation: Quotation, piece: Furniture) -> None:
    """Emit line items for one furniture piece.

    Two flows:

    * **Boards** — one line per piece × panel role, area × material price.
    * **Hardware** — one line per piece × category, qty × SKU price.

    For pieces with no material chosen, a single placeholder row covers
    the boards; hardware rows are still emitted so the customer sees the
    total project cost even before finishes are picked.
    """
    panels = _expand_panels(piece)

    if piece.material is None:
        quotation.line_items.append(
            QuotationLineItem(
                description=f"{piece.label} (未选板材)",
                quantity=0.0,
                unit="sqm",
                unit_price=0.0,
                amount=0.0,
            ),
        )
    else:
        # Sum area per role → one line item per role for this piece.
        sqm_by_role: dict[str, float] = defaultdict(float)
        panel_count_by_role: dict[str, int] = defaultdict(int)
        for p in panels:
            sqm_by_role[p.role] += p.total_area_sqm
            panel_count_by_role[p.role] += p.count

        for role, sqm in sqm_by_role.items():
            if sqm <= 0:
                continue
            n = panel_count_by_role[role]
            desc = f"{piece.label} · {role} · {piece.material.name}" + (f" ×{n}" if n > 1 else "")
            quotation.line_items.append(
                QuotationLineItem(
                    description=desc,
                    quantity=round(sqm, 3),
                    unit="sqm",
                    unit_price=piece.material.price,
                    amount=round(sqm * piece.material.price, 2),
                ),
            )

    # Hardware rows — fires regardless of material choice so the customer
    # can see the total cost while iterating on finishes.
    for need in _derive_hardware(piece, panels):
        if need.qty <= 0:
            continue
        hw = _default_hardware_for(db, need.category)
        if hw is None:
            # No SKU of this category in the showroom yet. Skip rather
            # than crash — the customer can still see the board lines.
            continue
        label = HARDWARE_LABELS.get(need.category, need.category.value)
        quotation.line_items.append(
            QuotationLineItem(
                description=f"{piece.label} · {label} ×{need.qty}",
                quantity=float(need.qty),
                unit="piece",
                unit_price=hw.price,
                amount=round(need.qty * hw.price, 2),
            ),
        )


def total_panel_area_sqm(pieces: list[Furniture]) -> float:
    """Public helper for callers that want the raw panel area (e.g. for
    custom labor quotes). Not used by `recompute_from_design` directly.
    """
    total = 0.0
    for piece in pieces:
        for p in _expand_panels(piece):
            total += p.total_area_sqm
    return total


def _estimate_labor(design: Design) -> float:
    """Labor cost as a function of expanded panel area.

    Real factories charge per piece of hardware + per linear meter of
    edge banding; the sqm-based heuristic is good enough until those
    signals are added to the furniture model.
    """
    total_sqm = total_panel_area_sqm(list(design.furniture))
    return round(total_sqm * DEFAULT_LABOR_RATE * HARDWARE_LABOR_MULTIPLIER, 2)
