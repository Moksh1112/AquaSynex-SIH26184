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
    Retrieve a list of cases, filtered by user authorization.
    """
    from app.services.audit_service import log_audit_event
    from app.models.jurisdiction import JurisdictionRouting
    from app.models.alert import Alert

    # 1. Fetch all cases
    all_cases = case_service.get_cases(db, skip=skip, limit=limit)

    # 2. Filter by Jurisdiction/Organization
    if current_user.role == RoleEnum.ADMIN or current_user.role == RoleEnum.I4C_ANALYST:
        # Sees all cases
        filtered_cases = all_cases
    else:
        # Only sees cases where an alert was routed to their organization
        filtered_cases = []
        for c in all_cases:
            # Check if any alert for this case is routed to the user's organization
            has_access = db.query(JurisdictionRouting).join(
                Alert, JurisdictionRouting.alert_id == Alert.id
            ).filter(
                Alert.case_id == c.case_id,
                JurisdictionRouting.target_organization == current_user.organization
            ).first()

            if has_access:
                filtered_cases.append(c)

    log_audit_event(db, action="READ", resource="cases", status="SUCCESS", user_id=current_user.id)
    return filtered_cases

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
