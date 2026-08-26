"""
test_audit.py — Comprehensive Backend Verification and Bug Audit Test Suite
"""
import sys
from fastapi.testclient import TestClient
from app.main import app

def run_audit():
    client = TestClient(app)
    passed = 0
    failed = 0
    errors = []

    def check(name, condition, details=""):
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  [PASS] {name}")
        else:
            failed += 1
            msg = f"  [FAIL] {name} - {details}"
            print(msg)
            errors.append(msg)

    print("\n" + "="*70)
    print(" 1. HEALTH & SYSTEM CHECKS")
    print("="*70)
    res = client.get("/api/health")
    check("Health check returns 200", res.status_code == 200)
    check("Health status is healthy", res.json().get("status") == "healthy")

    print("\n" + "="*70)
    print(" 2. AUTHENTICATION & OTP FLOWS")
    print("="*70)
    # Request OTP with primary driver phone
    res = client.post("/api/auth/otp/request", json={"phone": "9901484683"})
    check("Request OTP valid phone returns 200", res.status_code == 200)

    # Request OTP with demo driver alias
    res = client.post("/api/auth/otp/request", json={"phone": "9876543210"})
    check("Request OTP demo alias 9876543210 returns 200", res.status_code == 200)

    # Request OTP with demo operator alias
    res = client.post("/api/auth/otp/request", json={"phone": "9876543222"})
    check("Request OTP demo alias 9876543222 returns 200", res.status_code == 200)

    # Request OTP with invalid phone -> 404
    res = client.post("/api/auth/otp/request", json={"phone": "0000000000"})
    check("Request OTP invalid phone returns 404", res.status_code == 404)

    # Verify OTP valid
    res = client.post("/api/auth/otp/verify", json={"phone": "9901484683", "otp": "1234"})
    check("Verify OTP valid returns 200", res.status_code == 200)
    data = res.json()
    check("Verify OTP returns access_token", bool(data.get("access_token")))
    check("Verify OTP returns user_type=driver", data.get("user_type") == "driver")
    check("Verify OTP returns name=Vivek", data.get("name") == "Vivek")

    # Verify OTP demo alias
    res = client.post("/api/auth/otp/verify", json={"phone": "9876543210", "otp": "1234"})
    check("Verify OTP demo alias returns 200", res.status_code == 200)

    # Verify OTP operator demo alias
    res = client.post("/api/auth/otp/verify", json={"phone": "9876543222", "otp": "1234"})
    check("Verify OTP operator demo alias returns 200", res.status_code == 200)
    check("Verify OTP operator returns user_type=operator", res.json().get("user_type") == "operator")

    # Verify OTP invalid OTP -> 400
    res = client.post("/api/auth/otp/verify", json={"phone": "9901484683", "otp": "9999"})
    check("Verify OTP invalid OTP returns 400", res.status_code == 400)

    # Password login
    res = client.post("/api/auth/login/password", json={"phone": "9901484683", "password": "password123"})
    check("Password login returns 200", res.status_code == 200)

    print("\n" + "="*70)
    print(" 3. DRIVER PROFILE & FLEET ENDPOINTS")
    print("="*70)
    # By phone
    res = client.get("/api/drivers/by-phone/9901484683")
    check("GET /api/drivers/by-phone/9901484683 returns 200", res.status_code == 200)
    d = res.json()
    check("Driver name is Vivek", d.get("full_name") == "Vivek")
    check("Driver vehicle_reg_number is KA05AQ7692", d.get("vehicle_reg_number") == "KA05AQ7692")

    # By phone alias route
    res = client.get("/api/drivers/phone/9901484683")
    check("GET /api/drivers/phone/9901484683 returns 200", res.status_code == 200)

    # By demo alias phone
    res = client.get("/api/drivers/by-phone/9876543210")
    check("GET /api/drivers/by-phone/9876543210 (alias) returns 200", res.status_code == 200)
    check("Alias resolves to Vivek", res.json().get("full_name") == "Vivek")

    # By ID (app_driver_id = 1)
    res = client.get("/api/drivers/1")
    check("GET /api/drivers/1 returns 200", res.status_code == 200)

    # By legacy driver_id (driver_id = 157)
    res = client.get("/api/drivers/157")
    check("GET /api/drivers/157 (legacy ID) returns 200", res.status_code == 200)

    # Non-existent driver -> 404
    res = client.get("/api/drivers/99999")
    check("GET /api/drivers/99999 returns 404", res.status_code == 404)

    # Current driver (/me)
    res = client.get("/api/drivers/me")
    check("GET /api/drivers/me returns 200", res.status_code == 200)

    # Drivers in fleet
    res = client.get("/api/drivers/fleet/1")
    check("GET /api/drivers/fleet/1 returns 200", res.status_code == 200)
    check("Operator 1 has 4 drivers", res.json().get("count") == 4)

    print("\n" + "="*70)
    print(" 4. OPERATOR PROFILE & FLEET SUMMARY ENDPOINTS")
    print("="*70)
    res = client.get("/api/operators/by-phone/9691938866")
    check("GET /api/operators/by-phone/9691938866 returns 200", res.status_code == 200)
    op = res.json()
    check("Company name is Anurag & RK Fleet Logistics", "Anurag" in op.get("company_name", ""))

    # Phone alias
    res = client.get("/api/operators/by-phone/9876543222")
    check("GET /api/operators/by-phone/9876543222 (alias) returns 200", res.status_code == 200)

    # By ID
    res = client.get("/api/operators/1")
    check("GET /api/operators/1 returns 200", res.status_code == 200)

    # Fleet summary
    res = client.get("/api/operators/1/fleet-summary")
    check("GET /api/operators/1/fleet-summary returns 200", res.status_code == 200)
    summary = res.json()
    check("Fleet summary vehicles count is 4", len(summary.get("vehicles", [])) == 4)
    check("Fleet summary has address populated", bool(summary.get("address")))
    check("Fleet summary has manager phone", bool(summary.get("assigned_manager_phone")))

    # Current operator (/me)
    res = client.get("/api/operators/me")
    check("GET /api/operators/me returns 200", res.status_code == 200)

    # Non-existent operator -> 404
    res = client.get("/api/operators/99999")
    check("GET /api/operators/99999 returns 404", res.status_code == 404)

    print("\n" + "="*70)
    print(" 5. HISAAB STATEMENTS & FINANCIAL ARITHMETIC")
    print("="*70)
    # Driver hisaabs
    res = client.get("/api/hisaabs/driver/1")
    check("GET /api/hisaabs/driver/1 returns 200", res.status_code == 200)
    check("Driver 1 has 3 hisaab statements", res.json().get("count") == 3)

    # Legacy driver ID hisaabs
    res = client.get("/api/hisaabs/driver/157")
    check("GET /api/hisaabs/driver/157 (legacy ID) returns 200", res.status_code == 200)
    check("Legacy driver 157 maps to 3 hisaabs", res.json().get("count") == 3)

    # Operator hisaabs
    res = client.get("/api/hisaabs/operator/1")
    check("GET /api/hisaabs/operator/1 returns 200", res.status_code == 200)
    check("Operator 1 has 12 hisaab statements", res.json().get("count") == 12)

    # Specific hisaab breakdown
    res = client.get("/api/hisaabs/1")
    check("GET /api/hisaabs/1 returns 200", res.status_code == 200)
    h = res.json()
    check("Hisaab 1 has hisaab_number", bool(h.get("hisaab_number")))
    check("Hisaab 1 week_number is 30", h.get("week_number") == 30)

    # Financial arithmetic verification:
    # 1. Total deductions = vehicle_rent + maintenance_charge + tds_amount + challan_amount + accident_charge + gps_dead_penalty - other_adjustment
    expected_deductions = round(
        h.get("vehicle_rent", 0) +
        h.get("maintenance_charge", 0) +
        h.get("tds_amount", 0) +
        h.get("challan_amount", 0) +
        h.get("accident_charge", 0) +
        h.get("gps_dead_penalty", 0) -
        h.get("other_adjustment", 0),
        2
    )
    check(
        f"Hisaab deductions arithmetic (calculated: {expected_deductions} vs recorded: {h.get('total_deductions')})",
        abs(expected_deductions - h.get("total_deductions", 0)) < 0.05
    )

    # 2. Net settlement logic: to_pay and to_collect are non-negative and mutually exclusive
    to_pay = h.get("to_pay", 0)
    to_collect = h.get("to_collect", 0)
    check("to_pay >= 0 and to_collect >= 0", to_pay >= 0 and to_collect >= 0)
    check("to_pay == 0 or to_collect == 0 (mutually exclusive)", to_pay == 0 or to_collect == 0)

    # Non-existent hisaab -> 404
    res = client.get("/api/hisaabs/99999")
    check("GET /api/hisaabs/99999 returns 404", res.status_code == 404)

    print("\n" + "="*70)
    print(" 6. PAYMENTS & CASHFREE CHECKOUT")
    print("="*70)
    # Payment initiation
    res = client.post("/api/payments/initiate", json={
        "amount": 750.0,
        "payment_mode": "cashfree_upi",
        "app_hisaab_id": 1,
        "payer_type": "driver",
        "payer_id": 1
    })
    check("POST /api/payments/initiate returns 200", res.status_code == 200)
    p_data = res.json()
    check("Payment has order ID", bool(p_data.get("cf_order_id")))
    check("Payment status is INITIATED", p_data.get("status") == "INITIATED")

    # Create-order endpoint (both /api/create-order and /api/payments/create-order)
    res = client.post("/api/create-order", json={
        "amount": 1000.0,
        "driverName": "Vivek",
        "driverPhone": "9901484683",
        "driverId": 1,
        "weekRange": "21 Jul - 27 Jul"
    })
    check("POST /api/create-order returns 200", res.status_code == 200)
    co_data = res.json()
    check("create-order returns payment_session_id", bool(co_data.get("payment_session_id")))
    check("create-order returns order_id", bool(co_data.get("order_id")))

    # Payment history
    res = client.get("/api/payments/history?payer_id=1")
    check("GET /api/payments/history returns 200", res.status_code == 200)
    check("Payment history has records", res.json().get("count", 0) >= 1)

    # Cashfree webhook simulation
    res = client.post("/api/payments/webhook/cashfree", json={
        "order": {"order_id": p_data.get("cf_order_id")},
        "payment": {"payment_status": "SUCCESS"}
    })
    check("POST /api/payments/webhook/cashfree returns 200", res.status_code == 200)

    print("\n" + "="*70)
    print(" 7. SUPPORT TICKETS")
    print("="*70)
    res = client.get("/api/tickets?creator_id=1")
    check("GET /api/tickets?creator_id=1 returns 200", res.status_code == 200)
    check("Driver 1 has tickets", res.json().get("count", 0) >= 2)

    res = client.post("/api/tickets", json={
        "creator_type": "driver",
        "creator_id": 1,
        "category": "Dispute",
        "subject": "Toll refund request",
        "description": "Airport toll receipt attached for reimbursement",
        "priority": "high"
    })
    check("POST /api/tickets returns 200", res.status_code == 200)
    t_data = res.json()
    check("Ticket has generated ticket_number", bool(t_data.get("ticket_number")))
    check("Ticket status is open", t_data.get("status") == "open")

    print("\n" + "="*70)
    print(" 8. NOTIFICATIONS & FEED")
    print("="*70)
    res = client.get("/api/notifications?target_id=1")
    check("GET /api/notifications?target_id=1 returns 200", res.status_code == 200)
    notifs = res.json()
    check("Notifications list is non-empty", len(notifs) >= 3)
    
    first_notif_id = notifs[0].get("app_notif_id")
    res = client.put(f"/api/notifications/{first_notif_id}/read")
    check(f"PUT /api/notifications/{first_notif_id}/read returns 200", res.status_code == 200)

    res = client.put("/api/notifications/99999/read")
    check("PUT /api/notifications/99999/read returns 404", res.status_code == 404)

    print("\n" + "="*70)
    print(" 9. REFERRALS PROGRAM")
    print("="*70)
    res = client.get("/api/referrals?driver_id=1")
    check("GET /api/referrals?driver_id=1 returns 200", res.status_code == 200)
    check("Driver 1 has referral leads", res.json().get("count", 0) >= 1)

    res = client.post("/api/referrals", json={
        "referred_by_type": "driver",
        "referred_by_id": 1,
        "lead_name": "Rohan Deshmukh",
        "lead_phone": "9822334455"
    })
    check("POST /api/referrals returns 200", res.status_code == 200)
    ref_data = res.json()
    check("Referral status is submitted", ref_data.get("status") == "submitted")
    check("Referral reward amount is 1000.0", ref_data.get("reward_amount") == 1000.0)

    print("\n" + "="*70)
    print(" 10. SECURITY AUDIT LOGS")
    print("="*70)
    res = client.get("/api/audit")
    check("GET /api/audit returns 200", res.status_code == 200)
    check("Audit logs contain recorded events", res.json().get("count", 0) >= 1)

    print("\n" + "="*70)
    print(f" AUDIT SUMMARY: {passed} PASSED, {failed} FAILED")
    print("="*70)

    if failed > 0:
        print("\nFailures:")
        for err in errors:
            print(err)
        sys.exit(1)
    else:
        print("\nAll backend routes, database models, schemas, and arithmetic verified 100% OK!")

if __name__ == "__main__":
    run_audit()
