from sqlalchemy.orm import Session
from typing import List
from app.models.evidence import Evidence
from app.schemas.evidence import EvidenceCreate

from datetime import datetime

def get_evidence_by_case(db: Session, case_id: str) -> List[Evidence]:
    return db.query(Evidence).filter(Evidence.case_id == case_id).all()

def create_evidence(db: Session, evidence_in: EvidenceCreate) -> Evidence:
    db_evidence = Evidence(
        case_id=evidence_in.case_id,
        evidence_type=evidence_in.evidence_type,
        title=evidence_in.title,
        source=evidence_in.source,
        created_by=evidence_in.created_by,
        reference_path=evidence_in.reference_path,
        original_filename=evidence_in.original_filename,
        stored_filename=evidence_in.stored_filename,
        mime_type=evidence_in.mime_type,
        file_size=evidence_in.file_size,
        collected_at=evidence_in.collected_at or datetime.utcnow()
    )
    db.add(db_evidence)
    db.commit()
    db.refresh(db_evidence)



    return db_evidence
