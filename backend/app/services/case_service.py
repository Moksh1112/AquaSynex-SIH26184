from sqlalchemy.orm import Session
from app.crud import crud_case
from fastapi import HTTPException

def get_cases(db: Session, skip: int = 0, limit: int = 100):
    return crud_case.get_cases(db, skip=skip, limit=limit)

def get_case_details(db: Session, case_id: str):
    case = crud_case.get_case_by_case_id(db, case_id=case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case
