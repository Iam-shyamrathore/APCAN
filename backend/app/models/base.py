"""
Base SQLAlchemy Model
Industry standard: Common fields for all models (timestamps, soft delete)
"""

from datetime import datetime
from sqlalchemy import DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class BaseModel(Base):
    """
    Abstract base model with common fields
    All models inherit from this
    """

    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, doc="Record creation timestamp"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        doc="Record last update timestamp",
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Soft delete flag - HIPAA compliance (never hard delete patient data)",
    )
