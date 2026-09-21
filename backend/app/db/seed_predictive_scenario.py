import os
import sys
import argparse
from datetime import timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.session import SessionLocal
from app.models import Account, Transaction, Withdrawal, ATM, Complaint

def seed_future_transactions(case_id: str):
    db = SessionLocal()
    try:
        complaint = db.query(Complaint).filter(Complaint.case_id == case_id).first()
        if not complaint:
            print(f"Error: Complaint with case_id {case_id} not found.")
            print("Please create the complaint via the New Intake UI first.")
            return

        t0_time = complaint.reported_at
        print(f"Found Complaint {case_id}. T0 (reported_at) = {t0_time}")
        
        # Ensure base accounts and ATM exist
        atm = db.query(ATM).filter(ATM.atm_id == "ATM-MUM-02").first()
        if not atm:
            atm = ATM(atm_id="ATM-MUM-02", latitude=19.0810, longitude=72.8820, address="Sakinaka, Mumbai", location="SRID=4326;POINT(72.8820 19.0810)")
            db.add(atm)
            db.flush()
            
        v_acc = db.query(Account).filter(Account.account_number == "V-5001").first()
        if not v_acc:
            v_acc = Account(account_number="V-5001", bank_name="Axis Bank", is_flagged=False)
            db.add(v_acc)
            
        m1_acc = db.query(Account).filter(Account.account_number == "M-5001A").first()
        if not m1_acc:
            m1_acc = Account(account_number="M-5001A", bank_name="HDFC Bank", is_flagged=True)
            db.add(m1_acc)
            
        m2_acc = db.query(Account).filter(Account.account_number == "M-5001B").first()
        if not m2_acc:
            m2_acc = Account(account_number="M-5001B", bank_name="State Bank of India", is_flagged=True)
            db.add(m2_acc)
            
        db.commit()
        
        # Create Transactions in the future relative to T0
        t1_time = t0_time + timedelta(hours=1)
        t2_time = t0_time + timedelta(hours=2)
        t3_time = t0_time + timedelta(hours=3)
        
        # Check if they exist to make it idempotent based on logical relationship
        t1 = db.query(Transaction).filter(
            Transaction.sender_account_id == v_acc.id,
            Transaction.receiver_account_id == m1_acc.id
        ).first()
        if not t1:
            t1 = Transaction(
                sender_account_id=v_acc.id,
                receiver_account_id=m1_acc.id,
                amount=60000.0,
                timestamp=t1_time
            )
            db.add(t1)
        else:
            t1.timestamp = t1_time
            
        t2 = db.query(Transaction).filter(
            Transaction.sender_account_id == m1_acc.id,
            Transaction.receiver_account_id == m2_acc.id
        ).first()
        if not t2:
            t2 = Transaction(
                sender_account_id=m1_acc.id,
                receiver_account_id=m2_acc.id,
                amount=58500.0,
                timestamp=t2_time
            )
            db.add(t2)
        else:
            t2.timestamp = t2_time
            
        w1 = db.query(Withdrawal).filter(
            Withdrawal.account_id == m2_acc.id,
            Withdrawal.atm_id == "ATM-MUM-02"
        ).first()
        if not w1:
            w1 = Withdrawal(
                account_id=m2_acc.id,
                atm_id="ATM-MUM-02",
                amount=58500.0,
                timestamp=t3_time
            )
            db.add(w1)
        else:
            w1.timestamp = t3_time
            
        db.commit()
        
        from app.db.neo4j_session import init_neo4j
        from app.db.neo4j_sync import sync_to_neo4j
        print("Syncing new data to Neo4j...")
        init_neo4j()
        sync_to_neo4j(db)
        print("Neo4j synced.")
        
        print(f"Predictive scenario transactions seeded successfully!")
        print(f"T0 (Complaint Time) = {t0_time}")
        print(f"T1 = {t1_time}")
        print(f"T2 = {t2_time}")
        print(f"T3 = {t3_time}")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding predictive scenario: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inject future cash-out transactions for a case.")
    parser.add_argument("--case-id", required=True, help="The case ID to attach future transactions to (e.g. C-2026-9082)")
    args = parser.parse_args()
    seed_future_transactions(args.case_id)
