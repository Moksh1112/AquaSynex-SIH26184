import logging
from sqlalchemy.orm import Session
from typing import Optional
from app.crud.crud_audit import create_audit_log
from app.schemas.audit import AuditLogCreate

logger = logging.getLogger(__name__)

def log_audit_event(
    db: Session,
    action: str,
    resource: str,
    status: str,
    user_id: Optional[int] = None
) -> None:
    """
    Logs an audit event to the database.
    
    If writing the audit log fails, the exception is caught and logged to standard 
    output/logging rather than propagating. This ensures that an ordinary audit-record 
    failure does not corrupt the primary business response, as transactional audit 
    guarantees are not explicitly required by the current architecture.
    """
    try:
        audit_in = AuditLogCreate(
            user_id=user_id,
            action=action,
            resource=resource,
            status=status
        )
        create_audit_log(db, audit_in=audit_in)
    except Exception as e:
        # We do not raise the exception to prevent breaking the business logic flow.
        logger.error(f"Failed to write audit log: action={action}, resource={resource}, error={e}")
