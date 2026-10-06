from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()

# Check how many drivers have Ramesh Naik or Priya Kumar
rn = db.execute(text("SELECT count(*) FROM app_drivers WHERE assigned_manager_name LIKE '%Ramesh%' OR assigned_manager_phone LIKE '%9876543299%'")).scalar()
print("Drivers with Ramesh Naik:", rn)

pk = db.execute(text("SELECT count(*) FROM app_drivers WHERE emergency_name LIKE '%Priya%'")).scalar()
print("Drivers with Priya Kumar:", pk)

# Who are the actual managers?
mgrs = db.execute(text("SELECT assigned_manager_name, assigned_manager_phone, count(*) FROM app_drivers GROUP BY assigned_manager_name, assigned_manager_phone ORDER BY count(*) DESC LIMIT 10")).fetchall()
print("\nTop driver managers:")
for m in mgrs:
    print(" ", m)

db.close()
