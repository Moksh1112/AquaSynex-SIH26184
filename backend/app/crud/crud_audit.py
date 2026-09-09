from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from app.schemas.audit import AuditLogCreate

def create_audit_log(db: Session, audit_in: AuditLogCreate) -> AuditLog:
    db_obj = AuditLog(
        user_id=audit_in.user_id,
        action=audit_in.action,
        resource=audit_in.resource,
        status=audit_in.status
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_audit_logs(db: Session, skip: int = 0, limit: int = 100):
    return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
