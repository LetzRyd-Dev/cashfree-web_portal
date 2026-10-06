"""
test_backend_fixes.py — Comprehensive Verification Suite for Backend Fixes:
1. Cross-Tenant Security Isolation Fix (operators.py)
2. Hisaab Overcounting in Fleet Summary (operators.py)
3. Remove Hardcoded Vehicle Fallback (drivers.py & operators.py)
4. Enhance Resolvers (helpers.py)
5. Support String Ticket IDs (tickets.py)
"""
import sys
from fastapi.testclient import TestClient
from app.main import app
from app.database import engine
from sqlalchemy.orm import Session
from app.services.helpers import resolve_driver, resolve_operator
from app.models.app_models import AppDrivers, AppOperators, AppHisaabs, AppSupportTickets

client = TestClient(app)

passed = 0
failed = 0
errors = []

def check(name: str, condition: bool, details: str = ""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        msg = f"  [FAIL] {name} - {details}"
        print(msg)
        errors.append(msg)

def run_tests():
    print("=" * 80)
    print("BACKEND FIXES VERIFICATION TEST SUITE")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # TEST SUITE 1: Cross-Tenant Security Isolation Fix
    # -------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print(" 1. CROSS-TENANT SECURITY ISOLATION VERIFICATION (Operator 940 vs Operator 1)")
    print("=" * 70)

    # 1.1 Fleet summary for Operator 940
    res_940_fleet = client.get("/api/operators/940/fleet-summary")
    check("GET /api/operators/940/fleet-summary returns 200", res_940_fleet.status_code == 200, f"Status: {res_940_fleet.status_code}")
    data_940_fleet = res_940_fleet.json()
    check("Operator 940 total_drivers == 0", data_940_fleet.get("total_drivers") == 0, f"Got: {data_940_fleet.get('total_drivers')}")
    check("Operator 940 vehicles count == 0", len(data_940_fleet.get("vehicles", [])) == 0, f"Got: {len(data_940_fleet.get('vehicles', []))}")
    driver_ids_940 = [v.get("driver_id") for v in data_940_fleet.get("vehicles", [])]
    check("Operator 940 does NOT see Driver 1 (Vivek)", 1 not in driver_ids_940, f"Drivers: {driver_ids_940}")
    check("Operator 940 does NOT see Driver 2 (Sushant)", 2 not in driver_ids_940, f"Drivers: {driver_ids_940}")
    check("Operator 940 does NOT see Driver 3 (Aayush)", 3 not in driver_ids_940, f"Drivers: {driver_ids_940}")
    check("Operator 940 does NOT see Driver 4 (Anurag Driver)", 4 not in driver_ids_940, f"Drivers: {driver_ids_940}")

    # 1.2 Profile for Operator 940 (_map_operator)
    res_940_profile = client.get("/api/operators/940")
    check("GET /api/operators/940 returns 200", res_940_profile.status_code == 200, f"Status: {res_940_profile.status_code}")
    data_940_profile = res_940_profile.json()
    check("Operator 940 profile total_drivers == 0", data_940_profile.get("total_drivers") == 0, f"Got: {data_940_profile.get('total_drivers')}")
    check("Operator 940 profile total_vehicles == 0", data_940_profile.get("total_vehicles") == 0, f"Got: {data_940_profile.get('total_vehicles')}")

    # 1.3 Operator 1 fleet summary isolation verification
    res_1_fleet = client.get("/api/operators/1/fleet-summary")
    check("GET /api/operators/1/fleet-summary returns 200", res_1_fleet.status_code == 200, f"Status: {res_1_fleet.status_code}")
    data_1_fleet = res_1_fleet.json()
    check("Operator 1 sees exactly 4 fleet drivers", data_1_fleet.get("total_drivers") == 4, f"Got: {data_1_fleet.get('total_drivers')}")
    check("Operator 1 vehicles list length is 4", len(data_1_fleet.get("vehicles", [])) == 4, f"Got: {len(data_1_fleet.get('vehicles', []))}")
    driver_names_1 = [v.get("driver_name") for v in data_1_fleet.get("vehicles", [])]
    check("Operator 1 drivers include Vivek", "Vivek" in driver_names_1, f"Names: {driver_names_1}")
    check("Operator 1 drivers include Sushant", "Sushant" in driver_names_1, f"Names: {driver_names_1}")
    check("Operator 1 drivers include Aayush", "Aayush" in driver_names_1, f"Names: {driver_names_1}")
    check("Operator 1 drivers include Anurag Driver", "Anurag Driver" in driver_names_1, f"Names: {driver_names_1}")

    # -------------------------------------------------------------------------
    # TEST SUITE 2: Hisaab Overcounting in Fleet Summary Fix
    # -------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print(" 2. HISAAB OVERCOUNTING FIX IN FLEET SUMMARY")
    print("=" * 70)
    # Check each driver's hisaab_count in Operator 1 fleet summary
    vehicles_1 = {v["driver_id"]: v for v in data_1_fleet.get("vehicles", [])}
    
    check("Driver 1 (Vivek) hisaab_count == 3 (NOT overcounted to 13)", vehicles_1.get(1, {}).get("hisaab_count") == 3, f"Got: {vehicles_1.get(1, {}).get('hisaab_count')}")
    check("Driver 2 (Sushant) hisaab_count == 3 (NOT overcounted to 13)", vehicles_1.get(2, {}).get("hisaab_count") == 3, f"Got: {vehicles_1.get(2, {}).get('hisaab_count')}")
    check("Driver 3 (Aayush) hisaab_count == 3 (NOT overcounted to 13)", vehicles_1.get(3, {}).get("hisaab_count") == 3, f"Got: {vehicles_1.get(3, {}).get('hisaab_count')}")
    check("Driver 4 (Anurag Driver) hisaab_count == 3 (NOT overcounted to 19)", vehicles_1.get(4, {}).get("hisaab_count") == 3, f"Got: {vehicles_1.get(4, {}).get('hisaab_count')}")

    # -------------------------------------------------------------------------
    # TEST SUITE 3: Remove Hardcoded Vehicle Fallback
    # -------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print(" 3. REMOVE HARDCODED VEHICLE FALLBACK ('KA05AQ7692', 'Maruti', 'Dzire CNG')")
    print("=" * 70)
    # 3.1 Driver 2024 has NO vehicle in DB
    res_no_veh = client.get("/api/drivers/2024")
    check("GET /api/drivers/2024 returns 200", res_no_veh.status_code == 200, f"Status: {res_no_veh.status_code}")
    d_no_veh = res_no_veh.json()
    check("Driver 2024 vehicle_reg_number is None (not hardcoded 'KA05AQ7692')", d_no_veh.get("vehicle_reg_number") is None, f"Got: {d_no_veh.get('vehicle_reg_number')}")
    check("Driver 2024 vehicle_make is None (not hardcoded 'Maruti')", d_no_veh.get("vehicle_make") is None, f"Got: {d_no_veh.get('vehicle_make')}")
    check("Driver 2024 vehicle_model is None (not hardcoded 'Dzire CNG')", d_no_veh.get("vehicle_model") is None, f"Got: {d_no_veh.get('vehicle_model')}")
    check("Driver 2024 vehicle_variant is None (not hardcoded 'VXi')", d_no_veh.get("vehicle_variant") is None, f"Got: {d_no_veh.get('vehicle_variant')}")
    check("Driver 2024 vehicle_year is None (not hardcoded 2021)", d_no_veh.get("vehicle_year") is None, f"Got: {d_no_veh.get('vehicle_year')}")

    # 3.2 Another driver with no vehicle: 1789
    res_1789 = client.get("/api/drivers/1789")
    check("GET /api/drivers/1789 returns 200", res_1789.status_code == 200, f"Status: {res_1789.status_code}")
    d_1789 = res_1789.json()
    check("Driver 1789 vehicle_reg_number is None", d_1789.get("vehicle_reg_number") is None, f"Got: {d_1789.get('vehicle_reg_number')}")

    # 3.3 Driver 1 (Vivek) legitimately HAS KA05AQ7692
    res_d1 = client.get("/api/drivers/1")
    check("GET /api/drivers/1 returns 200", res_d1.status_code == 200, f"Status: {res_d1.status_code}")
    d1 = res_d1.json()
    check("Driver 1 preserves legitimate vehicle KA05AQ7692", d1.get("vehicle_reg_number") == "KA05AQ7692", f"Got: {d1.get('vehicle_reg_number')}")
    check("Driver 1 preserves legitimate make Maruti", d1.get("vehicle_make") == "Maruti", f"Got: {d1.get('vehicle_make')}")
    check("Driver 1 preserves legitimate model Dzire CNG", d1.get("vehicle_model") == "Dzire CNG", f"Got: {d1.get('vehicle_model')}")

    # -------------------------------------------------------------------------
    # TEST SUITE 4: Enhanced Resolvers (driver_code, operator_code, prefix strip)
    # -------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print(" 4. ENHANCED RESOLVERS (helpers.py & API Endpoints)")
    print("=" * 70)
    with Session(engine) as db:
        # 4.1 resolve_driver direct checks
        d_by_code1 = resolve_driver("LETZBLR6362111715", db)
        check("resolve_driver by code 'LETZBLR6362111715'", d_by_code1 is not None and d_by_code1.app_driver_id == 110)

        d_by_code2 = resolve_driver("DRV-AL-777", db)
        check("resolve_driver by code 'DRV-AL-777'", d_by_code2 is not None and d_by_code2.app_driver_id == 5287)

        d_by_code3 = resolve_driver("LR-DRV-0418", db)
        check("resolve_driver by code 'LR-DRV-0418'", d_by_code3 is not None and d_by_code3.app_driver_id == 5)

        d_strip1 = resolve_driver("LR-DRV-1", db)
        check("resolve_driver by prefix strip 'LR-DRV-1'", d_strip1 is not None and d_strip1.app_driver_id == 1)

        d_strip2 = resolve_driver("DRV-1", db)
        check("resolve_driver by prefix strip 'DRV-1'", d_strip2 is not None and d_strip2.app_driver_id == 1)

        d_strip3 = resolve_driver("LR-DRV-202", db)
        check("resolve_driver by prefix strip 'LR-DRV-202' (legacy ID 202)", d_strip3 is not None and d_strip3.app_driver_id == 2)

        # 4.2 resolve_operator direct checks
        op_by_code1 = resolve_operator("OPR-HYD-001", db)
        check("resolve_operator by code 'OPR-HYD-001'", op_by_code1 is not None and op_by_code1.app_operator_id == 1)

        op_by_code2 = resolve_operator("OP-501", db)
        check("resolve_operator by code 'OP-501'", op_by_code2 is not None and op_by_code2.operator_code == "OP-501")

        op_by_code3 = resolve_operator("LETZHYDIP6301750940", db)
        check("resolve_operator by code 'LETZHYDIP6301750940'", op_by_code3 is not None and op_by_code3.app_operator_id == 21)

        op_strip1 = resolve_operator("LR-OP-1", db)
        check("resolve_operator by prefix strip 'LR-OP-1'", op_strip1 is not None and op_strip1.app_operator_id == 1)

        op_strip2 = resolve_operator("OPR-1", db)
        check("resolve_operator by prefix strip 'OPR-1'", op_strip2 is not None and op_strip2.app_operator_id == 1)

        op_strip3 = resolve_operator("LR-OP-940", db)
        check("resolve_operator by prefix strip 'LR-OP-940'", op_strip3 is not None and op_strip3.app_operator_id == 940)

        op_strip4 = resolve_operator("OPR-940", db)
        check("resolve_operator by prefix strip 'OPR-940'", op_strip4 is not None and op_strip4.app_operator_id == 940)

    # 4.3 API Endpoints with Codes and Prefixes
    res = client.get("/api/drivers/DRV-AL-777")
    check("GET /api/drivers/DRV-AL-777 returns 200", res.status_code == 200, f"Status: {res.status_code}")
    check("Driver resolved is Alloc Test Driver", res.json().get("full_name") == "Alloc Test Driver")

    res = client.get("/api/drivers/LR-DRV-0418")
    check("GET /api/drivers/LR-DRV-0418 returns 200", res.status_code == 200, f"Status: {res.status_code}")
    check("Driver resolved is Mohammed Ali", res.json().get("full_name") == "Mohammed Ali")

    res = client.get("/api/drivers/LR-DRV-1")
    check("GET /api/drivers/LR-DRV-1 returns 200", res.status_code == 200, f"Status: {res.status_code}")
    check("Driver resolved is Vivek", res.json().get("full_name") == "Vivek")

    res = client.get("/api/operators/OPR-HYD-001")
    check("GET /api/operators/OPR-HYD-001 returns 200", res.status_code == 200, f"Status: {res.status_code}")
    check("Operator resolved is Anurag & RK Fleet", "Anurag" in res.json().get("company_name", ""))

    res = client.get("/api/operators/OPR-HYD-001/fleet-summary")
    check("GET /api/operators/OPR-HYD-001/fleet-summary returns 200", res.status_code == 200, f"Status: {res.status_code}")
    check("Fleet summary has 4 drivers", res.json().get("total_drivers") == 4)

    res = client.get("/api/operators/LR-OP-940/fleet-summary")
    check("GET /api/operators/LR-OP-940/fleet-summary returns 200", res.status_code == 200, f"Status: {res.status_code}")
    check("Fleet summary for 940 has 0 drivers", res.json().get("total_drivers") == 0)

    # -------------------------------------------------------------------------
    # TEST SUITE 5: Support String Ticket IDs (tickets.py)
    # -------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print(" 5. SUPPORT STRING TICKET IDS (tickets.py)")
    print("=" * 70)

    # 5.1 Create a ticket to obtain ticket_number and app_ticket_id
    ticket_payload = {
        "creator_type": "driver",
        "creator_id": 1,
        "category": "Vehicle Maintenance",
        "subject": "Engine Oil Replacement Needed",
        "description": "Vehicle requires immediate engine oil maintenance check.",
        "priority": "high"
    }
    create_res = client.post("/api/tickets", json=ticket_payload)
    check("POST /api/tickets returns 200", create_res.status_code == 200, f"Status: {create_res.status_code}")
    tkt_data = create_res.json()
    tkt_num = tkt_data.get("ticket_number")
    tkt_id = tkt_data.get("app_ticket_id")
    check("Ticket has valid ticket_number", bool(tkt_num) and tkt_num.startswith("TKT-"), f"Got: {tkt_num}")
    check("Ticket has valid app_ticket_id", bool(tkt_id) and tkt_id > 0, f"Got: {tkt_id}")

    # 5.2 Fetch ticket by string ticket_number
    res_get_str = client.get(f"/api/tickets/{tkt_num}")
    check(f"GET /api/tickets/{tkt_num} (string number) returns 200", res_get_str.status_code == 200, f"Status: {res_get_str.status_code}")
    check("Fetched ticket matches ticket_number", res_get_str.json().get("ticket_number") == tkt_num)

    # 5.3 Fetch ticket by integer id
    res_get_int = client.get(f"/api/tickets/{tkt_id}")
    check(f"GET /api/tickets/{tkt_id} (numeric id) returns 200", res_get_int.status_code == 200, f"Status: {res_get_int.status_code}")
    check("Fetched ticket matches app_ticket_id", res_get_int.json().get("app_ticket_id") == tkt_id)

    # 5.4 Fetch ticket by string with stripped prefix (e.g. "2026-...")
    tkt_num_stripped = tkt_num[4:] if tkt_num.startswith("TKT-") else tkt_num
    res_get_stripped = client.get(f"/api/tickets/{tkt_num_stripped}")
    check(f"GET /api/tickets/{tkt_num_stripped} (prefix stripped) returns 200", res_get_stripped.status_code == 200, f"Status: {res_get_stripped.status_code}")

    # 5.5 Update status using full string ticket_number (PATCH /{ticket_id}/status)
    res_patch_str = client.patch(f"/api/tickets/{tkt_num}/status", json={"status": "in_progress", "resolution_note": "Assigned technician"})
    check(f"PATCH /api/tickets/{tkt_num}/status (string) returns 200", res_patch_str.status_code == 200, f"Status: {res_patch_str.status_code}")
    check("Ticket status updated to 'in_progress'", res_patch_str.json().get("status") == "in_progress")

    # 5.6 Update status using stripped string ticket_number (PUT /{ticket_id}/status)
    res_put_stripped = client.put(f"/api/tickets/{tkt_num_stripped}/status", json={"status": "resolved", "resolution_note": "Oil replaced"})
    check(f"PUT /api/tickets/{tkt_num_stripped}/status (prefix stripped string) returns 200", res_put_stripped.status_code == 200, f"Status: {res_put_stripped.status_code}")
    check("Ticket status updated to 'resolved'", res_put_stripped.json().get("status") == "resolved")
    check("Ticket has resolved_at set", bool(res_put_stripped.json().get("resolved_at")))

    # 5.7 Update status using numeric app_ticket_id (PATCH /{ticket_id})
    res_patch_int = client.patch(f"/api/tickets/{tkt_id}", json={"status": "closed", "resolution_note": "Work order verified"})
    check(f"PATCH /api/tickets/{tkt_id} (numeric id) returns 200", res_patch_int.status_code == 200, f"Status: {res_patch_int.status_code}")
    check("Ticket status updated to 'closed'", res_patch_int.json().get("status") == "closed")

    # 5.8 Update non-existent ticket -> 404
    res_404 = client.patch("/api/tickets/TKT-INVALID-99999/status", json={"status": "closed"})
    check("PATCH /api/tickets/TKT-INVALID-99999/status returns 404", res_404.status_code == 404)

    # 5.9 List tickets with string creator_id
    res_list_str = client.get("/api/tickets?creator_id=LR-DRV-1&creator_type=driver")
    check("GET /api/tickets?creator_id=LR-DRV-1 returns 200", res_list_str.status_code == 200)
    check("Ticket list contains created ticket", any(t["ticket_number"] == tkt_num for t in res_list_str.json().get("data", [])))

    # -------------------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print(f"VERIFICATION RESULTS: {passed} PASSED, {failed} FAILED")
    print("=" * 80)
    if errors:
        print("\nFailures:")
        for err in errors:
            print(err)
        sys.exit(1)
    else:
        print("\nALL BACKEND FIXES VERIFIED SUCCESSFULLY AND WORKING CORRECTLY!")

if __name__ == "__main__":
    run_tests()
