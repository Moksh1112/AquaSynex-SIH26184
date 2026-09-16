from pydantic import BaseModel
from typing import List, Optional

class PredictRequest(BaseModel):
    case_id: str

class PredictionItem(BaseModel):
    rank: int
    atm_id: str
    probability: float
    latitude: float
    longitude: float
    risk: str

class PredictResponse(BaseModel):
    case_id: str
    risk: str
    time_window: str
    predictions: List[PredictionItem]
    explanation: List[str]

# ---------------------------------------------------------------------------
# Response Intelligence schemas (ADDITIVE — PredictResponse is unchanged)
# ---------------------------------------------------------------------------

class ResponseIntelligence(BaseModel):
    """Enrichment block attached to each predicted candidate."""
    nearest_station_id: Optional[str] = None
    nearest_station_name: Optional[str] = None
    station_latitude: Optional[float] = None
    station_longitude: Optional[float] = None
    distance_km: Optional[float] = None
    jurisdiction: Optional[str] = None
    recommended_action: str = "Response unit unavailable."

class EnrichedPredictionItem(BaseModel):
    """PredictionItem extended with a ResponseIntelligence block."""
    rank: int
    atm_id: str
    probability: float
    latitude: float
    longitude: float
    risk: str
    response: ResponseIntelligence

class EnrichedPredictResponse(BaseModel):
    """
    Returned by GET /predict/{case_id}/response-intelligence.
    Preserves all fields of PredictResponse and replaces predictions list
    with EnrichedPredictionItem entries.
    """
    case_id: str
    risk: str
    time_window: str
    predictions: List[EnrichedPredictionItem]
    explanation: List[str]
