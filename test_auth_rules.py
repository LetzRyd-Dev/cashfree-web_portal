import requests

BASE_URL = "http://localhost:8000/api"

print("--- TEST 1: Fleet Operator (9691938866) ---")
res = requests.post(f"{BASE_URL}/auth/otp/verify", json={"phone": "9691938866", "otp": "1234", "user_type": "operator"})
print("Operator login status:", res.status_code, res.json())

print("\n--- TEST 2: Independent Driver (9901484683) ---")
res = requests.post(f"{BASE_URL}/auth/otp/verify", json={"phone": "9901484683", "otp": "1234", "user_type": "driver"})
print("Independent driver status:", res.status_code, res.json())

print("\n--- TEST 3: Fleet Driver (Managed by Operator - should be blocked) ---")
# Finding a fleet driver phone
from app.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    row = conn.execute(text("SELECT phone, full_name, operator_id FROM app_drivers WHERE operator_id > 0 AND phone NOT IN (SELECT phone FROM app_operators) LIMIT 1")).fetchone()
    fleet_phone = row[0]
    print(f"Testing fleet-managed driver: {row[1]} (Phone: {fleet_phone}, Operator ID: {row[2]})")

res = requests.post(f"{BASE_URL}/auth/otp/request", json={"phone": fleet_phone, "user_type": "driver"})
print("Fleet driver OTP request status:", res.status_code, res.json())

res = requests.post(f"{BASE_URL}/auth/otp/verify", json={"phone": fleet_phone, "otp": "1234", "user_type": "driver"})
print("Fleet driver OTP verify status:", res.status_code, res.json())
