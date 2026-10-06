"""
Comprehensive End-to-End Auditor for Multi-Role Partner Authentication & Profile Synchronization
"""
import jwt
from fastapi.testclient import TestClient
from sqlalchemy import text
from app.main import app
from app.database import SessionLocal
from app.config import settings
from app.models.app_models import AppDrivers, AppOperators

client = TestClient(app)
db = SessionLocal()

print("=" * 80)
print("MULTI-ROLE PARTNER AUTHENTICATION & PROFILE END-TO-END AUDIT REPORT")
print("=" * 80)

archetypes = {
    "Archetype 1: Fleet Operators": [
        ("9656907001", "Rishad P V"),
        ("9640404017", "Pasupureddy Karthik"),
        ("9691938866", "Anurag & RK Fleet Logistics"),
    ],
    "Archetype 2: Independent Drivers (Active Allocations)": [
        ("7899861394", "Sadath Pasha"),
        ("8008663719", "Ahmed Shareef"),
    ],
    "Archetype 3: Managed Drivers Under Operators": [
        ("6206009022", "Rohit Kumar (under Subair Ahamed M)"),
        ("9645999966", "Muhammad Shafeel V K (under Rishad P V)"),
        ("9848012346", "Mohammed Ali (under Samvreeddhi)"),
    ],
    "Archetype 4: Dual-Role Partners (Exist in Both Tables)": [
        ("7400234053", "Sayyed Sultan Feroz Ahmed"),
        ("9656907001", "Rishad P V"),
        ("9640404017", "Pasupureddy Karthik"),
    ],
}

total_tests = 0
passed_tests = 0
failures = []

def record(name, condition, details=""):
    global total_tests, passed_tests, failures
    total_tests += 1
    if condition:
        passed_tests += 1
        print(f"  [PASS] {name}")
    else:
        msg = f"  [FAIL] {name} | Error: {details}"
        print(msg)
        failures.append(msg)

for category, partners in archetypes.items():
    print(f"\n{'='*70}")
    print(f"AUDITING: {category}")
    print(f"{'='*70}")

    for phone, label in partners:
        print(f"\n--- Partner: {label} ({phone}) ---")

        # 1. Test OTP Request & Verify for Driver role (if registered as driver or dual)
        d_rec = db.query(AppDrivers).filter(AppDrivers.phone == phone).first()
        o_rec = db.query(AppOperators).filter(AppOperators.phone == phone).first()

        print(f"  DB Status -> Driver Table: {'YES' if d_rec else 'NO'}, Operator Table: {'YES' if o_rec else 'NO'}")

        # Test OTP flow requesting 'driver'
        res_req_drv = client.post("/api/auth/otp/request", json={"phone": phone, "user_type": "driver"})
        record(f"[{phone}] OTP Request (user_type=driver) status=200", res_req_drv.status_code == 200, res_req_drv.text)

        res_ver_drv = client.post("/api/auth/otp/verify", json={"phone": phone, "otp": "1234", "user_type": "driver"})
        record(f"[{phone}] OTP Verify (user_type=driver) status=200", res_ver_drv.status_code == 200, res_ver_drv.text)
        if res_ver_drv.status_code == 200:
            token_data = res_ver_drv.json()
            payload = jwt.decode(token_data["access_token"], settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            expected_role = "driver" if d_rec else "operator"
            record(
                f"[{phone}] Token payload user_type matches expected ({expected_role})",
                payload.get("user_type") == expected_role and token_data.get("user_type") == expected_role,
                f"Got token user_type={token_data.get('user_type')}, payload={payload.get('user_type')}"
            )

        # Test OTP flow requesting 'operator'
        res_req_op = client.post("/api/auth/otp/request", json={"phone": phone, "user_type": "operator"})
        record(f"[{phone}] OTP Request (user_type=operator) status=200", res_req_op.status_code == 200, res_req_op.text)

        res_ver_op = client.post("/api/auth/otp/verify", json={"phone": phone, "otp": "1234", "user_type": "operator"})
        record(f"[{phone}] OTP Verify (user_type=operator) status=200", res_ver_op.status_code == 200, res_ver_op.text)
        if res_ver_op.status_code == 200:
            token_data = res_ver_op.json()
            payload = jwt.decode(token_data["access_token"], settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            expected_role = "operator" if o_rec else "driver"
            record(
                f"[{phone}] Token payload user_type matches expected ({expected_role})",
                payload.get("user_type") == expected_role and token_data.get("user_type") == expected_role,
                f"Got token user_type={token_data.get('user_type')}, payload={payload.get('user_type')}"
            )

        # 2. Test Driver Profile Endpoint if driver exists
        if d_rec:
            res_dp = client.get(f"/api/drivers/by-phone/{phone}")
            record(f"[{phone}] /api/drivers/by-phone/{phone} returns 200", res_dp.status_code == 200, res_dp.text)
            if res_dp.status_code == 200:
                dp = res_dp.json()
                record(f"[{phone}] Driver vehicle_reg_number is non-null ({dp.get('vehicle_reg_number')})", dp.get("vehicle_reg_number") is not None)
                record(f"[{phone}] Driver assigned_manager_name is non-null ({dp.get('assigned_manager_name')})", dp.get("assigned_manager_name") is not None and dp.get("assigned_manager_name") != "")
                record(f"[{phone}] Driver assigned_manager_phone is non-null ({dp.get('assigned_manager_phone')})", dp.get("assigned_manager_phone") is not None and dp.get("assigned_manager_phone") != "")
                record(f"[{phone}] Driver address is non-null ({dp.get('address')[:30] if dp.get('address') else 'None'}...)", dp.get("address") is not None and dp.get("address") != "")

        # 3. Test Operator Profile Endpoint if operator exists
        if o_rec:
            res_op = client.get(f"/api/operators/by-phone/{phone}")
            record(f"[{phone}] /api/operators/by-phone/{phone} returns 200", res_op.status_code == 200, res_op.text)
            if res_op.status_code == 200:
                op = res_op.json()
                record(f"[{phone}] Operator company_name is non-null ({op.get('company_name')})", bool(op.get("company_name")))
                record(f"[{phone}] Operator contact_person_name is non-null ({op.get('contact_person_name')})", bool(op.get("contact_person_name")))
                record(f"[{phone}] Operator assigned_manager_name is non-null ({op.get('assigned_manager_name')})", bool(op.get("assigned_manager_name")))
                record(f"[{phone}] Operator address is non-null ({op.get('address')[:30] if op.get('address') else 'None'}...)", bool(op.get("address")))

            # Fleet summary endpoint
            res_fs = client.get(f"/api/operators/{o_rec.app_operator_id}/fleet-summary")
            record(f"[{phone}] /api/operators/{o_rec.app_operator_id}/fleet-summary returns 200", res_fs.status_code == 200, res_fs.text)
            if res_fs.status_code == 200:
                fs = res_fs.json()
                record(f"[{phone}] Fleet vehicles count is valid ({len(fs.get('vehicles', []))})", isinstance(fs.get("vehicles"), list))
                for v in fs.get("vehicles", []):
                    if not v.get("vehicle_number"):
                        record(f"[{phone}] Fleet vehicle has vehicle_number", False, str(v))

print("\n" + "=" * 80)
print("DATABASE WIDE AUDIT FOR ALL ACTIVE DRIVERS & OPERATORS")
print("=" * 80)

# Check active operators
active_ops_missing_comp = db.query(AppOperators).filter(
    AppOperators.is_active == True,
    (AppOperators.company_name == None) | (AppOperators.company_name == '')
).count()
record("All active operators have company_name", active_ops_missing_comp == 0, f"Found {active_ops_missing_comp} missing")

active_ops_missing_contact = db.query(AppOperators).filter(
    AppOperators.is_active == True,
    (AppOperators.contact_person_name == None) | (AppOperators.contact_person_name == '')
).count()
record("All active operators have contact_person_name", active_ops_missing_contact == 0, f"Found {active_ops_missing_contact} missing")

active_ops_missing_addr = db.query(AppOperators).filter(
    AppOperators.is_active == True,
    (AppOperators.address == None) | (AppOperators.address == '')
).count()
record("All active operators have address", active_ops_missing_addr == 0, f"Found {active_ops_missing_addr} missing")

active_ops_missing_mgr = db.query(AppOperators).filter(
    AppOperators.is_active == True,
    (AppOperators.assigned_manager_name == None) | (AppOperators.assigned_manager_name == '')
).count()
record("All active operators have assigned_manager_name", active_ops_missing_mgr == 0, f"Found {active_ops_missing_mgr} missing")

# Check active drivers with active car allocations
active_alloc_missing_veh = db.execute(text("""
    SELECT count(*) 
    FROM app_drivers d 
    JOIN app_driver_allocations a ON d.app_driver_id = a.app_driver_id 
    WHERE a.allocation_status = 'ACTIVE' AND (d.vehicle_reg_number IS NULL OR d.vehicle_reg_number = '')
""")).scalar()
record("Active drivers with active car allocation have vehicle_reg_number", active_alloc_missing_veh == 0, f"Found {active_alloc_missing_veh} missing")

active_drv_missing_addr = db.query(AppDrivers).filter(
    AppDrivers.is_active == True,
    (AppDrivers.address == None) | (AppDrivers.address == '')
).count()
record("All active drivers have address", active_drv_missing_addr == 0, f"Found {active_drv_missing_addr} missing")

active_drv_missing_mgr = db.query(AppDrivers).filter(
    AppDrivers.is_active == True,
    (AppDrivers.assigned_manager_name == None) | (AppDrivers.assigned_manager_name == '')
).count()
record("All active drivers have assigned_manager_name", active_drv_missing_mgr == 0, f"Found {active_drv_missing_mgr} missing")

print("\n" + "=" * 80)
print(f"AUDIT SUMMARY: {passed_tests} / {total_tests} TESTS PASSED ({(passed_tests/total_tests)*100:.1f}%)")
if failures:
    print(f"FAILURES DETECTED ({len(failures)}):")
    for f in failures:
        print(f)
else:
    print("ALL TESTS PASSED WITH 100% SUCCESS RATE!")
print("=" * 80)

db.close()
