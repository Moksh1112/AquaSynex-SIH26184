from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class EvidenceBase(BaseModel):
    case_id: str
    evidence_type: str
    title: str
    source: Optional[str] = None
    created_by: str
    reference_path: Optional[str] = None
    original_filename: Optional[str] = None
    stored_filename: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    collected_at: Optional[datetime] = None

class EvidenceCreate(EvidenceBase):
    pass

class EvidenceResponse(EvidenceBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
