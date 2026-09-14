from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.crud import crud_alert
from app.schemas.alert import AlertCreate, AlertUpdateStatus, AlertStatusEnum
from app.models.alert import Alert
from app.models.prediction import Prediction

def map_risk_to_priority(risk_level: str) -> str:
    """Map the ML risk level to investigator priority."""
    risk_upper = risk_level.upper() if risk_level else "UNKNOWN"
    if risk_upper == "HIGH":
        return "P1"
    elif risk_upper == "MEDIUM":
        return "P2"
    elif risk_upper == "LOW":
        return "P3"
    return "P4"

def evaluate_and_create_alert(db: Session, prediction: Prediction) -> Alert:
    """
    Evaluates a prediction and creates an alert idempotently.
    """
    # 1. Duplicate check (Idempotency)
    existing_alert = crud_alert.get_alert_by_prediction_id(db, prediction.id)
    if existing_alert:
        return existing_alert

    # 2. Business Logic: Evaluate Risk -> Priority
    priority = map_risk_to_priority(prediction.risk_level)

    # 3. Create Alert
    alert_in = AlertCreate(
        case_id=prediction.case_id,
        prediction_id=prediction.id,
        priority=priority,
        status=AlertStatusEnum.OPEN
    )

    alert = crud_alert.create_alert(db, alert_in)

    # 4. Route Intelligence to Jurisdiction
    from app.services.routing_service import route_intelligence
    if prediction.candidates:
        # Route based on the top candidate ATM
        top_cand = sorted(prediction.candidates, key=lambda x: x.rank)[0]
        route_intelligence(db, prediction, alert, top_cand.atm_id)

    # 5. Dispatch Notifications
    from app.services.notification_service import notification_service
    notification_service.dispatch_alert(db, alert)

    # 5. Broadcast SSE event
    import asyncio
    import json
    from app.api.routes.events import broadcast_event
    try:
        loop = asyncio.get_running_loop()
        payload = json.dumps({
            "type": "NEW_ALERT",
            "case_id": alert.case_id,
            "alert_id": alert.id,
            "prediction_id": alert.prediction_id
        })
        loop.create_task(broadcast_event(payload))
    except RuntimeError:
        # If no event loop (e.g. running outside ASGI like tests), ignore.
        pass

    return alert
def update_alert(db: Session, alert_id: int, status_update: AlertUpdateStatus) -> Alert:
    """
    Updates the status of an alert.
    """
    alert = crud_alert.update_alert_status(db, alert_id=alert_id, status_in=status_update)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert
