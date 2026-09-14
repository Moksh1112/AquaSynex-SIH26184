from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db.base import Base

class StakeholderType(str, enum.Enum):
    I4C = "I4C"
    STATE_LEA = "STATE_LEA"
    LOCAL_LEA = "LOCAL_LEA"
    BANK_FI = "BANK_FI"

class RoutingStatus(str, enum.Enum):
    PENDING = "PENDING"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"

class JurisdictionRouting(Base):
    __tablename__ = "jurisdiction_routing"

    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=False)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False)

    originating_jurisdiction = Column(String, nullable=False)
    target_jurisdiction = Column(String, nullable=False)
    stakeholder_type = Column(Enum(StakeholderType), nullable=False)
    target_organization = Column(String, nullable=False)

    status = Column(Enum(RoutingStatus), default=RoutingStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime, nullable=True)

    prediction = relationship("Prediction")
    alert = relationship("Alert")
