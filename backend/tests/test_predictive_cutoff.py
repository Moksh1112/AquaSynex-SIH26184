import pytest
from datetime import datetime, timedelta
from app.db.session import SessionLocal
from app.models import Account, Transaction, Withdrawal, ATM, Complaint
from app.ml.feature_engineering import FeatureEngineer
from app.db.seed_predictive_scenario import seed_future_transactions

def test_predictive_cutoff_prevents_data_leakage():
    db = SessionLocal()
    case_id = "C-TEST-CUTOFF"
    try:
        # 1. Create complaint (simulating frontend New Intake)
        now = datetime.utcnow()
        complaint = db.query(Complaint).filter(Complaint.case_id == case_id).first()
        if not complaint:
            complaint = Complaint(
                case_id=case_id,
                description="Test cutoff scenario",
                status="OPEN",
                reported_at=now,
                account_id="V-5001"
            )
            db.add(complaint)
            db.commit()
            
        # 2. Run developer utility to inject future T1, T2, T3 relative to T0
        seed_future_transactions(case_id)
        
        # Reload complaint to get precise T0
        db.expire_all()
        complaint = db.query(Complaint).filter(Complaint.case_id == case_id).first()
        t0_time = complaint.reported_at
        
        v_acc = db.query(Account).filter(Account.account_number == "V-5001").first()
        assert v_acc is not None
        m1_acc = db.query(Account).filter(Account.account_number == "M-5001A").first()
        m2_acc = db.query(Account).filter(Account.account_number == "M-5001B").first()
        
        # 3. Verify T0 < T1 invariant
        t1 = db.query(Transaction).filter(
            Transaction.sender_account_id == v_acc.id,
            Transaction.receiver_account_id == m1_acc.id
        ).first()
        assert t1 is not None
        assert t1.timestamp == t0_time + timedelta(hours=1)
        
        # 4. Verify FeatureEngineer completely excludes T1, T2, T3 when cutoff = T0
        fe = FeatureEngineer(db)
        feats = fe.generate_features(account_id=v_acc.id, candidate_atm_id="ATM-MUM-02", prediction_timestamp=t0_time)
        
        # The ML model must see exactly 0 past transactions, as T1/T2/T3 are strictly > T0
        assert feats.outgoing_amount == 0.0
        assert feats.transaction_count == 0
        
        # 5. IDEMPOTENCY TEST
        # Run seeder again with exact same T0
        seed_future_transactions(case_id)
        
        # Assert exact number of scenario transactions (2) and withdrawals (1)
        # We only count the logical edges specific to this scenario to ensure no duplicates were made
        v_to_m1_count = db.query(Transaction).filter(
            Transaction.sender_account_id == v_acc.id,
            Transaction.receiver_account_id == m1_acc.id
        ).count()
        assert v_to_m1_count == 1
        
        m1_to_m2_count = db.query(Transaction).filter(
            Transaction.sender_account_id == m1_acc.id,
            Transaction.receiver_account_id == m2_acc.id
        ).count()
        assert m1_to_m2_count == 1
        
        m2_wd_count = db.query(Withdrawal).filter(
            Withdrawal.account_id == m2_acc.id,
            Withdrawal.atm_id == "ATM-MUM-02"
        ).count()
        assert m2_wd_count == 1
        
        # 6. IDEMPOTENCY TEST: TIMESTAMP ANCHOR SHIFT
        # Shift T0 by 5 minutes to simulate recreating the complaint later
        new_t0 = t0_time + timedelta(minutes=5)
        complaint.reported_at = new_t0
        db.commit()
        
        # Run seeder again
        seed_future_transactions(case_id)
        
        # Assert there are still exactly 2 scenario transactions and 1 withdrawal (no duplicates)
        assert db.query(Transaction).filter(
            Transaction.sender_account_id == v_acc.id,
            Transaction.receiver_account_id == m1_acc.id
        ).count() == 1
        assert db.query(Transaction).filter(
            Transaction.sender_account_id == m1_acc.id,
            Transaction.receiver_account_id == m2_acc.id
        ).count() == 1
        assert db.query(Withdrawal).filter(
            Withdrawal.account_id == m2_acc.id,
            Withdrawal.atm_id == "ATM-MUM-02"
        ).count() == 1
        
        # Assert timestamps were realigned to the new T0
        t1_realigned = db.query(Transaction).filter(
            Transaction.sender_account_id == v_acc.id,
            Transaction.receiver_account_id == m1_acc.id
        ).first()
        assert t1_realigned.timestamp == new_t0 + timedelta(hours=1)
        
    finally:
        # Cleanup test data to maintain idempotency
        c = db.query(Complaint).filter(Complaint.case_id == case_id).first()
        if c:
            db.delete(c)
            db.commit()
        db.close()
