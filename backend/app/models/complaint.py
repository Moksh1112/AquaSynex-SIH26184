from sqlalchemy import Column, Integer, String, DateTime, Enum, Float
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
    account_id = Column(String, nullable=True, index=True)
    fraud_amount = Column(Float, nullable=True)
    category = Column(String, default="FINANCIAL_FRAUD")
