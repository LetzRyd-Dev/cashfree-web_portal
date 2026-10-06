from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    print("=== Searching for tables with Faizan / Deepak / Durganjaneyulu ===")
    # Check tables that have columns like phone, name, email
    q = """
        SELECT table_name, column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
          AND data_type IN ('character varying', 'text')
          AND (column_name ILIKE '%name%' OR column_name ILIKE '%poc%' OR column_name ILIKE '%user%')
    """
    cols = conn.execute(text(q)).fetchall()
    found = set()
    for t, c in cols:
        if t in found:
            continue
        try:
            r = conn.execute(text(f"SELECT count(*) FROM {t} WHERE {c} ILIKE '%Faizan%'")).scalar()
            if r > 0:
                print(f"Found {r} in {t}.{c}")
                found.add(t)
        except Exception:
            pass
