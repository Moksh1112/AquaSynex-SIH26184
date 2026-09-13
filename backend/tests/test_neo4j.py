import pytest
from app.db.neo4j_session import get_neo4j_driver
from app.core.config import settings

def test_neo4j_configuration():
    """Verify Neo4j configuration is loaded."""
    assert settings.NEO4J_URI.startswith("bolt://")
    assert settings.NEO4J_USERNAME is not None
    assert settings.NEO4J_PASSWORD is not None

def test_neo4j_connectivity():
    """Verify Neo4j is reachable and authentication succeeds."""
    driver = get_neo4j_driver()
    if driver is None:
        pytest.skip("Neo4j is not reachable or credentials failed")
    
    with driver.session() as session:
        result = session.run("RETURN 1 as n").single()
        assert result["n"] == 1

def test_neo4j_constraints():
    """Verify constraints exist."""
    driver = get_neo4j_driver()
    if driver is None:
        pytest.skip("Neo4j is not reachable")
        
    with driver.session() as session:
        # Check constraints (syntax works for Neo4j 5+)
        result = session.run("SHOW CONSTRAINTS").data()
        labels_with_constraints = [r['labelsOrTypes'][0] for r in result if 'labelsOrTypes' in r and len(r['labelsOrTypes']) > 0]
        
        # Verify our expected labels have constraints
        assert "Account" in labels_with_constraints
        assert "Transaction" in labels_with_constraints
        assert "Withdrawal" in labels_with_constraints
        assert "ATM" in labels_with_constraints
        assert "Complaint" in labels_with_constraints

def test_neo4j_sih26184_graph():
    """Verify the specific SIH26184 graph (C-2026-9081) was created correctly."""
    driver = get_neo4j_driver()
    if driver is None:
        pytest.skip("Neo4j is not reachable")
        
    with driver.session() as session:
        # Verify the victim -> mule1 -> mule2 path
        query_path = """
        MATCH p = (v:Account {account_number: 'V-100200300'})-[:TRANSFERRED_TO*2]->(m2:Account {account_number: 'M-555444333'})
        RETURN nodes(p) as accounts, [r IN relationships(p) | r.amount] as amounts
        """
        result = session.run(query_path).single()
        assert result is not None, "Victim -> Mule1 -> Mule2 path not found"
        
        accounts = result["accounts"]
        amounts = result["amounts"]
        assert len(accounts) == 3
        assert accounts[0]["account_number"] == "V-100200300"
        assert accounts[1]["account_number"] == "M-999888777"
        assert accounts[2]["account_number"] == "M-555444333"
        
        # Transaction amounts in the seed are 45000.0 and 40000.0
        assert amounts[0] == 45000.0
        assert amounts[1] == 40000.0

        # Verify Mule2 -> ATM withdrawal
        query_withdrawal = """
        MATCH (m:Account {account_number: 'M-555444333'})-[:MADE_WITHDRAWAL]->(w:Withdrawal)-[:AT_ATM]->(atm:ATM)
        RETURN w.amount as amount, atm.atm_id as atm_id
        """
        w_result = session.run(query_withdrawal).single()
        assert w_result is not None, "Withdrawal to ATM path not found"
        assert w_result["amount"] == 40000.0
        assert w_result["atm_id"] == "ATM-MUM-01"

        # Verify Complaint exists
        query_case = "MATCH (c:Complaint {case_id: 'C-2026-9081'}) RETURN c.status as status"
        c_result = session.run(query_case).single()
        assert c_result is not None, "Complaint node not found"
        assert c_result["status"] == "OPEN"

def test_neo4j_idempotency():
    """Verify that syncing twice doesn't create duplicate nodes."""
    driver = get_neo4j_driver()
    if driver is None:
        pytest.skip("Neo4j is not reachable")
        
    with driver.session() as session:
        # Check node counts for Mule 1
        query = "MATCH (a:Account {account_number: 'M-999888777'}) RETURN count(a) as cnt"
        result = session.run(query).single()
        assert result["cnt"] == 1
