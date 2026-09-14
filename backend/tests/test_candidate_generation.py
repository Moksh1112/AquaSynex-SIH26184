import pytest
from datetime import datetime, timedelta
from app.db.session import SessionLocal
from app.models import Account, Withdrawal, ATM, Transaction
from app.ml.candidate_generation import CandidateGenerator

@pytest.fixture(scope="module")
def db_session():
    session = SessionLocal()
    yield session
    session.close()

def test_c2026_9081_inclusion(db_session):
    """
    Test the C-2026-9081 cold-start fallback scenario.
    Mule2 has no prior history. It should fallback and include ATM-MUM-01.
    """
    mule2 = db_session.query(Account).filter(Account.account_number == "M-555444333").first()
    assert mule2 is not None

    cg = CandidateGenerator(db_session, max_candidates=10)
    
    # We find the actual withdrawal time
    withdrawal = db_session.query(Withdrawal).filter(
        Withdrawal.account_id == mule2.id,
        Withdrawal.atm_id == "ATM-MUM-01"
    ).first()
    
    # Time just before withdrawal
    cutoff_time = withdrawal.timestamp - timedelta(seconds=1)
    
    candidates = cg.generate_candidates(mule2.id, cutoff_time)
    
    # It should fallback and pull ATM-MUM-01
    atm_ids = [c.atm_id for c in candidates]
    assert "ATM-MUM-01" in atm_ids
    
    # Reason should contain Fallback
    cand_obj = next((c for c in candidates if c.atm_id == "ATM-MUM-01"), None)
    assert any("Fallback" in r for r in cand_obj.reasons)

def test_candidate_leakage(db_session):
    """
    Explicitly ensure a future withdrawal does NOT show up as 'Historical'.
    """
    mule2 = db_session.query(Account).filter(Account.account_number == "M-555444333").first()
    cg = CandidateGenerator(db_session)
    
    withdrawal = db_session.query(Withdrawal).filter(
        Withdrawal.account_id == mule2.id,
        Withdrawal.atm_id == "ATM-MUM-01"
    ).first()
    
    # Time just before withdrawal
    cutoff_time = withdrawal.timestamp - timedelta(seconds=1)
    candidates = cg.generate_candidates(mule2.id, cutoff_time)
    
    cand_obj = next((c for c in candidates if c.atm_id == "ATM-MUM-01"), None)
    # Even if it's found via fallback, it MUST NOT be found via "Historical"
    if cand_obj:
        assert "Historical" not in cand_obj.reasons

    # Now time AFTER withdrawal
    after_time = withdrawal.timestamp + timedelta(seconds=1)
    candidates_after = cg.generate_candidates(mule2.id, after_time)
    cand_obj_after = next((c for c in candidates_after if c.atm_id == "ATM-MUM-01"), None)
    
    assert cand_obj_after is not None
    assert "Historical" in cand_obj_after.reasons

def test_candidate_syndicate_and_spatial(db_session):
    """
    Test syndicate relationships in Neo4j and spatial fallbacks using temporary data.
    """
    from app.db.neo4j_session import get_neo4j_driver
    driver = get_neo4j_driver()

    cg = CandidateGenerator(db_session)
    
    import uuid
    uid = uuid.uuid4().hex[:8]
    test_x = f"TEST-X-{uid}"
    test_y = f"TEST-Y-{uid}"
    atm_syn_id = f"ATM-SYN-{uid}"
    atm_spa_id = f"ATM-SPA-{uid}"

    # 1. Setup Postgres
    acc_x = Account(account_number=test_x, bank_name="Bank X", is_flagged=True)
    acc_y = Account(account_number=test_y, bank_name="Bank Y", is_flagged=True)
    
    atm_syn = ATM(atm_id=atm_syn_id, latitude=19.1000, longitude=72.9000, address="Syndicate ATM")
    atm_spa = ATM(atm_id=atm_spa_id, latitude=19.1010, longitude=72.9010, address="Spatial ATM") # approx 140m away
    
    db_session.add_all([acc_x, acc_y, atm_syn, atm_spa])
    db_session.commit()
    
    t_minus = datetime.utcnow() - timedelta(hours=2)
    cutoff_time = datetime.utcnow()
    
    w_x = Withdrawal(account_id=acc_x.id, atm_id=atm_syn_id, amount=100, timestamp=t_minus)
    db_session.add(w_x)
    db_session.commit()
    
    # 2. Setup Neo4j
    try:
        with driver.session() as session:
            session.run("MERGE (x:Account {account_number: $x})", {"x": test_x})
            session.run("MERGE (y:Account {account_number: $y})", {"y": test_y})
            session.run("MERGE (w:Withdrawal {withdrawal_id: $w_id}) SET w.timestamp=$ts", {"w_id": w_x.id, "ts": t_minus.isoformat()})
            session.run("MERGE (atm:ATM {atm_id: $atm_id})", {"atm_id": atm_syn_id})
            
            # X transferred to Y
            session.run(
                "MATCH (x:Account {account_number: $x}), (y:Account {account_number: $y}) "
                "MERGE (x)-[:TRANSFERRED_TO {timestamp: $ts}]->(y)", 
                {"x": test_x, "y": test_y, "ts": t_minus.isoformat()}
            )
            # X withdrew at ATM-SYN
            session.run(
                "MATCH (x:Account {account_number: $x}), (w:Withdrawal {withdrawal_id: $w_id}) "
                "MERGE (x)-[:MADE_WITHDRAWAL]->(w)",
                {"x": test_x, "w_id": w_x.id}
            )
            session.run(
                "MATCH (w:Withdrawal {withdrawal_id: $w_id}), (atm:ATM {atm_id: $atm_id}) "
                "MERGE (w)-[:AT_ATM]->(atm)",
                {"w_id": w_x.id, "atm_id": atm_syn_id}
            )
            
        # Target is Y. Y receives from X. X withdrew from ATM-SYN.
        # ATM-SYN should be a Syndicate candidate.
        # ATM-SPA should be a Spatial candidate (near ATM-SYN).
        candidates = cg.generate_candidates(acc_y.id, cutoff_time)
        
        atm_ids = [c.atm_id for c in candidates]
        
        # Syndicate validation
        assert atm_syn_id in atm_ids
        cand_syn = next(c for c in candidates if c.atm_id == atm_syn_id)
        assert "Syndicate" in cand_syn.reasons
        
        # Spatial validation
        assert atm_spa_id in atm_ids
        cand_spa = next(c for c in candidates if c.atm_id == atm_spa_id)
        assert "Spatial" in cand_spa.reasons
        
    finally:
        with driver.session() as session:
            session.run("MATCH (x:Account {account_number: $x}) DETACH DELETE x", {"x": test_x})
            session.run("MATCH (y:Account {account_number: $y}) DETACH DELETE y", {"y": test_y})
            session.run("MATCH (w:Withdrawal {withdrawal_id: $w_id}) DETACH DELETE w", {"w_id": w_x.id})
            session.run("MATCH (atm:ATM {atm_id: $atm_id}) DETACH DELETE atm", {"atm_id": atm_syn_id})
            
        db_session.delete(w_x)
        db_session.delete(acc_x)
        db_session.delete(acc_y)
        db_session.delete(atm_syn)
        db_session.delete(atm_spa)
        db_session.commit()
