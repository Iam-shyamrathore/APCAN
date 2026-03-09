"""
Base SQLAlchemy Model
Industry standard: Common fields for all models (timestamps, soft delete)
"""

from datetime import datetime, UTC
from sqlalchemy import Integer, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _utc_now() -> datetime:
    return datetime.now(UTC)


class BaseModel(Base):
    """
    Abstract base model with common fields
    All models inherit from this
    """

    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utc_now, nullable=False, doc="Record creation timestamp"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=_utc_now,
        onupdate=_utc_now,
        nullable=False,
        doc="Record last update timestamp",
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Soft delete flag - HIPAA compliance (never hard delete patient data)",
    )
