from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from app.api import deps
from app.models.atm import ATM
from app.models.prediction import Prediction, PredictionCandidate
from app.models.complaint import Complaint

router = APIRouter()

class ATMResponse(BaseModel):
    atm_id: str
    latitude: float
    longitude: float
    address: Optional[str] = None

@router.get("/locations", response_model=List[ATMResponse])
def get_locations(db: Session = Depends(deps.get_db)):
    atms = db.query(ATM).all()
    return [{"atm_id": a.atm_id, "latitude": a.latitude, "longitude": a.longitude, "address": a.address} for a in atms]

@router.get("/locations/heatmap")
def get_heatmap(
    crime_category: Optional[str] = Query(None, description="Filter by crime category"),
    start_time: Optional[datetime] = Query(None, description="Start time for filtering predictions"),
    end_time: Optional[datetime] = Query(None, description="End time for filtering predictions"),
    latitude: Optional[float] = Query(None, description="Center latitude for radius filter"),
    longitude: Optional[float] = Query(None, description="Center longitude for radius filter"),
    radius_km: Optional[float] = Query(None, description="Radius in kilometers"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level (HIGH, MEDIUM, LOW)"),
    db: Session = Depends(deps.get_db)
):
    """
    Returns high-risk predictions joined with ATM locations to form a heatmap,
    dynamically filtered by the provided parameters. Includes H3 indexing.
    """
    # Start the base query
    query = db.query(Prediction, PredictionCandidate, ATM, Complaint).join(
        PredictionCandidate, Prediction.id == PredictionCandidate.prediction_id
    ).join(
        ATM, PredictionCandidate.atm_id == ATM.atm_id
    ).join(
        Complaint, Prediction.case_id == Complaint.case_id
    )

    # 1. Crime Category Filter
    if crime_category:
        query = query.filter(Complaint.category == crime_category)

    # 2. Time Filter
    if start_time:
        query = query.filter(Prediction.created_at >= start_time)
    if end_time:
        query = query.filter(Prediction.created_at <= end_time)

    # 3. Location/Radius Filter (PostGIS)
    if latitude is not None and longitude is not None and radius_km is not None:
        target_point = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)
        # Using ST_DWithin for PostGIS geography
        query = query.filter(
            func.ST_DWithin(ATM.location, target_point, radius_km * 1000)
        )

    # 4. Risk Level Filter
    if risk_level:
        query = query.filter(Prediction.risk_level == risk_level)
    else:
        # Default behavior: medium/high risk
        query = query.filter(PredictionCandidate.probability > 0.5)

    results = query.all()

    try:
        import h3
    except ImportError:
        h3 = None

    heatmap_data = []
    for pred, cand, atm, comp in results:
        h3_index = None
        if h3:
            try:
                # Resolution 8 is typically good for neighborhood level
                h3_index = h3.latlng_to_cell(atm.latitude, atm.longitude, 8)
            except AttributeError:
                # Fallback for older h3 library versions
                h3_index = h3.geo_to_h3(atm.latitude, atm.longitude, 8)

        heatmap_data.append({
            "lat": atm.latitude,
            "lng": atm.longitude,
            "weight": cand.probability,
            "case_id": pred.case_id,
            "atm_id": atm.atm_id,
            "crime_category": comp.category,
            "risk_level": pred.risk_level,
            "h3_index": h3_index
        })

    return heatmap_data
