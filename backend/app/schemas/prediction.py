from pydantic import BaseModel
from typing import List

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
    predicted_time_window: str
    ranked_candidates: List[PredictionItem]
    explanations: List[str]
    reliability_statement: str
