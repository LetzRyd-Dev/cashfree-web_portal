from app.database import engine
from sqlalchemy import text
import requests

with engine.connect() as conn:
    row = conn.execute(text("SELECT app_driver_id, full_name, phone, operator_id FROM app_drivers WHERE (operator_id IS NULL OR operator_id = 0) LIMIT 5")).fetchall()
    print("Sample Independent Drivers:")
    for r in row:
        print(dict(r._mapping))
        
    test_phone = row[0][2]
    print(f"\nTesting independent driver login for {row[0][1]} ({test_phone}):")
    res = requests.post("http://localhost:8000/api/auth/otp/verify", json={"phone": test_phone, "otp": "1234", "user_type": "driver"})
    print("Status:", res.status_code, res.json())
