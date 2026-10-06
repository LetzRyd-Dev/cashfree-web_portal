from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()

# Clean Ramesh Naik
res1 = db.execute(text("""
    UPDATE app_drivers
    SET assigned_manager_name = NULL,
        assigned_manager_phone = NULL
    WHERE assigned_manager_name ILIKE '%Ramesh Naik%'
       OR assigned_manager_phone = '9876543299'
"""))

# Clean Priya Kumar fake emergency contact
res2 = db.execute(text("""
    UPDATE app_drivers
    SET emergency_name = NULL,
        emergency_phone = NULL,
        emergency_relation = NULL
    WHERE emergency_name ILIKE '%Priya Kumar%'
       OR emergency_phone = '9876543211'
"""))

db.commit()
print(f"Cleaned fake managers from {res1.rowcount} drivers.")
print(f"Cleaned fake emergency contacts from {res2.rowcount} drivers.")

db.close()
