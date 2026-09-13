from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from app.db.base import Base

class AlertStatus(str, enum.Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String, ForeignKey("complaints.case_id"), index=True, nullable=False)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=True)
    priority = Column(String, nullable=False) # e.g. HIGH, MEDIUM, LOW
    status = Column(Enum(AlertStatus), default=AlertStatus.OPEN)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    complaint = relationship("Complaint")
    prediction = relationship("Prediction")
