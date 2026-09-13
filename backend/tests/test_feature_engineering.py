import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.models import Account, Transaction, Withdrawal, ATM, Complaint
from app.ml.feature_engineering import FeatureEngineer
from app.db.session import SessionLocal

# Re-use the real database but isolate via transactions or just query it
# since seed.py has populated it with C-2026-9081 data.
# We will use the main DB session to avoid maintaining a separate setup for tests,
# specifically querying the known seed data.

@pytest.fixture(scope="module")
def db_session():
    # Use the configured SessionLocal to connect to Postgres
    session = SessionLocal()
    yield session
    session.close()

def test_feature_engineering_determinism(db_session):
    """Verify that calling the feature generator twice yields identical features."""
    fe = FeatureEngineer(db_session)
    
    # Get the Mule2 account
    mule2 = db_session.query(Account).filter(Account.account_number == "M-555444333").first()
    assert mule2 is not None
    
    candidate_atm_id = "ATM-MUM-01"
    prediction_time = datetime.utcnow()
    
    features1 = fe.generate_features(mule2.id, candidate_atm_id, prediction_time)
    features2 = fe.generate_features(mule2.id, candidate_atm_id, prediction_time)
    
    assert features1.model_dump() == features2.model_dump()

def test_feature_engineering_no_leakage(db_session):
    """Verify that using a timestamp *before* any transactions yields zeros/Nones."""
    fe = FeatureEngineer(db_session)
    
    mule2 = db_session.query(Account).filter(Account.account_number == "M-555444333").first()
    
    # Pick a time 10 years ago
    past_time = datetime.utcnow() - timedelta(days=3650)
    
    features = fe.generate_features(mule2.id, "ATM-MUM-01", past_time)
    
    assert features.transaction_count == 0
    assert features.incoming_amount == 0.0
    assert features.upstream_account_count == 0
    assert features.historical_withdrawal_count == 0
    assert features.distance_to_last_withdrawal_meters is None
    assert features.time_since_last_withdrawal_hours is None

def test_c2026_9081_validation(db_session):
    """Verify features right before the actual withdrawal occurs in seed data."""
    fe = FeatureEngineer(db_session)
    
    mule2 = db_session.query(Account).filter(Account.account_number == "M-555444333").first()
    withdrawal = db_session.query(Withdrawal).filter(
        Withdrawal.account_id == mule2.id, 
        Withdrawal.atm_id == "ATM-MUM-01"
    ).first()
    
    assert withdrawal is not None
    
    # Time just BEFORE the withdrawal
    cutoff_time = withdrawal.timestamp - timedelta(seconds=1)
    
    features = fe.generate_features(mule2.id, "ATM-MUM-01", cutoff_time)
    
    # Check Transaction Features (Mule2 received 40,000 from Mule1 before this)
    assert features.transaction_count == 1
    assert features.incoming_amount == 40000.0
    
    # Graph features: M-555444333 has 1 direct upstream account (M-999888777)
    # The new logic counts single-hop direct incoming transfers.
    assert features.upstream_account_count == 1
    
    # At this point, the withdrawal hasn't happened yet!
    assert features.historical_withdrawal_count == 0
    assert features.total_withdrawn_amount == 0.0
    
    # Now check time exactly AT/AFTER the withdrawal
    after_time = withdrawal.timestamp + timedelta(seconds=1)
    features_after = fe.generate_features(mule2.id, "ATM-MUM-01", after_time)
    
    assert features_after.historical_withdrawal_count == 1
    assert features_after.total_withdrawn_amount == 40000.0
    assert features_after.previous_use_of_candidate_atm == 1
    # distance is 0 because last withdrawal was at ATM-MUM-01
    assert features_after.distance_to_last_withdrawal_meters == 0.0

def test_postgis_distance_calculation(db_session):
    """Test spatial logic against known seed ATMs (ATM-MUM-01 vs ATM-MUM-02)."""
    fe = FeatureEngineer(db_session)
    
    # Let's mock a scenario where the last withdrawal was at ATM-MUM-01 
    # but candidate is ATM-MUM-02
    
    mule2 = db_session.query(Account).filter(Account.account_number == "M-555444333").first()
    withdrawal = db_session.query(Withdrawal).filter(Withdrawal.account_id == mule2.id).first()
    
    # Use time after withdrawal
    after_time = withdrawal.timestamp + timedelta(seconds=1)
    
    features = fe.generate_features(mule2.id, "ATM-MUM-02", after_time)
    
    # ATM-MUM-01 (19.0760, 72.8777) to ATM-MUM-02 (19.0810, 72.8820)
    # Distance should be around 715 meters
    dist = features.distance_to_last_withdrawal_meters
    assert dist is not None
    assert 600 < dist < 800  # Allows for slight variation in spatial projection

def test_upstream_account_count_leakage(db_session):
    """
    Regression test explicitly proving future graph relationships are excluded.
    Scenario:
    A -> B at T-1
    C -> B at T+1
    Cutoff = T
    upstream_account_count for B MUST be 1.
    """
    from app.db.neo4j_session import get_neo4j_driver
    fe = FeatureEngineer(db_session)
    
    # 1. Create temporary accounts in Postgres
    acc_a = Account(account_number="TEST-A", bank_name="Bank A")
    acc_b = Account(account_number="TEST-B", bank_name="Bank B")
    acc_c = Account(account_number="TEST-C", bank_name="Bank C")
    db_session.add_all([acc_a, acc_b, acc_c])
    db_session.commit()
    
    cutoff_time = datetime.utcnow()
    t_minus = cutoff_time - timedelta(hours=1)
    t_plus = cutoff_time + timedelta(hours=1)
    
    driver = get_neo4j_driver()
    try:
        # 2. Setup Neo4j state directly for A -> B and C -> B
        with driver.session() as session:
            # Create nodes
            session.run("MERGE (a:Account {account_number: 'TEST-A'})")
            session.run("MERGE (b:Account {account_number: 'TEST-B'})")
            session.run("MERGE (c:Account {account_number: 'TEST-C'})")
            
            # Create past relationship (A -> B)
            session.run(
                """
                MATCH (a:Account {account_number: 'TEST-A'}), (b:Account {account_number: 'TEST-B'})
                MERGE (a)-[r:TRANSFERRED_TO {test: true, timestamp: $ts}]->(b)
                """, 
                {"ts": t_minus.isoformat()}
            )
            
            # Create future relationship (C -> B)
            session.run(
                """
                MATCH (c:Account {account_number: 'TEST-C'}), (b:Account {account_number: 'TEST-B'})
                MERGE (c)-[r:TRANSFERRED_TO {test: true, timestamp: $ts}]->(b)
                """, 
                {"ts": t_plus.isoformat()}
            )
            
        # 3. Test Feature Generation at Cutoff T
        features = fe.generate_features(acc_b.id, "ATM-TEST", cutoff_time)
        
        # Must only count A (since A was before cutoff, C was after)
        assert features.upstream_account_count == 1
        
    finally:
        # Cleanup Neo4j
        with driver.session() as session:
            session.run("MATCH (a:Account {account_number: 'TEST-A'}) DETACH DELETE a")
            session.run("MATCH (b:Account {account_number: 'TEST-B'}) DETACH DELETE b")
            session.run("MATCH (c:Account {account_number: 'TEST-C'}) DETACH DELETE c")
            
        # Cleanup Postgres
        db_session.delete(acc_a)
        db_session.delete(acc_b)
        db_session.delete(acc_c)
        db_session.commit()
