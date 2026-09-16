from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.alert import Alert
from app.schemas.alert import AlertCreate, AlertUpdateStatus

def get_alert(db: Session, alert_id: int) -> Optional[Alert]:
    return db.query(Alert).filter(Alert.id == alert_id).first()

def get_alerts(db: Session, skip: int = 0, limit: int = 100) -> List[Alert]:
    return db.query(Alert).offset(skip).limit(limit).all()

def get_alert_by_prediction_id(db: Session, prediction_id: int) -> Optional[Alert]:
    return db.query(Alert).filter(Alert.prediction_id == prediction_id).first()

def create_alert(db: Session, alert_in: AlertCreate) -> Alert:
    # Auto-assign stakeholder and action based on priority
    stakeholder = alert_in.target_stakeholder
    action = alert_in.recommended_action

    if not stakeholder:
        if alert_in.priority == "CRITICAL":
            stakeholder = "I4C"
            action = "ESCALATE_I4C"
        elif alert_in.priority == "HIGH":
            stakeholder = "LEA"
            action = "DEPLOY_LOCAL_TEAM"
        else:
            stakeholder = "BANK_FI"
            action = "MONITOR_ATM"

    db_alert = Alert(
        case_id=alert_in.case_id,
        prediction_id=alert_in.prediction_id,
        priority=alert_in.priority,
        status=alert_in.status.value,
        target_stakeholder=stakeholder,
        recommended_action=action
    )
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)

    return db_alert

def update_alert_status(db: Session, alert_id: int, status_in: AlertUpdateStatus) -> Optional[Alert]:
    db_alert = get_alert(db, alert_id)
    if db_alert:
        old_status = db_alert.status
        db_alert.status = status_in.status.value
        db.commit()
        db.refresh(db_alert)

        # Audit logging is deferred to the API/service layer which has user context
    return db_alert
