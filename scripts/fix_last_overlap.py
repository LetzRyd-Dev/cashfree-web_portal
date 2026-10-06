from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()

# app_operator_id 44750 is a ghost operator - Samvreeddhi with NULL total_vehicles and no hisaabs
# But it has phone 7483731338 which matches Bharath B R (a real driver)
# Delete this ghost operator
res = db.execute(text("DELETE FROM app_operators WHERE app_operator_id = 44750"))
db.commit()
print(f"Deleted ghost operator app_operator_id 44750: {res.rowcount} row(s)")

# Verify no more overlaps
remaining = db.execute(text("""
    SELECT count(*) FROM app_drivers d
    JOIN app_operators o ON d.phone = o.phone
""")).scalar()
print(f"Phone overlaps remaining: {remaining}")

db.close()
