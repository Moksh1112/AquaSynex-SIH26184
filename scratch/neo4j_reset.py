import sys, os
ROOT = r'C:\Users\ASUS\OneDrive\Desktop\AquaSynex-SIH26184'
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'backend'))
from app.db.neo4j_session import neo4j_conn
from app.db.neo4j_sync import sync_to_neo4j
from app.db.session import SessionLocal

print('--- BEFORE ---')
nodes = neo4j_conn.query('MATCH (n) RETURN count(n) as count')[0]['count']
rels = neo4j_conn.query('MATCH ()-[r]->() RETURN count(r) as count')[0]['count']
print(f'Nodes: {nodes}')
print(f'Relationships: {rels}')
txs = neo4j_conn.query('MATCH (t:Transaction) RETURN t.transaction_id AS id ORDER BY id')
print('Transactions:', [r['id'] for r in txs])

print('\n--- CLEARING NEO4J ---')
neo4j_conn.query('MATCH (n) DETACH DELETE n')

print('\n--- RUNNING SYNC ---')
db = SessionLocal()
try:
    sync_to_neo4j(db)
finally:
    db.close()

print('\n--- AFTER ---')
nodes_after = neo4j_conn.query('MATCH (n) RETURN count(n) as count')[0]['count']
rels_after = neo4j_conn.query('MATCH ()-[r]->() RETURN count(r) as count')[0]['count']
print(f'Nodes: {nodes_after}')
print(f'Relationships: {rels_after}')
txs_after = neo4j_conn.query('MATCH (t:Transaction) RETURN t.transaction_id AS id ORDER BY id')
print('Transactions:', [r['id'] for r in txs_after])

print('\n--- VERIFYING V-5001 CHAIN ---')
res = neo4j_conn.query('''
MATCH (v:Account {account_number: "V-5001"})-[:INITIATED]->(t1:Transaction)-[:RECEIVED_BY]->(m1:Account {account_number: "M-5001A"})
MATCH (m1)-[:INITIATED]->(t2:Transaction)-[:RECEIVED_BY]->(m2:Account {account_number: "M-5001B"})
MATCH (m2)-[:MADE_WITHDRAWAL]->(w:Withdrawal)-[:AT_ATM]->(atm:ATM {atm_id: "ATM-MUM-02"})
RETURN t1.transaction_id AS t1_id, t2.transaction_id AS t2_id, w.withdrawal_id AS w_id
''')
for r in res:
    print(f'V-5001 -> M-5001A (Tx {r["t1_id"]}) -> M-5001B (Tx {r["t2_id"]}) -> ATM-MUM-02 (Wd {r["w_id"]})')
