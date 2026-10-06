from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()

cols = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'core_vehicle_allocation'")).scalars().fetchall()
print("core_vehicle_allocation columns:")
for c in cols:
    if any(k in c for k in ['phone', 'contact', 'reg', 'number', 'driver', 'plan']):
        print(" ", c)

db.close()
