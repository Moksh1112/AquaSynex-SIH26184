from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AuditLogBase(BaseModel):
    user_id: Optional[int] = None
    action: str
    resource: str
    status: str

class AuditLogCreate(AuditLogBase):
    pass

class AuditLogResponse(AuditLogBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True
