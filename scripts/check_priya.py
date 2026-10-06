from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()

pk = db.execute(text("SELECT app_driver_id, full_name, emergency_name, emergency_phone FROM app_drivers WHERE emergency_name ILIKE '%Priya%'")).mappings().fetchall()
for p in pk:
    print(dict(p))

db.close()
