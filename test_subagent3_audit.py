# test_subagent3_audit.py
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.app_models import AppSupportTickets, AppNotifications, AppReferralLeads, AppDrivers, AppOperators

client = TestClient(app)
db = SessionLocal()

print("=== 1. AUDITING TICKETS ===")
# A. Listing tickets for nonexistent user or 0 tickets
res_empty = client.get("/api/tickets?creator_id=99999999")
assert res_empty.status_code == 200, f"Expected 200, got {res_empty.status_code}"
assert res_empty.json()["data"] == [], f"Expected empty list, got {res_empty.json()}"
print(f"Empty listing verified: status={res_empty.status_code}, data={res_empty.json()['data']}")

# B. Creating ticket as driver
res_tkt_drv = client.post("/api/tickets", json={
    "creator_type": "driver",
    "creator_id": 5,
    "category": "hisaab",
    "subject": "Driver Week 30 Discrepancy",
    "description": "My fuel deduction was miscalculated by 200.",
    "priority": "high"
})
assert res_tkt_drv.status_code == 200
tkt_drv = res_tkt_drv.json()
tkt_id = tkt_drv["app_ticket_id"]
print(f"Created driver ticket: id={tkt_id}, number={tkt_drv['ticket_number']}, status={tkt_drv['status']}")

# C. Creating ticket as operator
res_tkt_op = client.post("/api/tickets", json={
    "creator_type": "operator",
    "creator_id": 940,
    "category": "vehicle",
    "subject": "Operator Fleet Vehicle Inspection",
    "description": "Vehicle KA05AQ7692 requires fitness certificate renewal.",
    "priority": "medium"
})
assert res_tkt_op.status_code == 200
tkt_op = res_tkt_op.json()
print(f"Created op ticket: id={tkt_op['app_ticket_id']}, number={tkt_op['ticket_number']}, status={tkt_op['status']}")

# D. Status Transitions (open -> in_progress -> resolved -> open)
print("\nTesting Status Transitions:")
# 1. Transition to in_progress
res_prog = client.patch(f"/api/tickets/{tkt_id}/status", json={"status": "in_progress"})
assert res_prog.status_code == 200
print(f"Transition to in_progress: status={res_prog.json()['status']}, resolved_at={res_prog.json()['resolved_at']}")
assert res_prog.json()["status"] == "in_progress"

# 2. Transition to resolved with resolution note
res_res = client.patch(f"/api/tickets/{tkt_id}/status", json={
    "status": "resolved",
    "resolution_note": "Adjustment of Rs 200 credited in next payout."
})
assert res_res.status_code == 200
print(f"Transition to resolved: status={res_res.json()['status']}, resolved_at={res_res.json()['resolved_at']}, note={res_res.json()['resolution_note']}")
assert res_res.json()["status"] == "resolved"
assert res_res.json()["resolved_at"] is not None

# 3. Transition back to open
res_reopen = client.patch(f"/api/tickets/{tkt_id}/status", json={"status": "open"})
assert res_reopen.status_code == 200
print(f"Transition back to open: status={res_reopen.json()['status']}, resolved_at={res_reopen.json()['resolved_at']}")
assert res_reopen.json()["status"] == "open"
assert res_reopen.json()["resolved_at"] is None

print("\n=== 2. AUDITING NOTIFICATIONS ===")
# Ensure test notification exists for driver 5 and operator 940
now_notif_drv = AppNotifications(
    target_type="driver",
    target_id=5,
    notif_type="hisaab",
    severity="info",
    title="Week 31 Settlement Ready",
    message="Your statement for week 31 is now ready for review.",
    is_read=False
)
now_notif_op = AppNotifications(
    target_type="operator",
    target_id=940,
    notif_type="fleet",
    severity="warning",
    title="Vehicle Fitness Renewal Due",
    message="Vehicle KA05AQ7692 fitness expires in 7 days.",
    is_read=False
)
db.add(now_notif_drv)
db.add(now_notif_op)
db.commit()

# Test fetching for driver 5
res_notif_drv = client.get("/api/notifications?target_id=5&target_type=driver")
assert res_notif_drv.status_code == 200
print(f"Driver notifs fetched: count={len(res_notif_drv.json())}")
assert any(n["app_notif_id"] == now_notif_drv.app_notif_id for n in res_notif_drv.json())

# Test fetching for operator 940
res_notif_op = client.get("/api/notifications?target_id=940&target_type=operator")
assert res_notif_op.status_code == 200
print(f"Operator notifs fetched: count={len(res_notif_op.json())}")
assert any(n["app_notif_id"] == now_notif_op.app_notif_id for n in res_notif_op.json())

# Test marking notification as read via PUT and PATCH
res_read_put = client.put(f"/api/notifications/{now_notif_drv.app_notif_id}/read")
assert res_read_put.status_code == 200, f"PUT mark read failed: {res_read_put.text}"
print(f"PUT /api/notifications/{now_notif_drv.app_notif_id}/read: {res_read_put.json()}")

res_read_patch = client.patch(f"/api/notifications/{now_notif_op.app_notif_id}/read")
assert res_read_patch.status_code == 200, f"PATCH mark read failed: {res_read_patch.text}"
print(f"PATCH /api/notifications/{now_notif_op.app_notif_id}/read: {res_read_patch.json()}")

db.refresh(now_notif_drv)
db.refresh(now_notif_op)
assert now_notif_drv.is_read is True
assert now_notif_op.is_read is True
print("Both driver and operator notifications verified is_read=True in DB.")

print("\n=== 3. AUDITING REFERRALS ===")
# Submit referral for driver
res_ref_drv = client.post("/api/referrals", json={
    "referred_by_type": "driver",
    "referred_by_id": 5,
    "lead_name": "Test Driver Lead",
    "lead_phone": "9876543233"
})
assert res_ref_drv.status_code == 200
drv_ref_data = res_ref_drv.json()
print(f"Driver referral submitted: id={drv_ref_data['app_referral_id']}, reward={drv_ref_data['reward_amount']}")
assert drv_ref_data['reward_amount'] == 1000.0, f"Expected 1000.0, got {drv_ref_data['reward_amount']}"

# Submit referral for operator
res_ref_op = client.post("/api/referrals", json={
    "referred_by_type": "operator",
    "referred_by_id": 940,
    "lead_name": "Test Operator Lead",
    "lead_phone": "9876543244"
})
assert res_ref_op.status_code == 200
op_ref_data = res_ref_op.json()
print(f"Operator referral submitted: id={op_ref_data['app_referral_id']}, reward={op_ref_data['reward_amount']}")
assert op_ref_data['reward_amount'] == 2000.0, f"Expected 2000.0, got {op_ref_data['reward_amount']}"

print("\nALL BACKEND AUDIT CHECKS PASSED SUCCESSFULLY!")
db.close()
