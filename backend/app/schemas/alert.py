from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from enum import Enum

class AlertStatusEnum(str, Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"

class AlertBase(BaseModel):
    case_id: str
    prediction_id: Optional[int] = None
    priority: str
    status: AlertStatusEnum

class AlertCreate(AlertBase):
    pass

class AlertUpdateStatus(BaseModel):
    status: AlertStatusEnum

class AlertResponse(AlertBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
