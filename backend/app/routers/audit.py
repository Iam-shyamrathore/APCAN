"""
Audit Log Router — Phase 5
REST endpoint for querying HIPAA audit logs.
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["Audit"])


class AuditLogResponse(PydanticBaseModel):
    """Single audit log entry."""

    id: int
    timestamp: datetime
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    agent: Optional[str] = None
    action: str
    tool_name: Optional[str] = None
    tool_args: Optional[dict] = None
    patient_id: Optional[int] = None
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    success: bool
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


class AuditLogsListResponse(PydanticBaseModel):
    """Paginated audit log response."""

    total: int
    logs: list[AuditLogResponse]


@router.get(
    "/logs",
    response_model=AuditLogsListResponse,
    summary="Query audit logs",
)
async def get_audit_logs(
    patient_id: Optional[int] = Query(default=None, description="Filter by patient ID"),
    user_id: Optional[int] = Query(default=None, description="Filter by user ID"),
    session_id: Optional[str] = Query(default=None, description="Filter by session ID"),
    action: Optional[str] = Query(default=None, description="Filter by action type"),
    limit: int = Query(default=100, ge=1, le=1000, description="Max results"),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve audit log entries with optional filters."""
    svc = AuditService(db)
    logs = await svc.get_logs(
        patient_id=patient_id,
        user_id=user_id,
        session_id=session_id,
        action=action,
        limit=limit,
    )
    return AuditLogsListResponse(
        total=len(logs),
        logs=[AuditLogResponse.model_validate(log) for log in logs],
    )
