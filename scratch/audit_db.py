import sqlalchemy
from sqlalchemy import create_engine, text
import json

engine = create_engine('postgresql://moksh:moksh26184@localhost:5432/sih26184')

with engine.connect() as conn:
    print('--- 1. POSTGRESQL & POSTGIS VERSIONS ---')
    print(conn.execute(text("SELECT version()")).scalar())
    print(conn.execute(text("SELECT postgis_full_version()")).scalar())
    print(conn.execute(text("SELECT current_database()")).scalar())
    print(conn.execute(text("SELECT current_user")).scalar())
    print(conn.execute(text("SELECT inet_server_addr(), inet_server_port()")).fetchone())

    print('\n--- 3. DATABASE TABLES ---')
    tables = [r[0] for r in conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")).fetchall()]
    expected_tables = ['users', 'complaints', 'accounts', 'transactions', 'withdrawals', 'atms', 'h3_cells', 'predictions', 'prediction_candidates', 'alerts', 'audit_logs']
    for t in expected_tables:
        print(f"{t}: {'Found' if t in tables else 'Missing'}")

    print('\n--- 4. POSTGIS DETAILS ---')
    geo = conn.execute(text("SELECT f_table_name, f_geometry_column, type, srid FROM geometry_columns")).fetchall()
    for g in geo:
        print(g)
    
    indexes = conn.execute(text("SELECT indexname FROM pg_indexes WHERE tablename IN ('atms', 'h3_cells') AND indexname LIKE 'idx_%'")).fetchall()
    for idx in indexes:
        print(idx[0])

    print('Spatial Query test:')
    res = conn.execute(text("SELECT ST_Distance(ST_SetSRID(ST_MakePoint(72.8777, 19.0760), 4326)::geography, ST_SetSRID(ST_MakePoint(72.8, 19.1), 4326)::geography)")).scalar()
    print(f"Distance between points: {res}")

    print('\n--- 5. SEED DATA COUNTS ---')
    for t in expected_tables:
        count = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
        print(f"{t}: {count} rows")
