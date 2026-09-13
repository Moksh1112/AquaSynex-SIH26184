from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String, ForeignKey("complaints.case_id"), index=True, nullable=False)
    risk_level = Column(String, nullable=False) # e.g. "HIGH"
    time_window = Column(String, nullable=False) # e.g. "22:00-23:00"
    
    # Store the top N ranked ATMs and their scores as JSON array
    # or we could normalize it, but JSON is fine for prototype snapshot.
    # To keep schema simple and relational as requested, we can normalize it:
    
    explanation = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    complaint = relationship("Complaint")
    candidates = relationship("PredictionCandidate", back_populates="prediction", cascade="all, delete-orphan")

class PredictionCandidate(Base):
    __tablename__ = "prediction_candidates"

    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=False)
    atm_id = Column(String, ForeignKey("atms.atm_id"), nullable=False)
    rank = Column(Integer, nullable=False)
    probability = Column(Float, nullable=False)
    risk = Column(String, nullable=False)

    prediction = relationship("Prediction", back_populates="candidates")
    atm = relationship("ATM")
