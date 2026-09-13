import sqlalchemy
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://moksh:moksh26184@localhost:5432/sih26184')

with engine.connect() as conn:
    print('--- TABLES ---')
    tables = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")).fetchall()
    for t in tables:
        print(t[0])
        
    print('\n--- GEOMETRY COLUMNS ---')
    geo = conn.execute(text("SELECT f_table_name, f_geometry_column, type, srid FROM geometry_columns")).fetchall()
    for g in geo:
        print(g)
        
    print('\n--- INDEXES ---')
    indexes = conn.execute(text("SELECT indexname, indexdef FROM pg_indexes WHERE tablename IN ('atms', 'h3_cells') AND indexname LIKE 'idx_%'")).fetchall()
    for idx in indexes:
        print(idx)
