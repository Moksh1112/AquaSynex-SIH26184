from pydantic import BaseModel

class ComplaintBase(BaseModel):
    case_id: str
    fraud_amount: float
