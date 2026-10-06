from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()

cols = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'core_vehicle_allocation'")).scalars().fetchall()
print("Columns in core_vehicle_allocation:")
for c in cols:
    if 'rent' in c or 'rate' in c or 'plan' in c or 'amount' in c or 'tariff' in c:
        print("  ", c)

print("\nLet's check any table with plan or tariff or rental:")
tables = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).scalars().fetchall()
for t in tables:
    if any(k in t for k in ['plan', 'tariff', 'rental', 'rate', 'rent']):
        print("  Table:", t)

db.close()
