from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    print("=== EXPLORING 1,876 NUMBER ===")

    # Check total drivers in app_drivers
    print("Total app_drivers:", conn.execute(text("SELECT count(*) FROM app_drivers")).scalar())
    print("app_drivers where vehicle_reg_number IS NOT NULL:", conn.execute(text("SELECT count(*) FROM app_drivers WHERE vehicle_reg_number IS NOT NULL")).scalar())
    print("app_drivers where vehicle_reg_number IS NULL:", conn.execute(text("SELECT count(*) FROM app_drivers WHERE vehicle_reg_number IS NULL")).scalar())

    # How many drivers in app_drivers have at least one allocation in app_driver_allocations?
    q1 = """
        SELECT count(DISTINCT d.app_driver_id)
        FROM app_drivers d
        JOIN app_driver_allocations a ON d.app_driver_id = a.app_driver_id
        WHERE d.vehicle_reg_number IS NULL
    """
    print("Drivers with NULL vehicle_reg having ANY allocation in app_driver_allocations:", conn.execute(text(q1)).scalar())

    # How many drivers with NULL vehicle_reg have an allocation in core_vehicle_allocation?
    q2 = """
        SELECT count(DISTINCT d.app_driver_id)
        FROM app_drivers d
        JOIN core_vehicle_allocation c ON (
            RIGHT(REGEXP_REPLACE(COALESCE(c.driver_phone, ''), '[^0-9]', '', 'g'), 10) = d.phone
        )
        WHERE d.vehicle_reg_number IS NULL
    """
    print("Drivers with NULL vehicle_reg matching core_vehicle_allocation by phone:", conn.execute(text(q2)).scalar())

    # How many allocations in app_driver_allocations have dropoff_date IS NULL?
    q3 = """
        SELECT count(DISTINCT d.app_driver_id)
        FROM app_drivers d
        JOIN app_driver_allocations a ON d.app_driver_id = a.app_driver_id
        WHERE d.vehicle_reg_number IS NULL AND a.dropoff_date IS NULL
    """
    print("Drivers with NULL vehicle_reg having dropoff_date IS NULL:", conn.execute(text(q3)).scalar())

    # What about core_vehicle_allocation where status != 'Dropoff' or return_date IS NULL?
    # Let's check allocation statuses in core_vehicle_allocation
    print("core_vehicle_allocation status counts:")
    for r in conn.execute(text("SELECT status, count(*) FROM core_vehicle_allocation GROUP BY status")).fetchall():
        print(" ", r)

    # What about reason_to_visit or allocation_type?
    print("core_vehicle_allocation allocation_type counts:")
    for r in conn.execute(text("SELECT allocation_type, count(*) FROM core_vehicle_allocation GROUP BY allocation_type")).fetchall():
        print(" ", r)

    # Let's check how many total drivers have allocations:
    # 2580 total drivers.
    # What about test drivers? (IDs 393878, 393887, 393888, 393942, 393943, 393944, 393991, 393992, 393993)
    # What about drivers with vehicle_reg_number:
    # If 2580 - 402 - 9 test drivers = 2169?
    # What if we look at latest allocation per driver in app_driver_allocations?
    q_latest = """
        SELECT DISTINCT ON (app_driver_id)
            app_driver_id,
            allocation_status,
            vehicle_number,
            allocation_date
        FROM app_driver_allocations
        ORDER BY app_driver_id, allocation_date DESC, app_allocation_id DESC
    """
    res = conn.execute(text(f"""
        WITH latest AS ({q_latest})
        SELECT count(*)
        FROM app_drivers d
        JOIN latest l ON d.app_driver_id = l.app_driver_id
        WHERE d.vehicle_reg_number IS NULL
    """)).scalar()
    print("Drivers with NULL vehicle_reg matching latest allocation (by date):", res)

    # What if we look at drivers that have active allocations vs returned:
    # Let's check how sync_active_allocations.py ran previously:
    # Look at sync_active_allocations.py:
    # UPDATE app_drivers d
    # SET vehicle_reg_number = sub.vehicle_number,
    #     current_allocation_id = sub.app_allocation_id,
    #     vehicle_allocated_from = sub.allocation_date
    # FROM (
    #     SELECT DISTINCT ON (app_driver_id) app_driver_id, vehicle_number, app_allocation_id, allocation_date
    #     FROM app_driver_allocations
    #     WHERE allocation_status = 'ACTIVE' AND vehicle_number IS NOT NULL AND vehicle_number != ''
    #     ORDER BY app_driver_id, app_allocation_id DESC
    # ) sub
    # WHERE d.app_driver_id = sub.app_driver_id
    #   AND (d.vehicle_reg_number IS NULL OR d.vehicle_reg_number = '');

    # Why did sync_active_allocations.py say:
    # "Updated drivers with active allocations: ..."
    # Let's check git log or history if any, or check app_driver_allocations.allocation_status!
