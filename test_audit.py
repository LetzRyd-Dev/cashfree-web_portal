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
    print(" 6. PAYMENTS & CASHFREE CHECKOUT AUDIT")
    print("="*70)
    # 6.1 Fleet Driver Payment Block (Vivek, app_driver_id=1, operator_id=1)
    res = client.post("/api/payments/initiate", json={
        "amount": 750.0,
        "payment_mode": "cashfree_upi",
        "app_hisaab_id": 1,
        "payer_type": "driver",
        "payer_id": 1
    })
    check("Fleet driver initiation is blocked with 400 Bad Request", res.status_code == 400)
    check("Block detail explains operator management", "managed by fleet operator" in res.json().get("detail", ""))

    res = client.post("/api/create-order", json={
        "amount": 1000.0,
        "driverName": "Vivek",
        "driverPhone": "9901484683",
        "driverId": 1,
        "weekRange": "21 Jul - 27 Jul"
    })
    check("Fleet driver create-order is blocked with 400 Bad Request", res.status_code == 400)

    # 6.2 Independent Driver Payment Flows (TULTUL DAS, app_driver_id=14, operator_id=0)
    res = client.post("/api/payments/initiate", json={
        "amount": 500.0,
        "payment_mode": "cashfree_upi",
        "app_hisaab_id": 1181,
        "payer_type": "driver",
        "payer_id": 14
    })
    check("Independent driver initiate returns 200", res.status_code == 200)
    p_data = res.json()
    check("Payment has unique order ID", bool(p_data.get("cf_order_id")))
    check("Payment status is INITIATED", p_data.get("status") == "INITIATED")

    res = client.post("/api/create-order", json={
        "amount": 1500.0,
        "driverName": "TULTUL DAS",
        "driverPhone": "6001357616",
        "driverId": 14,
        "weekRange": "Week 39"
    })
    check("Independent driver create-order returns 200", res.status_code == 200)
    co_data = res.json()
    check("create-order returns valid payment_session_id", bool(co_data.get("payment_session_id")))
    check("create-order returns valid order_id", bool(co_data.get("order_id")))

    # 6.3 Operator Payment Initiation (Operator 1, Anurag & RK Fleet Logistics)
    res = client.post("/api/payments/initiate", json={
        "amount": 2500.0,
        "payment_mode": "cashfree_netbanking",
        "payer_type": "operator",
        "payer_id": 1
    })
    check("Operator payment initiate returns 200", res.status_code == 200)
    op_p_data = res.json()
    check("Operator payment has order ID", bool(op_p_data.get("cf_order_id")))

    # 6.4 Payment History Query
    res = client.get("/api/payments/history?payer_id=14&payer_type=driver")
    check("GET /api/payments/history for driver returns 200", res.status_code == 200)
    check("Driver payment history has records", res.json().get("count", 0) >= 1)

    # 6.5 Webhook HMAC Verification
    res = client.post("/api/payments/webhook/cashfree", json={
        "order": {"order_id": p_data.get("cf_order_id")},
        "payment": {"payment_status": "SUCCESS"}
    })
    check("Webhook rejects unsigned payload with 400", res.status_code == 400)

    import time, hmac, hashlib, base64, json as py_json
    from app.config import settings
    webhook_payload = {
        "order": {"order_id": p_data.get("cf_order_id")},
        "payment": {"payment_status": "SUCCESS", "cf_payment_id": "cf_test_pay_123", "payment_group": "upi", "payment_amount": 500.0}
    }
    raw_payload = py_json.dumps(webhook_payload)
    ts = str(int(time.time()))
    data_to_sign = ts + raw_payload
    sig = base64.b64encode(
        hmac.new(settings.CASHFREE_SECRET_KEY.encode("utf-8"), data_to_sign.encode("utf-8"), hashlib.sha256).digest()
    ).decode("utf-8")

    res = client.post(
        "/api/payments/webhook/cashfree",
        content=raw_payload,
        headers={
            "Content-Type": "application/json",
            "x-webhook-signature": sig,
            "x-webhook-timestamp": ts
        }
    )
    check("Webhook accepts cryptographically signed payload with 200", res.status_code == 200)

    # 6.6 Verification of Driver Payment Cascade Logic (_apply_payment_success)
    # Test partial pay, full pay, and advance surplus pay on independent driver models
    from app.models.app_models import AppDrivers, AppHisaabs, AppOperators, AppPayments
    from app.api.payments import _apply_payment_success
    from app.database import SessionLocal

    db_sess = SessionLocal()
    try:
        import uuid
        rand_suffix = uuid.uuid4().hex[:6]
        test_d = AppDrivers(
            driver_id=int(f"99{int(rand_suffix[:4], 16) % 1000:03d}"),
            full_name="AUDIT TEST DRIVER",
            phone=f"99{rand_suffix[:8]}",
            operator_id=0,
            cw_to_collect=1500.0,
            cw_os=1500.0,
            deposit_paid=5000.0,
            deposit_pending=1000.0,
            deposit_total_req=6000.0
        )
        db_sess.add(test_d)
        db_sess.flush()

        from datetime import date
        test_h = AppHisaabs(
            app_driver_id=test_d.app_driver_id,
            app_operator_id=0,
            hisaab_number=f"HS-AUD-{rand_suffix[:6]}",
            week_number=40,
            period_start=date(2026, 9, 28),
            period_end=date(2026, 10, 4),
            weekly_hisaab_due=1500.0,
            to_collect=1500.0,
            current_period_os=1500.0,
            paid_amount=0.0,
            payment_status="unpaid"
        )
        db_sess.add(test_h)
        db_sess.flush()

        # Step A: Partial payment of 500 on 1500 due
        p_partial = AppPayments(
            amount=500.0,
            payer_type="driver",
            payer_id=test_d.app_driver_id,
            app_hisaab_id=test_h.app_hisaab_id,
            status="SUCCESS"
        )
        _apply_payment_success(p_partial, db_sess)
        check("Partial pay updates paid_amount to 500", test_h.paid_amount == 500.0)
        check("Partial pay updates hisaab to_collect to 1000", test_h.to_collect == 1000.0)
        check("Partial pay updates hisaab current_period_os to 1000", test_h.current_period_os == 1000.0)
        check("Partial pay updates driver cw_to_collect to 1000", test_d.cw_to_collect == 1000.0)
        check("Partial pay sets status to partial", test_h.payment_status == "partial")

        # Step B: Full pay remainder (1000)
        p_full = AppPayments(
            amount=1000.0,
            payer_type="driver",
            payer_id=test_d.app_driver_id,
            app_hisaab_id=test_h.app_hisaab_id,
            status="SUCCESS"
        )
        _apply_payment_success(p_full, db_sess)
        check("Full pay settles hisaab paid_amount to 1500", test_h.paid_amount == 1500.0)
        check("Full pay hisaab to_collect is 0", test_h.to_collect == 0.0)
        check("Full pay driver cw_to_collect is 0", test_d.cw_to_collect == 0.0)
        check("Full pay sets status to settled", test_h.payment_status == "settled")

        # Step C: Advance surplus payment (2500) -> 1000 to deposit, 1500 to surplus advance credit
        p_surplus = AppPayments(
            amount=2500.0,
            payer_type="driver",
            payer_id=test_d.app_driver_id,
            app_hisaab_id=test_h.app_hisaab_id,
            status="SUCCESS"
        )
        _apply_payment_success(p_surplus, db_sess)
        check("Surplus pay fully clears deposit_pending to 0", test_d.deposit_pending == 0.0)
        check("Surplus pay updates deposit_paid to 6000", test_d.deposit_paid == 6000.0)
        check("Surplus pay creates advance credit cw_to_pay of 1500", test_d.cw_to_pay == 1500.0)
        check("Surplus pay sets negative cw_os of -1500", test_d.cw_os == -1500.0)

        # 6.7 Verification of Operator 3-Tier Cascade Logic
        op_suf = uuid.uuid4().hex[:6]
        test_op = AppOperators(
            operator_id=int(f"98{int(op_suf[:4], 16) % 1000:03d}"),
            operator_code=f"OP-{op_suf[:4].upper()}",
            company_name="AUDIT FLEET OP",
            phone=f"88{op_suf[:8]}",
            cw_to_collect=1800.0,
            deposit_paid=15000.0,
            deposit_pending=5000.0,
            deposit_total_req=20000.0
        )
        db_sess.add(test_op)
        db_sess.flush()

        fleet_d1 = AppDrivers(
            driver_id=int(f"97{int(op_suf[:4], 16) % 1000:03d}"),
            full_name="FLEET DRIVER 1",
            phone=f"87{op_suf[:8]}",
            operator_id=test_op.app_operator_id,
            cw_to_collect=1000.0,
            cw_os=1000.0
        )
        fleet_d2 = AppDrivers(
            driver_id=int(f"96{int(op_suf[:4], 16) % 1000:03d}"),
            full_name="FLEET DRIVER 2",
            phone=f"86{op_suf[:8]}",
            operator_id=test_op.app_operator_id,
            cw_to_collect=800.0,
            cw_os=800.0
        )
        db_sess.add_all([fleet_d1, fleet_d2])
        db_sess.flush()

        fleet_h1 = AppHisaabs(
            app_driver_id=fleet_d1.app_driver_id,
            app_operator_id=test_op.app_operator_id,
            hisaab_number=f"HS-F1-{op_suf[:6]}",
            week_number=40,
            period_start=date(2026, 9, 28),
            period_end=date(2026, 10, 4),
            weekly_hisaab_due=1000.0,
            to_collect=1000.0,
            current_period_os=1000.0,
            paid_amount=0.0
        )
        fleet_h2 = AppHisaabs(
            app_driver_id=fleet_d2.app_driver_id,
            app_operator_id=test_op.app_operator_id,
            hisaab_number=f"HS-F2-{op_suf[:6]}",
            week_number=40,
            period_start=date(2026, 9, 28),
            period_end=date(2026, 10, 4),
            weekly_hisaab_due=800.0,
            to_collect=800.0,
            current_period_os=800.0,
            paid_amount=0.0
        )
        db_sess.add_all([fleet_h1, fleet_h2])
        db_sess.flush()

        # Operator pays 8800 (1800 clears Tier 1 driver debt, 5000 clears Tier 2 deposit, 2000 to Tier 3 cw_to_pay)
        p_op = AppPayments(
            amount=8800.0,
            payer_type="operator",
            payer_id=test_op.app_operator_id,
            status="SUCCESS"
        )
        _apply_payment_success(p_op, db_sess)
        check("Operator cascade Tier 1 clears fleet_d1 debt", fleet_d1.cw_to_collect == 0.0)
        check("Operator cascade Tier 1 clears fleet_d2 debt", fleet_d2.cw_to_collect == 0.0)
        check("Operator cascade Tier 1 marks fleet_h1 settled", fleet_h1.payment_status == "settled")
        check("Operator cascade Tier 1 marks fleet_h2 settled", fleet_h2.payment_status == "settled")
        check("Operator cascade Tier 1 clears op cw_to_collect", test_op.cw_to_collect == 0.0)
        check("Operator cascade Tier 2 clears op deposit_pending", test_op.deposit_pending == 0.0)
        check("Operator cascade Tier 2 increases op deposit_paid to 20000", test_op.deposit_paid == 20000.0)
        check("Operator cascade Tier 3 deposits 2000 into op cw_to_pay credit", test_op.cw_to_pay == 2000.0)

    finally:
        db_sess.rollback()
        db_sess.close()

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
