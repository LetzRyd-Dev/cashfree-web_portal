from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()

# The remaining overlap - operator_id 44750 doesn't exist in app_operators, 
# so Samvreeddhi Mobility Fleet at app_operator_id 44750 is a different entity
# Let's confirm
op_44750 = db.execute(text("SELECT * FROM app_operators WHERE app_operator_id = 44750")).mappings().first()
print("app_operator_id 44750:", op_44750)

# So Bharath B R (DRV-1001) is actually a real driver under operator 713 (Samvreeddhi)
# The match was on company phone, not driver phone. Let's check operator 713
op_713 = db.execute(text("SELECT app_operator_id, company_name, phone, total_vehicles FROM app_operators WHERE app_operator_id = 713")).mappings().first()
print("Operator 713:", dict(op_713) if op_713 else "NOT FOUND")

db.close()
