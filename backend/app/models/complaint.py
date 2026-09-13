from sqlalchemy import Column, Integer, String, DateTime, Enum
from datetime import datetime
import enum
from app.db.base import Base

class ComplaintStatus(str, enum.Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    CLOSED = "CLOSED"

class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    status = Column(Enum(ComplaintStatus), default=ComplaintStatus.OPEN)
    reported_at = Column(DateTime, default=datetime.utcnow)
