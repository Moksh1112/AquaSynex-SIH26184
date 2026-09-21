import os
import sys
from datetime import datetime, timedelta

# Ensure backend directory is in the path for direct execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.session import SessionLocal
from app.models import (
    User, Complaint, Account, Transaction, Withdrawal, ATM,
    Prediction, PredictionCandidate, Alert, AuditLog
)

def seed_demo_801():
    db = SessionLocal()
    try:
        print("Starting DEMO-2026-801 seed generation...")
        
        # Check if already seeded
        existing = db.query(Complaint).filter(Complaint.case_id == "DEMO-2026-801").first()
        if existing:
            print("DEMO-2026-801 already exists. Idempotent exit.")
            return

        t0_time = datetime.utcnow() - timedelta(hours=24) # Complaint time

        # 1. Accounts
        victim_acc = db.query(Account).filter(Account.account_number == "V-DEMO-801").first()
        if not victim_acc:
            victim_acc = Account(account_number="V-DEMO-801", bank_name="State Bank of India", is_flagged=False)
            db.add(victim_acc)
            
        mule1_acc = db.query(Account).filter(Account.account_number == "M-DEMO-801A").first()
        if not mule1_acc:
            mule1_acc = Account(account_number="M-DEMO-801A", bank_name="HDFC Bank", is_flagged=True)
            db.add(mule1_acc)
            
        mule2_acc = db.query(Account).filter(Account.account_number == "M-DEMO-801B").first()
        if not mule2_acc:
            mule2_acc = Account(account_number="M-DEMO-801B", bank_name="ICICI Bank", is_flagged=True)
            db.add(mule2_acc)
            
        db.flush()

        # 2. Complaint
        complaint = Complaint(
            case_id="DEMO-2026-801",
            description="Victim reported multiple unauthorized transfers totaling ₹150,000.",
            status="OPEN",
            reported_at=t0_time,
            account_id=victim_acc.account_number
        )
        db.add(complaint)
        db.flush()

        # 3. ATMs
        atms_data = [
            # HIGH Candidates (High fraud history, isolated)
            ("ATM-SYN-881a", 19.3500, 72.9500, "Navi Mumbai Expressway - Kiosk 1"),
            ("ATM-SYN-881b", 19.3520, 72.9520, "Navi Mumbai Expressway - Kiosk 2"),
            # MEDIUM Candidate (Moderate fraud, moderate distance)
            ("ATM-SYN-882m", 19.3400, 72.9400, "Vashi Sector 17 Main Road"),
            # LOW Candidates (No fraud, dense)
            ("ATM-SYN-883x", 19.3300, 72.9300, "Vashi Railway Station North"),
            ("ATM-SYN-883y", 19.3320, 72.9320, "Vashi Railway Station South")
        ]
        
        # Add decoy ATMs to increase density for M1, L1, L2
        for i in range(3):
            atms_data.append((f"ATM-SYN-882d{i}", 19.3400 + (i*0.0001), 72.9400 + (i*0.0001), f"Vashi Sector 17 Branch {i+1}"))
        for i in range(8):
            atms_data.append((f"ATM-SYN-883d{i}", 19.3300 + (i*0.0001), 72.9300 + (i*0.0001), f"Vashi Station Plaza {i+1}"))
        
        atm_objs = []
        for atm_id, lat, lon, addr in atms_data:
            atm = db.query(ATM).filter(ATM.atm_id == atm_id).first()
            if not atm:
                atm = ATM(
                    atm_id=atm_id, 
                    latitude=lat, 
                    longitude=lon, 
                    address=addr,
                    location=f"SRID=4326;POINT({lon} {lat})"
                )
                db.add(atm)
            atm_objs.append(atm)
        db.flush()

        # 4. Transactions (Before T0)
        # Add an inbound transaction so maximum_transaction_amount is > 0 (model likes this)
        txs = []
        rand_sender = db.query(Account).filter(Account.account_number == "R-RAND-SENDER").first()
        if not rand_sender:
            rand_sender = Account(account_number="R-RAND-SENDER", bank_name="Unknown", is_flagged=False)
            db.add(rand_sender)
            db.flush()
        txs.append(Transaction(sender_account_id=rand_sender.id, receiver_account_id=victim_acc.id, amount=200000.0, timestamp=t0_time - timedelta(days=2)))
        
        # High velocity transfers
        # Victim -> Mule 1
        txs.append(Transaction(sender_account_id=victim_acc.id, receiver_account_id=mule1_acc.id, amount=75000.0, timestamp=t0_time - timedelta(hours=5)))
        txs.append(Transaction(sender_account_id=victim_acc.id, receiver_account_id=mule1_acc.id, amount=75000.0, timestamp=t0_time - timedelta(hours=4)))
        txs.append(Transaction(sender_account_id=victim_acc.id, receiver_account_id=mule1_acc.id, amount=50000.0, timestamp=t0_time - timedelta(hours=3, minutes=30)))
        txs.append(Transaction(sender_account_id=victim_acc.id, receiver_account_id=mule1_acc.id, amount=50000.0, timestamp=t0_time - timedelta(hours=3, minutes=15)))
        txs.append(Transaction(sender_account_id=victim_acc.id, receiver_account_id=mule1_acc.id, amount=50000.0, timestamp=t0_time - timedelta(hours=3)))
        
        # Mule 1 -> Mule 2
        txs.append(Transaction(sender_account_id=mule1_acc.id, receiver_account_id=mule2_acc.id, amount=140000.0, timestamp=t0_time - timedelta(hours=2)))
        db.add_all(txs)
        db.flush()

        # 5. Historical Withdrawals (To manipulate ATM fraud rates natively)
        # H1 & H2 will get a lot of recent fraud withdrawals from other accounts
        wds = []
        
        # Create some random other accounts for historical global fraud
        rand_acc = db.query(Account).filter(Account.account_number == "R-RAND-1").first()
        if not rand_acc:
            rand_acc = Account(account_number="R-RAND-1", bank_name="Unknown", is_flagged=True)
            db.add(rand_acc)
            db.flush()

        # Give H1 10 fraud withdrawals
        for i in range(10):
            wds.append(Withdrawal(account_id=rand_acc.id, atm_id="ATM-SYN-881a", amount=10000.0, timestamp=t0_time - timedelta(days=2, hours=i), is_fraud=1))
        
        # Give H2 8 fraud withdrawals
        for i in range(8):
            wds.append(Withdrawal(account_id=rand_acc.id, atm_id="ATM-SYN-881b", amount=10000.0, timestamp=t0_time - timedelta(days=3, hours=i), is_fraud=1))
            
        # Give M1 2 fraud withdrawals, 3 legit
        for i in range(2):
            wds.append(Withdrawal(account_id=rand_acc.id, atm_id="ATM-SYN-882m", amount=5000.0, timestamp=t0_time - timedelta(days=5, hours=i), is_fraud=1))
        for i in range(3):
            wds.append(Withdrawal(account_id=rand_acc.id, atm_id="ATM-SYN-882m", amount=5000.0, timestamp=t0_time - timedelta(days=6, hours=i), is_fraud=0))

        # L1 and L2 get NO historical withdrawals (or 0 fraud)

        # Make the mules withdraw at H1 and H2 recently (Before T0!) to build spatial proximity
        # Set timestamp to just 1 hour ago so atm_days_since_last_activity is very small but > 0
        wds.append(Withdrawal(account_id=mule1_acc.id, atm_id="ATM-SYN-881a", amount=10000.0, timestamp=t0_time - timedelta(hours=1), is_fraud=1, case_id="DEMO-2026-801"))
        wds.append(Withdrawal(account_id=mule2_acc.id, atm_id="ATM-SYN-881b", amount=15000.0, timestamp=t0_time - timedelta(minutes=30), is_fraud=1, case_id="DEMO-2026-801"))
        wds.append(Withdrawal(account_id=mule1_acc.id, atm_id="ATM-SYN-881a", amount=10000.0, timestamp=t0_time - timedelta(hours=2), is_fraud=1, case_id="DEMO-2026-801"))
        wds.append(Withdrawal(account_id=mule2_acc.id, atm_id="ATM-SYN-881b", amount=15000.0, timestamp=t0_time - timedelta(hours=1, minutes=30), is_fraud=1, case_id="DEMO-2026-801"))

        # Past legitimate withdrawal for the suspect account near H1 to establish distance_from_previous_withdrawal
        wds.append(Withdrawal(account_id=victim_acc.id, atm_id="ATM-SYN-881a", amount=1000.0, timestamp=t0_time - timedelta(days=10), is_fraud=0))

        db.add_all(wds)
        db.commit()

        print("DEMO-2026-801 seeded successfully!")

        # Sync to Neo4j
        from app.db.neo4j_session import init_neo4j
        from app.db.neo4j_sync import sync_to_neo4j
        
        print("Syncing new demo data to Neo4j...")
        init_neo4j()
        sync_to_neo4j(db)
        print("Neo4j synced.")

    except Exception as e:
        db.rollback()
        print(f"Error seeding DEMO-2026-801: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_801()
