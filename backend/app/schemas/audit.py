from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, field_validator

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
    username: Optional[str] = None

    @field_validator('timestamp', mode='before')
    @classmethod
    def force_utc(cls, v):
        if isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    class Config:
        from_attributes = True
