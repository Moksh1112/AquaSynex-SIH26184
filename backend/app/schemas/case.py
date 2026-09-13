from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class CaseBase(BaseModel):
    case_id: str
    description: Optional[str] = None
    status: str
    reported_at: datetime

class CaseCreate(CaseBase):
    pass

class CaseResponse(CaseBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)
