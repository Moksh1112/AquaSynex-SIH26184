from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel, Field

from app.api import deps
from app.db.session import SessionLocal
from app.models.complaint import Complaint, ComplaintStatus
from app.models.user import User, RoleEnum
from app.schemas.prediction import PredictRequest
from app.services.prediction_service import generate_prediction
from app.ml.predictor import RealPredictor
from app.services.audit_service import log_audit_event

router = APIRouter()

class NCRPComplaintPayload(BaseModel):
    ncrp_id: str
    description: str
    account_number: str
    fraud_amount: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    category: str = "FINANCIAL_FRAUD"

def process_ncrp_complaint_bg(case_id: str):
    """
    Background task to process complaint and run prediction pipeline automatically.
    """
    db = SessionLocal()
    try:
        req = PredictRequest(case_id=case_id)
        predictor = RealPredictor()
        # Run proactive prediction
        generate_prediction(db, req, predictor)
    except Exception as e:
        print(f"Error in background prediction for {case_id}: {e}")
    finally:
        db.close()

@router.post("/ncrp/complaints", status_code=201)
def ingest_ncrp_complaint(
    payload: NCRPComplaintPayload,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    # Assuming NCRP service uses a special role or API key in real life.
    # We use ADMIN for the mock/demo.
    current_user: User = Depends(deps.require_role(RoleEnum.ADMIN.value))
):
    """
    Ingest a complaint from the external NCRP system.
    """
    # Check if exists
    existing = db.query(Complaint).filter(Complaint.case_id == payload.ncrp_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Complaint already exists")

    # Create Case
    new_complaint = Complaint(
        case_id=payload.ncrp_id,
        description=payload.description,
        account_id=payload.account_number,
        fraud_amount=payload.fraud_amount,
        reported_at=payload.timestamp,
        status=ComplaintStatus.OPEN,
        category=payload.category
    )
    db.add(new_complaint)
    db.commit()
    db.refresh(new_complaint)

    log_audit_event(db, action="INGEST_NCRP", resource=f"case:{payload.ncrp_id}", status="SUCCESS", user_id=current_user.id)

    # Trigger background prediction (Proactive pipeline)
    background_tasks.add_task(process_ncrp_complaint_bg, case_id=payload.ncrp_id)

    return {"status": "success", "case_id": payload.ncrp_id, "message": "Complaint ingested and prediction pipeline triggered"}
