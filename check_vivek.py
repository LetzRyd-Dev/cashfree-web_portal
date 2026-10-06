from app.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    row = conn.execute(text("SELECT app_driver_id, full_name, phone, operator_id FROM app_drivers WHERE phone = '9901484683'")).fetchone()
    print("Vivek row in DB:", dict(row._mapping))
