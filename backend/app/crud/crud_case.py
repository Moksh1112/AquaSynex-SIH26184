from sqlalchemy.orm import Session
from app.models.complaint import Complaint

def get_cases(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Complaint).offset(skip).limit(limit).all()

def get_case_by_case_id(db: Session, case_id: str):
    return db.query(Complaint).filter(Complaint.case_id == case_id).first()
