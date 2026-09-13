from app.models import (
    User, Complaint, Account, Transaction, Withdrawal,
    ATM, H3Cell, Prediction, PredictionCandidate, Alert, AuditLog
)
from app.db.base import Base

def test_models_importable():
    # If this test runs, it means all models were successfully imported
    # and their declarative mappings were successfully processed by SQLAlchemy.
    assert User.__tablename__ == "users"
    assert Complaint.__tablename__ == "complaints"
    assert Account.__tablename__ == "accounts"
    assert Transaction.__tablename__ == "transactions"
    assert Withdrawal.__tablename__ == "withdrawals"
    assert ATM.__tablename__ == "atms"
    assert H3Cell.__tablename__ == "h3_cells"
    assert Prediction.__tablename__ == "predictions"
    assert Alert.__tablename__ == "alerts"
    assert AuditLog.__tablename__ == "audit_logs"

def test_metadata_contains_all_tables():
    tables = Base.metadata.tables.keys()
    assert "users" in tables
    assert "complaints" in tables
    assert "accounts" in tables
    assert "transactions" in tables
    assert "withdrawals" in tables
    assert "atms" in tables
    assert "h3_cells" in tables
    assert "predictions" in tables
    assert "alerts" in tables
    assert "audit_logs" in tables
