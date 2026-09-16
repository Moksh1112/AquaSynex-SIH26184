import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.session import SessionLocal
from app.models import Complaint, Account, Transaction, Withdrawal, ATM
from app.db.neo4j_sync import sync_to_neo4j

def generate_demo_case(db, case_id, desc, amount, acct_num, bank, mule1_acct, mule1_bank, mule2_acct, mule2_bank, atm_id, base_time):
    # Check if case exists
    if db.query(Complaint).filter(Complaint.case_id == case_id).first():
        print(f"Case {case_id} already exists.")
        return

    # Accounts
    v_acc = db.query(Account).filter(Account.account_number == acct_num).first()
    if not v_acc:
        v_acc = Account(account_number=acct_num, bank_name=bank, is_flagged=False)
        db.add(v_acc)

    m1_acc = db.query(Account).filter(Account.account_number == mule1_acct).first()
    if not m1_acc:
        m1_acc = Account(account_number=mule1_acct, bank_name=mule1_bank, is_flagged=True)
        db.add(m1_acc)

    m2_acc = db.query(Account).filter(Account.account_number == mule2_acct).first()
    if not m2_acc:
        m2_acc = Account(account_number=mule2_acct, bank_name=mule2_bank, is_flagged=True)
        db.add(m2_acc)

    db.flush()

    # Complaint
    complaint = Complaint(
        case_id=case_id,
        description=desc,
        status="OPEN",
        reported_at=base_time,
        account_id=acct_num,
        fraud_amount=amount,
        category="FINANCIAL_FRAUD"
    )
    db.add(complaint)
    db.flush()

    # Transactions
    t1 = Transaction(
        sender_account_id=v_acc.id,
        receiver_account_id=m1_acc.id,
        amount=amount,
        timestamp=base_time - timedelta(hours=3)
    )
    t2 = Transaction(
        sender_account_id=m1_acc.id,
        receiver_account_id=m2_acc.id,
        amount=amount - 500,
        timestamp=base_time - timedelta(hours=2)
    )
    db.add_all([t1, t2])
    db.flush()

    # Withdrawal
    w = Withdrawal(
        account_id=m2_acc.id,
        atm_id=atm_id,
        amount=amount - 500,
        timestamp=base_time - timedelta(hours=1),
        is_fraud=1,
        case_id=case_id
    )
    db.add(w)
    db.commit()
    print(f"Created {case_id} successfully.")

def seed_demo_cases():
    db = SessionLocal()
    try:
        base_time = datetime.utcnow()

        generate_demo_case(
            db, "C-2026-DEMO-001", "Phishing attack resulting in loss.",
            25000, "V-2001", "HDFC Bank", "M-2001A", "Axis Bank", "M-2001B", "SBI",
            "ATM-MUM-01", base_time - timedelta(days=1)
        )
        generate_demo_case(
            db, "C-2026-DEMO-002", "UPI fraud.",
            15000, "V-3001", "ICICI Bank", "M-3001A", "Bank of Baroda", "M-3001B", "SBI",
            "ATM-MUM-02", base_time - timedelta(days=2)
        )
        generate_demo_case(
            db, "C-2026-DEMO-003", "Credit card spoofing.",
            80000, "V-4001", "Kotak Bank", "M-4001A", "HDFC Bank", "M-4001B", "Axis Bank",
            "ATM-MUM-01", base_time - timedelta(days=3)
        )

        print("Syncing to Neo4j...")
        sync_to_neo4j(db)

    except Exception as e:
        db.rollback()
        print(f"Error seeding demo cases: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_cases()
