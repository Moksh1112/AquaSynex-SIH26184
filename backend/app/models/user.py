from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from app.db.base import Base

class RoleEnum(str, enum.Enum):
    ADMIN = "Administrator"
    I4C_ANALYST = "I4C Analyst"
    LEA_INVESTIGATOR = "LEA Investigator"
    BANK_OFFICER = "Bank Officer"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    organization = Column(String, nullable=True) # e.g. "MH_POLICE", "NCIIPC_FIN"
    created_at = Column(DateTime, default=datetime.utcnow)

    audit_logs = relationship("AuditLog", back_populates="user")
