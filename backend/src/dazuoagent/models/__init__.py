"""SQLAlchemy ORM models.

Importing this package registers every mapper on `Base.metadata`, which is
required for `Base.metadata.create_all()` and Alembic autogenerate.
"""

from dazuoagent.models.base import TimestampMixin
from dazuoagent.models.design import Design, Furniture
from dazuoagent.models.material import Material
from dazuoagent.models.project import Project, Room
from dazuoagent.models.quotation import Quotation, QuotationLineItem

__all__ = [
    "Design",
    "Furniture",
    "Material",
    "Project",
    "Quotation",
    "QuotationLineItem",
    "Room",
    "TimestampMixin",
]