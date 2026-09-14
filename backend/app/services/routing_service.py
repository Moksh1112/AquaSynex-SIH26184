from sqlalchemy.orm import Session
from datetime import datetime
from app.models.jurisdiction import JurisdictionRouting, StakeholderType, RoutingStatus
from app.models.prediction import Prediction
from app.models.alert import Alert
from app.models.atm import ATM

def determine_jurisdiction(lat: float, lng: float) -> str:
    """
    Determines the jurisdiction based on coordinates.
    This is a prototype local configuration without external API calls.
    """
    # Simple prototype logic: Map everything near Mumbai to Maharashtra LEA.
    if 18.0 <= lat <= 20.0 and 72.0 <= lng <= 74.0:
        return "MH_MUMBAI"
    if 28.0 <= lat <= 29.0 and 77.0 <= lng <= 78.0:
        return "DL_DELHI"
    return "UNKNOWN_JURISDICTION"

def get_target_stakeholders(jurisdiction: str) -> list:
    """
    Maps a jurisdiction to target stakeholder organizations.
    """
    stakeholders = [
        {"type": StakeholderType.I4C, "org": "I4C_HQ"},
        {"type": StakeholderType.BANK_FI, "org": "NCIIPC_FIN"}
    ]

    if jurisdiction == "MH_MUMBAI":
        stakeholders.append({"type": StakeholderType.STATE_LEA, "org": "MH_POLICE"})
        stakeholders.append({"type": StakeholderType.LOCAL_LEA, "org": "MUMBAI_CYBER_CELL"})
    elif jurisdiction == "DL_DELHI":
        stakeholders.append({"type": StakeholderType.STATE_LEA, "org": "DELHI_POLICE"})
        stakeholders.append({"type": StakeholderType.LOCAL_LEA, "org": "DELHI_CYBER_CELL"})
    else:
        stakeholders.append({"type": StakeholderType.STATE_LEA, "org": "DEFAULT_STATE_POLICE"})

    return stakeholders

def route_intelligence(db: Session, prediction: Prediction, alert: Alert, atm_id: str):
    """
    Determines the jurisdiction of the predicted ATM, resolves the appropriate stakeholders,
    and records intelligence distribution routes.
    """
    atm = db.query(ATM).filter(ATM.atm_id == atm_id).first()
    if not atm:
        return []

    jurisdiction = determine_jurisdiction(atm.latitude, atm.longitude)
    stakeholders = get_target_stakeholders(jurisdiction)

    routes = []
    for st in stakeholders:
        routing = JurisdictionRouting(
            prediction_id=prediction.id,
            alert_id=alert.id,
            originating_jurisdiction="NCRP_CENTRAL",
            target_jurisdiction=jurisdiction,
            stakeholder_type=st["type"],
            target_organization=st["org"],
            status=RoutingStatus.DELIVERED,
            delivered_at=datetime.utcnow()
        )
        db.add(routing)
        routes.append(routing)

    db.commit()
    for r in routes:
        db.refresh(r)

    return routes
