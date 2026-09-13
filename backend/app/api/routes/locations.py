from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from app.api import deps
from app.models import ATM

router = APIRouter()

class ATMResponse(BaseModel):
    atm_id: str
    latitude: float
    longitude: float
    address: str

@router.get("/locations", response_model=List[ATMResponse])
def get_locations(db: Session = Depends(deps.get_db)):
    atms = db.query(ATM).all()
    return [{"atm_id": a.atm_id, "latitude": a.latitude, "longitude": a.longitude, "address": a.address} for a in atms]
