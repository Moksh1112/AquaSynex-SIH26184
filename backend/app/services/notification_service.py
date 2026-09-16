import os
import logging
from sqlalchemy.orm import Session
from app.models.alert import Alert

logger = logging.getLogger(__name__)

class NotificationAdapter:
    def send(self, alert: Alert, message: str) -> bool:
        raise NotImplementedError

class SandboxSMSAdapter(NotificationAdapter):
    def send(self, alert: Alert, message: str) -> bool:
        logger.info(f"[SANDBOX SMS] Alert {alert.id} -> SMS Sent: {message}")
        return True

class SandboxEmailAdapter(NotificationAdapter):
    def send(self, alert: Alert, message: str) -> bool:
        logger.info(f"[SANDBOX EMAIL] Alert {alert.id} -> Email Sent: {message}")
        return True

class SandboxBankAPIAdapter(NotificationAdapter):
    def send(self, db: Session, alert: Alert, message: str) -> bool:
        logger.info(f"[SANDBOX BANK API] Alert {alert.id} -> Request Sent: {message}")
        from app.services.audit_service import log_audit_event

        # Simulate lifecycle: PENDING -> BLOCKED
        log_audit_event(db, action="FUND_BLOCK_REQUEST", resource=f"alert:{alert.id}", status="PENDING", user_id=None)

        # In a real system, this would be an async callback from the bank. We simulate immediate success.
        logger.info(f"[SANDBOX BANK API] Alert {alert.id} -> Funds Blocked successfully.")
        log_audit_event(db, action="FUND_BLOCK_EXECUTE", resource=f"alert:{alert.id}", status="BLOCKED", user_id=None)

        return True

class NotificationService:
    def __init__(self):
        self.sms_adapter = SandboxSMSAdapter()
        self.email_adapter = SandboxEmailAdapter()
        self.bank_adapter = SandboxBankAPIAdapter()

    def dispatch_alert(self, db: Session, alert: Alert):
        """
        Dispatches alert notifications.
        """
        message = f"HIGH RISK ALERT: Case {alert.case_id}. Priority {alert.priority}."

        # In a real system, you'd look up configured stakeholders for this jurisdiction.
        # Here we mock the delivery based on alert priority.

        if alert.priority in ["P1", "P2"]:
            # Notify investigator via SMS/Email
            self.sms_adapter.send(alert, message)
            self.email_adapter.send(alert, message)

            # Notify Bank/FI
            self.bank_adapter.send(db, alert, f"Target ATM at risk for case {alert.case_id}")

notification_service = NotificationService()
