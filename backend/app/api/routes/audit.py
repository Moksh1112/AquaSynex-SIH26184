from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.api import deps
from app.schemas.audit import AuditLogResponse
from app.crud import crud_audit
from app.models.user import User, RoleEnum

router = APIRouter()

# Only ADMIN can access audit logs
_audit_role = deps.require_role(RoleEnum.ADMIN.value)

@router.get("/audit", response_model=List[AuditLogResponse])
def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(_audit_role)
):
    """
    Retrieve audit logs. Restricted to Administrator.
    """
    return crud_audit.get_audit_logs(db, skip=skip, limit=limit)
