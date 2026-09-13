import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_graph_mocked(monkeypatch):
    """Test retrieving graph data with mocked neo4j session."""
    
    class MockRecord:
        def __init__(self, n, r, m):
            self._n = n
            self._r = r
            self._m = m
            
        def __getitem__(self, key):
            if key == "n": return self._n
            if key == "r": return self._r
            if key == "m": return self._m
            raise KeyError(key)

    class MockNode:
        def __init__(self, element_id, labels, properties):
            self.element_id = element_id
            self.labels = labels
            self.properties = properties
            
        def get(self, key):
            return self.properties.get(key)
            
        def keys(self):
            return self.properties.keys()
            
        def __iter__(self):
            return iter(self.properties)
            
        def __getitem__(self, key):
            return self.properties[key]
            
    class MockRelationship:
        def __init__(self, type, properties):
            self.type = type
            self.properties = properties
            
        def keys(self):
            return self.properties.keys()
            
        def __iter__(self):
            return iter(self.properties)
            
        def __getitem__(self, key):
            return self.properties[key]

    mock_results = [
        MockRecord(
            n=MockNode("1", ["Account"], {"account_number": "V-100200300"}),
            r=MockRelationship("TRANSFERRED_TO", {"amount": 45000}),
            m=MockNode("2", ["Account"], {"account_number": "M-999888777"})
        ),
        MockRecord(
            n=MockNode("2", ["Account"], {"account_number": "M-999888777"}),
            r=MockRelationship("TRANSFERRED_TO", {"amount": 40000}),
            m=MockNode("3", ["Account"], {"account_number": "M-555444333"})
        ),
        MockRecord(
            n=MockNode("3", ["Account"], {"account_number": "M-555444333"}),
            r=MockRelationship("MADE_WITHDRAWAL", {}),
            m=MockNode("4", ["Withdrawal"], {"withdrawal_id": "1"})
        ),
        MockRecord(
            n=MockNode("4", ["Withdrawal"], {"withdrawal_id": "1"}),
            r=MockRelationship("AT_ATM", {}),
            m=MockNode("5", ["ATM"], {"atm_id": "ATM-MUM-01"})
        ),
        MockRecord(
            n=MockNode("3", ["Account"], {"account_number": "M-555444333"}),
            r=MockRelationship("INITIATED", {}),
            m=MockNode("6", ["Transaction"], {"transaction_id": "1"})
        )
    ]
    
    def mock_query(query):
        return mock_results
        
    from app.api.routes import graph
    class MockNeo4jConn:
        def query(self, q):
            return mock_query(q)
            
    monkeypatch.setattr(graph, "neo4j_conn", MockNeo4jConn())
    
    response = client.get("/graph/C-2026-9081")
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == "C-2026-9081"
    assert len(data["nodes"]) == 6
    assert len(data["edges"]) == 5
    
    node_ids = {n["id"] for n in data["nodes"]}
    assert "account_V-100200300" in node_ids
    assert "atm_ATM-MUM-01" in node_ids
    assert "wd_1" in node_ids
    assert "tx_1" in node_ids

@pytest.mark.skip(reason="Requires live Neo4j environment")
def test_get_graph_integration():
    """Integration test: actual graph read."""
    res = client.get("/graph/C-2026-9081")
    assert res.status_code == 200
    data = res.json()
    assert data["case_id"] == "C-2026-9081"
    assert "nodes" in data
    assert "edges" in data
