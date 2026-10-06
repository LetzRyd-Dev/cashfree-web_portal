from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()

tables = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).scalars().fetchall()
print("Tables in public schema:")
for t in sorted(tables):
    if 'operator' in t or 'driver' in t or 'fleet' in t or 'hisaab' in t or 'user' in t or 'alloc' in t:
        count = db.execute(text(f"SELECT count(*) FROM {t}")).scalar()
        print(f"  {t}: {count} rows")

db.close()
