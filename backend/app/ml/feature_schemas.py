from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class CandidateATM(BaseModel):
    atm_id: str
    reasons: List[str]


class CandidateFeatures(BaseModel):
    # Identifiers (Not features)
    account_id: int
    candidate_atm_id: str
    prediction_timestamp: datetime
    
    # A. Transaction Features
    transaction_count: int
    incoming_amount: float
    outgoing_amount: float
    time_since_last_transfer_hours: Optional[float]
    
    # B. Graph Features (from Neo4j)
    upstream_account_count: int
    
    # C. Withdrawal Features
    historical_withdrawal_count: int
    total_withdrawn_amount: float
    previous_use_of_candidate_atm: int
    
    # D. Spatial Features
    distance_to_last_withdrawal_meters: Optional[float]
    
    # E. Temporal Features
    hour_of_day: int
    day_of_week: int
    time_since_last_withdrawal_hours: Optional[float]
