import os
from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

def run_deep_audit():
    with engine.connect() as conn:
        print("="*60)
        print("1. DRIVERS WITH NULL/EMPTY DRIVER CODE OR PHONE")
        print("="*60)
        q = text("""
            SELECT app_driver_id, driver_id, full_name, phone, driver_code, operator_id, joined_date 
            FROM app_drivers 
            WHERE driver_code IS NULL OR driver_code = '' OR phone IS NULL OR phone = '';
        """)
        rows = conn.execute(q).fetchall()
        for r in rows:
            print(f"  app_driver_id={r[0]}, driver_id={r[1]}, name={r[2]}, phone={r[3]}, code={r[4]}, op_id={r[5]}")

        print("\n" + "="*60)
        print("2. DUPLICATE OPERATOR CODES")
        print("="*60)
        q_dup_op = text("""
            SELECT operator_code, count(*), array_agg(app_operator_id), array_agg(company_name), array_agg(phone)
            FROM app_operators 
            GROUP BY operator_code 
            HAVING count(*) > 1;
        """)
        dup_ops = conn.execute(q_dup_op).fetchall()
        for r in dup_ops:
            print(f"  Code: {r[0]}, Count: {r[1]}, IDs: {r[2]}, Names: {r[3]}, Phones: {r[4]}")

        print("\n" + "="*60)
        print("3. DRIVERS WITH NULL ASSIGNED MANAGER")
        print("="*60)
        q_null_mgr = text("""
            SELECT app_driver_id, full_name, phone, driver_code, operator_id 
            FROM app_drivers 
            WHERE assigned_manager_name IS NULL OR assigned_manager_phone IS NULL;
        """)
        null_mgrs = conn.execute(q_null_mgr).fetchall()
        for r in null_mgrs:
            print(f"  app_driver_id={r[0]}, name={r[1]}, phone={r[2]}, code={r[3]}, op_id={r[4]}")

        print("\n" + "="*60)
        print("4. SOURCE TABLES FOR MANAGER DETAILS")
        print("="*60)
        # Check july_form_onboarding
        q_onboarding_mgr = text("""
            SELECT driver_manager_id, driver_manager_name, count(*) 
            FROM july_form_onboarding 
            WHERE driver_manager_name IS NOT NULL 
            GROUP BY driver_manager_id, driver_manager_name 
            ORDER BY count(*) DESC 
            LIMIT 10;
        """)
        try:
            onb_mgrs = conn.execute(q_onboarding_mgr).fetchall()
            print("july_form_onboarding manager samples:")
            for r in onb_mgrs:
                print(f"  ID={r[0]}, Name={r[1]}, Count={r[2]}")
        except Exception as e:
            print(f"  july_form_onboarding query failed: {e}")

        # Check core_vehicle_allocation.vehicle_manager_poc
        q_alloc_poc = text("""
            SELECT vehicle_manager_poc, count(*) 
            FROM core_vehicle_allocation 
            WHERE vehicle_manager_poc IS NOT NULL AND vehicle_manager_poc != ''
            GROUP BY vehicle_manager_poc 
            ORDER BY count(*) DESC 
            LIMIT 10;
        """)
        try:
            alloc_pocs = conn.execute(q_alloc_poc).fetchall()
            print("\ncore_vehicle_allocation vehicle_manager_poc samples:")
            for r in alloc_pocs:
                print(f"  POC={r[0]}, Count={r[1]}")
        except Exception as e:
            print(f"  core_vehicle_allocation query failed: {e}")

        # Check july_employees
        q_emp = text("""
            SELECT employee_id, first_name, last_name, role_id, phone, department, city 
            FROM july_employees 
            LIMIT 10;
        """)
        try:
            emps = conn.execute(q_emp).fetchall()
            print("\njuly_employees samples:")
            for r in emps:
                print(f"  ID={r[0]}, Name={r[1]} {r[2]}, Role={r[3]}, Phone={r[4]}, Dept={r[5]}, City={r[6]}")
        except Exception as e:
            print(f"  july_employees query failed: {e}")

        # Check hubs_parking
        q_hubs = text("""
            SELECT id, hub_name, city_name, hub_manager, manager_phone 
            FROM hubs_parking 
            WHERE hub_manager IS NOT NULL 
            LIMIT 10;
        """)
        try:
            hubs = conn.execute(q_hubs).fetchall()
            print("\nhubs_parking manager samples:")
            for r in hubs:
                print(f"  Hub={r[1]} ({r[2]}), Manager={r[3]}, Phone={r[4]}")
        except Exception as e:
            print(f"  hubs_parking query failed: {e}")

        print("\n" + "="*60)
        print("5. VEHICLE REGISTRATION POPULATION IN APP_DRIVERS")
        print("="*60)
        # Check how many drivers have active allocations in core_vehicle_allocation vs app_driver_allocations
        q_drv_alloc_match = text("""
            SELECT 
                COUNT(d.app_driver_id) as total_drivers,
                COUNT(a.app_allocation_id) as matched_allocations,
                COUNT(DISTINCT a.vehicle_number) as distinct_vehicles
            FROM app_drivers d
            LEFT JOIN app_driver_allocations a ON d.app_driver_id = a.app_driver_id;
        """)
        alloc_match = conn.execute(q_drv_alloc_match).mappings().first()
        print(f"Driver to allocation join: {dict(alloc_match)}")

        # Check latest allocation per driver
        q_latest_alloc = text("""
            WITH latest_alloc AS (
                SELECT DISTINCT ON (app_driver_id) 
                    app_driver_id, vehicle_number, allocation_date, daily_rental_rate, assigned_hub, assigned_city
                FROM app_driver_allocations
                ORDER BY app_driver_id, allocation_date DESC, app_allocation_id DESC
            )
            SELECT count(*) FROM latest_alloc;
        """)
        latest_count = conn.execute(q_latest_alloc).scalar()
        print(f"Drivers with at least one allocation in app_driver_allocations: {latest_count} / 2578")

        print("\n" + "="*60)
        print("6. CHECKING VEHICLES TABLE")
        print("="*60)
        try:
            veh_cnt = conn.execute(text("SELECT count(*) FROM july_vehicles")).scalar()
            veh_cols = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'july_vehicles'")).fetchall()
            print(f"july_vehicles: {veh_cnt} rows, cols: {[c[0] for c in veh_cols]}")
        except Exception as e:
            print(f"july_vehicles failed: {e}")

        try:
            veh2_cnt = conn.execute(text("SELECT count(*) FROM vehicles")).scalar()
            veh2_cols = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'vehicles'")).fetchall()
            print(f"vehicles: {veh2_cnt} rows, cols: {[c[0] for c in veh2_cols]}")
        except Exception as e:
            print(f"vehicles failed: {e}")

        print("\n" + "="*60)
        print("7. CHECKING APP_HISAABS INTEGRITY")
        print("="*60)
        hisaab_stats = conn.execute(text("""
            SELECT 
                count(*) as total_hisaabs,
                count(distinct app_hisaab_id) as uniq_hisaab_ids,
                count(distinct hisaab_number) as uniq_hisaab_numbers,
                count(case when hisaab_number is null or hisaab_number = '' then 1 end) as empty_hisaab_numbers,
                count(distinct app_driver_id) as distinct_drivers,
                count(distinct app_operator_id) as distinct_operators
            FROM app_hisaabs;
        """)).mappings().first()
        print(f"app_hisaabs integrity: {dict(hisaab_stats)}")

if __name__ == '__main__':
    run_deep_audit()
