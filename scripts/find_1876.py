from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    # Let's inspect the 1895 drivers
    q_drivers = """
        SELECT d.app_driver_id, d.driver_id, d.driver_code, d.full_name, d.phone, d.is_active,
               count(a.app_allocation_id) as total_allocs,
               max(a.allocation_date) as max_alloc_date,
               max(a.dropoff_date) as max_drop_date
        FROM app_drivers d
        JOIN app_driver_allocations a ON d.app_driver_id = a.app_driver_id
        WHERE d.vehicle_reg_number IS NULL
        GROUP BY d.app_driver_id, d.driver_id, d.driver_code, d.full_name, d.phone, d.is_active
    """
    rows = conn.execute(text(q_drivers)).fetchall()
    print(f"Total drivers with NULL vehicle_reg and allocations: {len(rows)}")

    # Check is_active
    active_count = sum(1 for r in rows if r[5] is True)
    inactive_count = sum(1 for r in rows if r[5] is False)
    none_active_count = sum(1 for r in rows if r[5] is None)
    print(f"Active: {active_count}, Inactive: {inactive_count}, None: {none_active_count}")

    # Check test driver IDs
    test_ids = {393878, 393887, 393888, 393942, 393943, 393944, 393991, 393992, 393993}
    test_in_rows = [r for r in rows if r[0] in test_ids or r[1] in test_ids]
    print(f"Test drivers in these rows: {len(test_in_rows)}")

    # What if we look at latest allocation vehicle_number? Are any vehicle numbers empty or test?
    q_latest_alloc = """
        SELECT DISTINCT ON (d.app_driver_id)
            d.app_driver_id, d.full_name, d.phone, d.is_active,
            a.app_allocation_id, a.vehicle_number, a.allocation_date, a.dropoff_date,
            a.daily_rental_rate, a.allocation_status,
            c.car_model, c.hub_name, c.vehicle_manager_poc, c.city
        FROM app_drivers d
        JOIN app_driver_allocations a ON d.app_driver_id = a.app_driver_id
        LEFT JOIN core_vehicle_allocation c ON a.core_allocation_id = c.id
        WHERE d.vehicle_reg_number IS NULL
        ORDER BY d.app_driver_id, a.allocation_date DESC, a.app_allocation_id DESC
    """
    latest_rows = conn.execute(text(q_latest_alloc)).fetchall()
    print(f"Latest alloc count: {len(latest_rows)}")

    # Check empty vehicle_number
    empty_veh = [r for r in latest_rows if not r[5] or r[5].strip() == '']
    print(f"Empty vehicle_number: {len(empty_veh)}")

    # Check distinct vehicle numbers
    vehs = set(r[5] for r in latest_rows if r[5])
    print(f"Distinct vehicle numbers across these latest allocations: {len(vehs)}")

    # Check if there are vehicles matching vehicles table or core_vehicle_onboarding
    v_in_onboarding = conn.execute(text("""
        WITH latest AS (
            SELECT DISTINCT ON (d.app_driver_id)
                d.app_driver_id, a.vehicle_number
            FROM app_drivers d
            JOIN app_driver_allocations a ON d.app_driver_id = a.app_driver_id
            WHERE d.vehicle_reg_number IS NULL
            ORDER BY d.app_driver_id, a.allocation_date DESC, a.app_allocation_id DESC
        )
        SELECT count(DISTINCT l.app_driver_id)
        FROM latest l
        JOIN core_vehicle_onboarding vo ON UPPER(REGEXP_REPLACE(vo.registration_no, '[^A-Za-z0-9]', '', 'g')) = UPPER(REGEXP_REPLACE(l.vehicle_number, '[^A-Za-z0-9]', '', 'g'))
    """)).scalar()
    print(f"Latest allocations matching core_vehicle_onboarding: {v_in_onboarding}")

    v_in_vehicles = conn.execute(text("""
        WITH latest AS (
            SELECT DISTINCT ON (d.app_driver_id)
                d.app_driver_id, a.vehicle_number
            FROM app_drivers d
            JOIN app_driver_allocations a ON d.app_driver_id = a.app_driver_id
            WHERE d.vehicle_reg_number IS NULL
            ORDER BY d.app_driver_id, a.allocation_date DESC, a.app_allocation_id DESC
        )
        SELECT count(DISTINCT l.app_driver_id)
        FROM latest l
        JOIN vehicles v ON UPPER(REGEXP_REPLACE(v.vehicle_number, '[^A-Za-z0-9]', '', 'g')) = UPPER(REGEXP_REPLACE(l.vehicle_number, '[^A-Za-z0-9]', '', 'g'))
    """)).scalar()
    print(f"Latest allocations matching vehicles table: {v_in_vehicles}")

    # Check why 1,876:
    # 1876 + 19 = 1895. What are the 19?
    # Let's check if there are 19 drivers with something specific (e.g., returned? or non-active? or duplicate vehicles? or what?)
