from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import AuditLog, User
from schemas import AuditLogResponse
from auth import require_role
from typing import List

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    user_email: str | None = None,
    action: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    query = db.query(AuditLog)
    
    if user_email:
        query = query.filter(AuditLog.user_email == user_email)
    if action:
        query = query.filter(AuditLog.action == action)
    
    return query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()