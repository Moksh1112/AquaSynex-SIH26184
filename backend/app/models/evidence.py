from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String, ForeignKey("complaints.case_id"), index=True, nullable=False)
    evidence_type = Column(String, nullable=False) # e.g. TRANSACTION_LOG, POLICE_REPORT, VIDEO
    title = Column(String, nullable=False)
    source = Column(String, nullable=True) # e.g. Bank, NCRP
    collected_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, nullable=False) # user id or role
    created_at = Column(DateTime, default=datetime.utcnow)
    reference_path = Column(String, nullable=True) # secure reference rather than arbitrary file upload
    original_filename = Column(String, nullable=True)
    stored_filename = Column(String, nullable=True)
    mime_type = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)

    complaint = relationship("Complaint")
