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

def seed_db():
    db = SessionLocal()
    try:
        print("Starting synthetic seed generation...")

        # 1. Clear existing data (if using sqlite during testing)
        # Note: In a real db with constraints, you'd delete in reverse order of dependencies.
        # This simple script assumes a fresh DB or handles collisions by checking existence.
        if db.query(Complaint).first():
            print("Database already seeded. Skipping Postgres seed...")

            # Sync to Neo4j anyway
            from app.db.neo4j_session import init_neo4j
            from app.db.neo4j_sync import sync_to_neo4j
            print("Initializing Neo4j constraints...")
            init_neo4j()
            print("Synchronizing data to Neo4j...")
            sync_to_neo4j(db)
            print("Neo4j graph populated!")
            return

        # 2. Users
        analyst = User(username="analyst_smith", email="smith@i4c.gov.in", hashed_password="hashed_pw_here", role="I4C_ANALYST")
        db.add(analyst)
        db.flush()

        # 3. Complaint (The Case)
        complaint = Complaint(
            case_id="C-2026-9081",
            description="Victim reported unauthorized transfer of ₹45,000 from their primary account.",
            status="OPEN",
            reported_at=datetime.utcnow() - timedelta(hours=5),
            account_id="V-100200300"
        )
        db.add(complaint)
        db.flush()

        # 4. Accounts (Victim + Mule 1 + Mule 2)
        victim_acc = Account(account_number="V-100200300", bank_name="State Bank of India", is_flagged=False)
        mule1_acc = Account(account_number="M-999888777", bank_name="HDFC Bank", is_flagged=True)
        mule2_acc = Account(account_number="M-555444333", bank_name="ICICI Bank", is_flagged=True)

        db.add_all([victim_acc, mule1_acc, mule2_acc])
        db.flush()

        # 5. Transactions (The Money Movement)
        # Victim -> Mule 1 (₹45,000)
        t1 = Transaction(
            sender_account_id=victim_acc.id,
            receiver_account_id=mule1_acc.id,
            amount=45000.0,
            timestamp=complaint.reported_at - timedelta(hours=2)
        )
        # Mule 1 -> Mule 2 (₹40,000)
        t2 = Transaction(
            sender_account_id=mule1_acc.id,
            receiver_account_id=mule2_acc.id,
            amount=40000.0,
            timestamp=complaint.reported_at - timedelta(hours=1, minutes=30)
        )
        db.add_all([t1, t2])
        db.flush()

        # 6. ATMs (Cash-out locations)
        atm1 = ATM(atm_id="ATM-MUM-01", latitude=19.0760, longitude=72.8777, address="Andheri East, Mumbai")
        atm2 = ATM(atm_id="ATM-MUM-02", latitude=19.0810, longitude=72.8820, address="Sakinaka, Mumbai")
        db.add_all([atm1, atm2])
        db.flush()

        # 7. Prediction & Candidates
        prediction = Prediction(
            case_id=complaint.case_id,
            risk_level="HIGH",
            time_window="18:00-20:00",
            explanation={"reasons": ["High velocity transfer", "Known mule network"]}
        )
        db.add(prediction)
        db.flush()

        cand1 = PredictionCandidate(prediction_id=prediction.id, atm_id=atm1.atm_id, rank=1, probability=0.88, risk="CRITICAL")
        cand2 = PredictionCandidate(prediction_id=prediction.id, atm_id=atm2.atm_id, rank=2, probability=0.65, risk="HIGH")
        db.add_all([cand1, cand2])
        db.flush()

        # 8. Alert
        alert = Alert(
            case_id=complaint.case_id,
            prediction_id=prediction.id,
            priority="HIGH",
            status="OPEN"
        )
        db.add(alert)
        db.flush()

        # 9. Eventual Withdrawal (Cash-out hits ATM-MUM-01)
        withdrawal = Withdrawal(
            account_id=mule2_acc.id,
            atm_id=atm1.atm_id,
            amount=40000.0,
            timestamp=complaint.reported_at - timedelta(minutes=45)
        )
        db.add(withdrawal)

        # Commit all synthetic records
        db.commit()
        print("Seed data successfully injected!")

        # 10. Sync to Neo4j
        from app.db.neo4j_session import init_neo4j
        from app.db.neo4j_sync import sync_to_neo4j

        print("Initializing Neo4j constraints...")
        init_neo4j()

        print("Synchronizing data to Neo4j...")
        sync_to_neo4j(db)
        print("Neo4j graph populated!")

        from app.models.police_station import PoliceStation

        print("Creating Police Stations...")
        stations = [
            PoliceStation(station_id="PS-MUM-ANDHERI-EAST",
                          station_name="Andheri East Police Station",
                          latitude=19.0832, longitude=72.8710,
                          jurisdiction_code="MH_MUMBAI",
                          address="Andheri East, Mumbai, Maharashtra"),
            PoliceStation(station_id="PS-MUM-SAKINAKA",
                          station_name="Sakinaka Police Station",
                          latitude=19.0867, longitude=72.8870,
                          jurisdiction_code="MH_MUMBAI",
                          address="Sakinaka, Mumbai, Maharashtra"),
            PoliceStation(station_id="PS-MUM-POWAI",
                          station_name="Powai Police Station",
                          latitude=19.1189, longitude=72.9050,
                          jurisdiction_code="MH_MUMBAI",
                          address="Powai, Mumbai, Maharashtra"),
        ]
        db.add_all(stations)
        db.commit()

        print("Seeding completed successfully.")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
