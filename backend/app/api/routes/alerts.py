from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.api import deps
from app.schemas.alert import AlertResponse, AlertUpdateStatus
from app.crud import crud_alert
from app.services import alert_service
from app.models.user import User, RoleEnum

router = APIRouter()

# All roles can read alerts
_read_alert_role = deps.require_role(
    RoleEnum.ADMIN.value,
    RoleEnum.I4C_ANALYST.value,
    RoleEnum.LEA_INVESTIGATOR.value,
    RoleEnum.BANK_OFFICER.value
)

# Only Admin and Investigator can mutate alert status
_mutate_alert_role = deps.require_role(
    RoleEnum.ADMIN.value,
    RoleEnum.LEA_INVESTIGATOR.value
)

@router.get("/alerts", response_model=List[AlertResponse])
def get_alerts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(_read_alert_role)
):
    """
    Retrieve all alerts.
    """
    from app.services.audit_service import log_audit_event
    log_audit_event(db, action="READ", resource="alerts", status="SUCCESS", user_id=current_user.id)
    return crud_alert.get_alerts(db, skip=skip, limit=limit)

@router.get("/alerts/{alert_id}", response_model=AlertResponse)
def get_alert(
    alert_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(_read_alert_role)
):
    """
    Retrieve a specific alert by ID.
    """
    alert = crud_alert.get_alert(db, alert_id=alert_id)
    from app.services.audit_service import log_audit_event
    if not alert:
        log_audit_event(db, action="READ", resource=f"alert:{alert_id}", status="FAILED", user_id=current_user.id)
        raise HTTPException(status_code=404, detail="Alert not found")
    log_audit_event(db, action="READ", resource=f"alert:{alert_id}", status="SUCCESS", user_id=current_user.id)
    return alert

@router.patch("/alerts/{alert_id}/status", response_model=AlertResponse)
def update_alert_status(
    alert_id: int,
    status_update: AlertUpdateStatus,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(_mutate_alert_role)
):
    """
    Update the status of an alert. Restricted to Admin and LEA Investigator.
    """
    from app.services.audit_service import log_audit_event
    try:
        response = alert_service.update_alert(db, alert_id=alert_id, status_update=status_update)
        log_audit_event(db, action="UPDATE_STATUS", resource=f"alert:{alert_id}", status="SUCCESS", user_id=current_user.id)
        return response
    except HTTPException:
        log_audit_event(db, action="UPDATE_STATUS", resource=f"alert:{alert_id}", status="FAILED", user_id=current_user.id)
        raise
