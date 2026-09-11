import logging
from sqlalchemy.orm import Session
from app.db.neo4j_session import neo4j_conn
from app.models import Account, Transaction, Withdrawal, ATM, Complaint

logger = logging.getLogger(__name__)

def sync_to_neo4j(db: Session):
    """
    Synchronizes authoritative data from PostgreSQL to Neo4j graph.
    This operation uses MERGE to remain idempotent.
    """
    if neo4j_conn.query("RETURN 1") is None:
        logger.error("Neo4j connection not available. Skipping sync.")
        return

    logger.info("Starting Neo4j synchronization...")

    # 1. Sync Accounts
    accounts = db.query(Account).all()
    for acc in accounts:
        query = """
        MERGE (a:Account {account_number: $acc_num})
        SET a.bank_name = $bank_name,
            a.is_flagged = $is_flagged
        """
        neo4j_conn.query(query, {
            "acc_num": acc.account_number,
            "bank_name": acc.bank_name,
            "is_flagged": acc.is_flagged
        })

    # 2. Sync ATMs
    atms = db.query(ATM).all()
    for atm in atms:
        query = """
        MERGE (a:ATM {atm_id: $atm_id})
        SET a.latitude = $lat,
            a.longitude = $lon,
            a.address = $address
        """
        neo4j_conn.query(query, {
            "atm_id": atm.atm_id,
            "lat": atm.latitude,
            "lon": atm.longitude,
            "address": atm.address
        })

    # 3. Sync Complaints
    complaints = db.query(Complaint).all()
    for comp in complaints:
        query = """
        MERGE (c:Complaint {case_id: $case_id})
        SET c.description = $desc,
            c.status = $status,
            c.reported_at = $reported_at
        """
        neo4j_conn.query(query, {
            "case_id": comp.case_id,
            "desc": comp.description,
            "status": comp.status.value if hasattr(comp.status, 'value') else str(comp.status),
            "reported_at": comp.reported_at.isoformat() if comp.reported_at else None
        })

    # 4. Sync Transactions & Relationships
    transactions = db.query(Transaction).all()
    for txn in transactions:
        # Create Transaction Node
        query_txn = """
        MERGE (t:Transaction {transaction_id: $txn_id})
        SET t.amount = $amount,
            t.timestamp = $timestamp
        """
        neo4j_conn.query(query_txn, {
            "txn_id": txn.id,
            "amount": txn.amount,
            "timestamp": txn.timestamp.isoformat() if txn.timestamp else None
        })

        sender = db.query(Account).filter(Account.id == txn.sender_account_id).first()
        receiver = db.query(Account).filter(Account.id == txn.receiver_account_id).first()

        if sender and receiver:
            # Direct money flow Account -> Account
            query_flow = """
            MATCH (s:Account {account_number: $s_acc}), (r:Account {account_number: $r_acc})
            MERGE (s)-[rel:TRANSFERRED_TO {transaction_id: $txn_id}]->(r)
            SET rel.amount = $amount,
                rel.timestamp = $timestamp
            """
            neo4j_conn.query(query_flow, {
                "s_acc": sender.account_number,
                "r_acc": receiver.account_number,
                "txn_id": txn.id,
                "amount": txn.amount,
                "timestamp": txn.timestamp.isoformat() if txn.timestamp else None
            })

            # Provenance
            query_prov = """
            MATCH (s:Account {account_number: $s_acc}), (r:Account {account_number: $r_acc}), (t:Transaction {transaction_id: $txn_id})
            MERGE (s)-[:INITIATED]->(t)
            MERGE (t)-[:RECEIVED_BY]->(r)
            """
            neo4j_conn.query(query_prov, {
                "s_acc": sender.account_number,
                "r_acc": receiver.account_number,
                "txn_id": txn.id
            })

    # 5. Sync Withdrawals & Relationships
    withdrawals = db.query(Withdrawal).all()
    for w in withdrawals:
        query_w = """
        MERGE (w:Withdrawal {withdrawal_id: $w_id})
        SET w.amount = $amount,
            w.timestamp = $timestamp
        """
        neo4j_conn.query(query_w, {
            "w_id": w.id,
            "amount": w.amount,
            "timestamp": w.timestamp.isoformat() if w.timestamp else None
        })

        acc = db.query(Account).filter(Account.id == w.account_id).first()
        if acc:
            query_rel1 = """
            MATCH (a:Account {account_number: $acc_num}), (w:Withdrawal {withdrawal_id: $w_id})
            MERGE (a)-[:MADE_WITHDRAWAL]->(w)
            """
            neo4j_conn.query(query_rel1, {"acc_num": acc.account_number, "w_id": w.id})

        # The model says withdrawal.atm_id is the string identifier (atm_id in ATM, not the primary key id)
        query_rel2 = """
        MATCH (w:Withdrawal {withdrawal_id: $w_id}), (atm:ATM {atm_id: $atm_id})
        MERGE (w)-[:AT_ATM]->(atm)
        """
        neo4j_conn.query(query_rel2, {"w_id": w.id, "atm_id": w.atm_id})

    logger.info("Neo4j synchronization complete.")
