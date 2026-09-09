from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    sender_account_id = Column(Integer, ForeignKey("accounts.id"), index=True, nullable=False)
    receiver_account_id = Column(Integer, ForeignKey("accounts.id"), index=True, nullable=False)
    amount = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    sender = relationship("Account", foreign_keys=[sender_account_id])
    receiver = relationship("Account", foreign_keys=[receiver_account_id])
