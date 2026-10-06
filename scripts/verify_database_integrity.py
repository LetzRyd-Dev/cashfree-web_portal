"""
Comprehensive Database Integrity Verification Script for LetzRyd cashfree-web_portal
Author: Subagent 1 (Database Integrity & Data Synchronization Agent)
Target DB: PostgreSQL at 35.200.196.113:5432/postgres
"""

import sys
from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

def run_verification():
    passed = 0
    failed = 0
    total_checks = 0

    def check(name, condition, details=""):
        nonlocal passed, failed, total_checks
        total_checks += 1
        if condition:
            passed += 1
            print(f"  [PASS] {name}")
            if details:
                print(f"         -> {details}")
        else:
            failed += 1
            print(f"  [FAIL] {name}")
            if details:
                print(f"         -> {details}")

    print("=" * 80)
    print("RUNNING SUBAGENT 1 COMPREHENSIVE VERIFICATION SUITE")
    print("=" * 80)

    with engine.connect() as conn:
        # ----------------------------------------------------------------------
        # 1. VERIFY DRIVERS VEHICLE REG & SPECS SYNC
        # ----------------------------------------------------------------------
        print("\n--- 1. VERIFY DRIVERS VEHICLE REG & SPECS SYNC ---")
        
        # Check active drivers with active allocations missing vehicle_reg_number
        active_alloc_missing = conn.execute(text("""
            SELECT count(*) 
            FROM app_drivers d 
            JOIN app_driver_allocations a ON d.app_driver_id = a.app_driver_id 
            WHERE a.allocation_status = 'ACTIVE' 
              AND (d.vehicle_reg_number IS NULL OR d.vehicle_reg_number = '')
              AND d.is_active = TRUE;
        """)).scalar()
        check(
            "Active drivers with active allocations missing vehicle_reg_number == 0",
            active_alloc_missing == 0,
            f"Missing count: {active_alloc_missing}"
        )

        # Check total drivers with vehicle_reg_number populated
        drvs_with_veh = conn.execute(text("""
            SELECT count(*) FROM app_drivers WHERE vehicle_reg_number IS NOT NULL AND vehicle_reg_number != ''
        """)).scalar()
        check(
            "Total drivers with populated vehicle_reg_number >= 2280",
            drvs_with_veh >= 2280,
            f"Total drivers with vehicle: {drvs_with_veh}"
        )

        # Check that vehicle specs are NOT NULL where vehicle_reg_number is populated
        missing_specs = conn.execute(text("""
            SELECT count(*) 
            FROM app_drivers 
            WHERE vehicle_reg_number IS NOT NULL AND vehicle_reg_number != ''
              AND (
                  vehicle_make IS NULL OR vehicle_make = ''
                  OR vehicle_model IS NULL OR vehicle_model = ''
                  OR vehicle_variant IS NULL OR vehicle_variant = ''
                  OR vehicle_daily_rate IS NULL
                  OR vehicle_allocated_from IS NULL
              );
        """)).scalar()
        check(
            "Drivers with vehicle having complete specs (make, model, variant, rate, date) with 0 nulls",
            missing_specs == 0,
            f"Incomplete specs count: {missing_specs}"
        )

        # Check sample synced driver
        sample_synced = conn.execute(text("""
            SELECT app_driver_id, full_name, vehicle_reg_number, vehicle_make, vehicle_model, vehicle_variant, vehicle_daily_rate, vehicle_allocated_from
            FROM app_drivers 
            WHERE vehicle_reg_number IS NOT NULL
            ORDER BY last_synced_at DESC NULLS LAST
            LIMIT 3;
        """)).fetchall()
        for s in sample_synced:
            print(f"         Sample synced: ID={s[0]} ({s[1]}): Reg={s[2]}, Make={s[3]}, Model={s[4]}, Variant={s[5]}, Rate={s[6]}, Date={s[7]}")

        # ----------------------------------------------------------------------
        # 2. VERIFY MANAGERS & HUB CONTACTS POPULATION
        # ----------------------------------------------------------------------
        print("\n--- 2. VERIFY MANAGERS & HUB CONTACTS POPULATION ---")

        # 2A. app_driver_allocations assigned_manager and assigned_hub
        alloc_mgr_stats = conn.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(assigned_manager) as with_mgr,
                COUNT(assigned_hub) as with_hub,
                COUNT(CASE WHEN assigned_manager IS NULL OR assigned_manager = '' THEN 1 END) as empty_mgr,
                COUNT(CASE WHEN assigned_hub IS NULL OR assigned_hub = '' THEN 1 END) as empty_hub
            FROM app_driver_allocations;
        """)).mappings().first()
        check(
            f"app_driver_allocations: All {alloc_mgr_stats['total']} rows have assigned_manager populated (0 empty)",
            alloc_mgr_stats['empty_mgr'] == 0 and alloc_mgr_stats['with_mgr'] >= 7941,
            f"Total: {alloc_mgr_stats['total']}, With Manager: {alloc_mgr_stats['with_mgr']}, Empty: {alloc_mgr_stats['empty_mgr']}"
        )
        check(
            f"app_driver_allocations: All {alloc_mgr_stats['total']} rows have assigned_hub populated (0 empty)",
            alloc_mgr_stats['empty_hub'] == 0 and alloc_mgr_stats['with_hub'] >= 7941,
            f"Total: {alloc_mgr_stats['total']}, With Hub: {alloc_mgr_stats['with_hub']}, Empty: {alloc_mgr_stats['empty_hub']}"
        )

        # 2B. app_drivers assigned_manager_name and phone
        drv_mgr_stats = conn.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN assigned_manager_name IS NULL OR assigned_manager_name = '' THEN 1 END) as empty_mgr_name,
                COUNT(CASE WHEN assigned_manager_phone IS NULL OR assigned_manager_phone = '' THEN 1 END) as empty_mgr_phone,
                COUNT(CASE WHEN assigned_manager_name = 'LetzRyd Fleet Operations' THEN 1 END) as placeholder_mgr_name,
                COUNT(CASE WHEN assigned_manager_phone = '080-4568-1234' THEN 1 END) as placeholder_mgr_phone
            FROM app_drivers
            WHERE is_active = TRUE;
        """)).mappings().first()
        check(
            "app_drivers (active): 0 drivers with empty manager name",
            drv_mgr_stats['empty_mgr_name'] == 0,
            f"Empty manager names: {drv_mgr_stats['empty_mgr_name']}"
        )
        check(
            "app_drivers (active): 0 drivers with empty manager phone",
            drv_mgr_stats['empty_mgr_phone'] == 0,
            f"Empty manager phones: {drv_mgr_stats['empty_mgr_phone']}"
        )
        check(
            "app_drivers (active): 0 drivers with 'LetzRyd Fleet Operations' placeholder",
            drv_mgr_stats['placeholder_mgr_name'] == 0,
            f"Placeholder manager count: {drv_mgr_stats['placeholder_mgr_name']}"
        )
        check(
            "app_drivers (active): 0 drivers with '080-4568-1234' placeholder phone",
            drv_mgr_stats['placeholder_mgr_phone'] == 0,
            f"Placeholder phone count: {drv_mgr_stats['placeholder_mgr_phone']}"
        )

        # Print distinct managers among drivers
        top_drv_mgrs = conn.execute(text("""
            SELECT assigned_manager_name, assigned_manager_phone, count(*) 
            FROM app_drivers 
            WHERE is_active = TRUE
            GROUP BY assigned_manager_name, assigned_manager_phone
            ORDER BY count(*) DESC
            LIMIT 7;
        """)).fetchall()
        print("         Top driver managers:")
        for tm in top_drv_mgrs:
            print(f"           - {tm[0]} ({tm[1]}): {tm[2]} drivers")

        # ----------------------------------------------------------------------
        # 3. VERIFY OPERATOR OP-501 DEDUPLICATION
        # ----------------------------------------------------------------------
        print("\n--- 3. VERIFY OPERATOR OP-501 DEDUPLICATION ---")
        op_501_rows = conn.execute(text("""
            SELECT app_operator_id, operator_id, operator_code, company_name, phone
            FROM app_operators
            WHERE operator_code = 'OP-501' OR app_operator_id IN (2, 940)
            ORDER BY app_operator_id;
        """)).mappings().fetchall()
        for op in op_501_rows:
            print(f"         Operator: app_id={op['app_operator_id']}, op_id={op['operator_id']}, code={op['operator_code']}, company='{op['company_name']}'")

        sole_501 = conn.execute(text("SELECT app_operator_id FROM app_operators WHERE operator_code = 'OP-501'")).fetchall()
        check(
            "app_operator_id = 2 is the SOLE OP-501 operator",
            len(sole_501) == 1 and sole_501[0][0] == 2,
            f"Operators with code OP-501: {[r[0] for r in sole_501]}"
        )

        op_940 = conn.execute(text("SELECT operator_code, operator_id FROM app_operators WHERE app_operator_id = 940")).mappings().first()
        check(
            "app_operator_id = 940 updated to OP-501-TEST and operator_id = 940",
            op_940['operator_code'] == 'OP-501-TEST' and op_940['operator_id'] == 940,
            f"Operator 940 code: {op_940['operator_code']}, operator_id: {op_940['operator_id']}"
        )

        dup_op_codes = conn.execute(text("""
            SELECT operator_code, count(*) FROM app_operators GROUP BY operator_code HAVING count(*) > 1
        """)).fetchall()
        check(
            "0 duplicate operator codes exist across entire app_operators table",
            len(dup_op_codes) == 0,
            f"Duplicates found: {dup_op_codes}"
        )

        # ----------------------------------------------------------------------
        # 4. VERIFY ORPHANED PAYMENTS RESOLUTION
        # ----------------------------------------------------------------------
        print("\n--- 4. VERIFY ORPHANED PAYMENTS RESOLUTION ---")
        pmts = conn.execute(text("""
            SELECT app_payment_id, payer_type, payer_id, amount, status
            FROM app_payments
            WHERE app_payment_id IN (50, 51, 52, 53)
            ORDER BY app_payment_id;
        """)).mappings().fetchall()
        for p in pmts:
            print(f"         Payment {p['app_payment_id']}: payer_type={p['payer_type']}, payer_id={p['payer_id']}, amount={p['amount']}, status={p['status']}")

        all_742 = all(p['payer_id'] == 742 for p in pmts)
        check(
            "Payments 50, 51, 52, 53 all have payer_id = 742 (Rishad)",
            all_742 and len(pmts) == 4,
            f"Payer IDs: {[p['payer_id'] for p in pmts]}"
        )

        remaining_4068 = conn.execute(text("""
            SELECT count(*) FROM app_payments WHERE payer_id = 4068 AND payer_type = 'operator';
        """)).scalar()
        check(
            "0 orphaned payments with payer_id = 4068 remain",
            remaining_4068 == 0,
            f"Count remaining: {remaining_4068}"
        )

        # ----------------------------------------------------------------------
        # 5. VERIFY CLEAN TEST DRIVERS
        # ----------------------------------------------------------------------
        print("\n--- 5. VERIFY CLEAN TEST DRIVERS ---")
        test_ids = [393878, 393887, 393888, 393942, 393943, 393944, 393991, 393992, 393993]
        test_rows = conn.execute(text(f"""
            SELECT app_driver_id, driver_code, full_name, is_active
            FROM app_drivers
            WHERE app_driver_id IN ({','.join(map(str, test_ids))})
            ORDER BY app_driver_id;
        """)).mappings().fetchall()
        for tr in test_rows:
            print(f"         Test Driver {tr['app_driver_id']}: code={tr['driver_code']}, name='{tr['full_name']}', is_active={tr['is_active']}")

        all_clean_code = all(tr['driver_code'] == f"DRV-TEST-{tr['app_driver_id']}" for tr in test_rows)
        all_inactive = all(tr['is_active'] is False for tr in test_rows)
        check(
            "All specified test drivers have clean synthetic codes DRV-TEST-<id>",
            all_clean_code and len(test_rows) == 9,
            f"Codes match DRV-TEST-<id>: {all_clean_code}"
        )
        check(
            "All specified test drivers have is_active = FALSE",
            all_inactive and len(test_rows) == 9,
            f"All inactive: {all_inactive}"
        )

        null_driver_codes = conn.execute(text("""
            SELECT count(*) FROM app_drivers WHERE driver_code IS NULL OR driver_code = '';
        """)).scalar()
        check(
            "0 drivers in app_drivers have NULL or empty driver_code",
            null_driver_codes == 0,
            f"Empty driver codes count: {null_driver_codes}"
        )

    print("\n" + "=" * 80)
    print(f"VERIFICATION RESULTS: {passed} / {total_checks} CHECKS PASSED ({(passed/total_checks)*100:.1f}%)")
    if failed == 0:
        print("ALL DATABASE INTEGRITY CHECKS PASSED WITH ZERO ERRORS!")
    else:
        print(f"WARNING: {failed} CHECKS FAILED!")
    print("=" * 80)
    return failed == 0

if __name__ == '__main__':
    success = run_verification()
    sys.exit(0 if success else 1)
