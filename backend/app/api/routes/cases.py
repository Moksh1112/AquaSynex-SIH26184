from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.api import deps
from app.schemas.case import CaseResponse
from app.services import case_service
from app.models.user import User, RoleEnum

router = APIRouter()

# All roles can read cases
_any_role = deps.require_role(
    RoleEnum.ADMIN.value,
    RoleEnum.I4C_ANALYST.value,
    RoleEnum.LEA_INVESTIGATOR.value,
    RoleEnum.BANK_OFFICER.value
)

@router.get("/cases", response_model=List[CaseResponse])
def get_cases(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(_any_role)
):
    """
    Retrieve a list of cases.
    """
    from app.services.audit_service import log_audit_event
    log_audit_event(db, action="READ", resource="cases", status="SUCCESS", user_id=current_user.id)
    return case_service.get_cases(db, skip=skip, limit=limit)

@router.get("/cases/{case_id}", response_model=CaseResponse)
def get_case(
    case_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(_any_role)
):
    """
    Retrieve a specific case by case_id.
    """
    from app.services.audit_service import log_audit_event
    log_audit_event(db, action="READ", resource=f"case:{case_id}", status="SUCCESS", user_id=current_user.id)
    return case_service.get_case_details(db, case_id=case_id)
