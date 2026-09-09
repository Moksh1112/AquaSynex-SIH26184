from pydantic import BaseModel

class AlertBase(BaseModel):
    alert_id: str
    case_id: str
    atm_id: str
    risk: str
    status: str
    recommended_action: str
