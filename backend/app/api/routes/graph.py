from fastapi import APIRouter, HTTPException
from typing import Any, Dict, List
from pydantic import BaseModel
from app.db.neo4j_session import neo4j_conn

router = APIRouter()

class GraphNode(BaseModel):
    id: str
    label: str
    metadata: Dict[str, Any]

class GraphEdge(BaseModel):
    source: str
    target: str
    type: str
    metadata: Dict[str, Any]

class GraphResponse(BaseModel):
    case_id: str
    nodes: List[GraphNode]
    edges: List[GraphEdge]

@router.get("/graph/{case_id}", response_model=GraphResponse)
def get_graph(case_id: str):
    # Enforces case isolation by starting from the specific complaint
    # and strictly following directed downstream money trail relationships
    query = """
    MATCH p=(c:Complaint {case_id: $case_id})-[:INVOLVES]->(a:Account)-[*0..4]->(m)
    WHERE ALL(r IN relationships(p) WHERE type(r) IN ['TRANSFERRED_TO', 'MADE_WITHDRAWAL', 'AT_ATM', 'INITIATED', 'RECEIVED_BY', 'INVOLVES'])
    UNWIND relationships(p) as r
    WITH startNode(r) AS n, r, endNode(r) AS m
    RETURN DISTINCT n, r, m
    """
    
    results = neo4j_conn.query(query, {"case_id": case_id})
    if not results:
        return {"case_id": case_id, "nodes": [], "edges": []}
        
    nodes = {}
    edges = []
    
    def get_node_id_and_label(node):
        labels = list(node.labels)
        label = labels[0] if labels else "Unknown"
        
        if label == "Account" and node.get("account_number"):
            custom_id = f"account_{node.get('account_number')}"
        elif label == "Transaction" and node.get("transaction_id"):
            custom_id = f"tx_{node.get('transaction_id')}"
        elif label == "Withdrawal" and node.get("withdrawal_id"):
            custom_id = f"wd_{node.get('withdrawal_id')}"
        elif label == "ATM" and node.get("atm_id"):
            custom_id = f"atm_{node.get('atm_id')}"
        else:
            custom_id = f"{label.lower()}_{node.element_id}"
            
        return custom_id, label

    for record in results:
        n = record["n"]
        m = record["m"]
        r = record["r"]
        
        n_custom_id, n_label = get_node_id_and_label(n)
        if n_custom_id not in nodes:
            nodes[n_custom_id] = {"id": n_custom_id, "label": n_label, "metadata": dict(n)}
            
        m_custom_id, m_label = get_node_id_and_label(m)
        if m_custom_id not in nodes:
            nodes[m_custom_id] = {"id": m_custom_id, "label": m_label, "metadata": dict(m)}
            
        edges.append({
            "source": n_custom_id,
            "target": m_custom_id,
            "type": r.type,
            "metadata": dict(r)
        })
        
    return {
        "case_id": case_id,
        "nodes": list(nodes.values()),
        "edges": edges
    }
