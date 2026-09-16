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
    from app.models.jurisdiction import JurisdictionRouting

    # 1. Fetch base alerts
    alerts = crud_alert.get_alerts(db, skip=skip, limit=limit)

    # 2. Filter by Jurisdiction/Organization and decorate with routes
    filtered_alerts = []
    for a in alerts:
        routes = db.query(JurisdictionRouting).filter(JurisdictionRouting.alert_id == a.id).all()
        # Decorate the alert dictionary with routing info for the UI
        alert_dict = a.__dict__.copy()
        alert_dict["routes"] = [r.target_organization for r in routes]
        if routes:
            # Overwrite target_stakeholder for UI display with a comma-separated list
            alert_dict["target_stakeholder"] = ", ".join([r.target_organization for r in routes])

        if current_user.role == RoleEnum.ADMIN or current_user.role == RoleEnum.I4C_ANALYST:
            filtered_alerts.append(alert_dict)
        else:
            if any(r.target_organization == current_user.organization for r in routes):
                filtered_alerts.append(alert_dict)

    log_audit_event(db, action="READ", resource="alerts", status="SUCCESS", user_id=current_user.id)
    return filtered_alerts

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
    from app.models.jurisdiction import JurisdictionRouting

    if not alert:
        log_audit_event(db, action="READ", resource=f"alert:{alert_id}", status="FAILED", user_id=current_user.id)
        raise HTTPException(status_code=404, detail="Alert not found")

    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.I4C_ANALYST]:
        routes = db.query(JurisdictionRouting).filter(JurisdictionRouting.alert_id == alert.id).all()
        if not any(r.target_organization == current_user.organization for r in routes):
            log_audit_event(db, action="READ", resource=f"alert:{alert_id}", status="UNAUTHORIZED", user_id=current_user.id)
            raise HTTPException(status_code=403, detail="Not authorized to view this jurisdiction's alert")

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
