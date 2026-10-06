from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    print("=== TASK 1 INVESTIGATION ===")
    
    # 1. How many drivers in app_drivers have vehicle_reg_number IS NULL?
    c_null = conn.execute(text("SELECT count(*) FROM app_drivers WHERE vehicle_reg_number IS NULL")).scalar()
    print("app_drivers with vehicle_reg_number IS NULL:", c_null)

    # 2. Latest active allocation in app_driver_allocations:
    # Notice: latest active allocation per driver:
    q_latest_active = """
        SELECT DISTINCT ON (app_driver_id)
            app_allocation_id,
            core_allocation_id,
            app_driver_id,
            vehicle_number,
            allocation_date,
            daily_rental_rate,
            allocation_status
        FROM app_driver_allocations
        WHERE allocation_status = 'ACTIVE'
          AND vehicle_number IS NOT NULL AND vehicle_number != ''
        ORDER BY app_driver_id, allocation_date DESC, app_allocation_id DESC
    """
    
    res = conn.execute(text(f"""
        WITH latest_active AS ({q_latest_active})
        SELECT count(*)
        FROM app_drivers d
        JOIN latest_active a ON d.app_driver_id = a.app_driver_id
        WHERE d.vehicle_reg_number IS NULL
    """)).scalar()
    print("Drivers with vehicle_reg_number IS NULL matching latest active allocation:", res)

    # What if allocation_status is not strictly 'ACTIVE', or what statuses are there?
    res_all_stat = conn.execute(text(f"""
        WITH latest_any AS (
            SELECT DISTINCT ON (app_driver_id)
                app_allocation_id, core_allocation_id, app_driver_id, vehicle_number, allocation_date, daily_rental_rate, allocation_status
            FROM app_driver_allocations
            WHERE vehicle_number IS NOT NULL AND vehicle_number != ''
            ORDER BY app_driver_id, 
                     CASE WHEN allocation_status = 'ACTIVE' THEN 1 ELSE 2 END,
                     allocation_date DESC, app_allocation_id DESC
        )
        SELECT a.allocation_status, count(*)
        FROM app_drivers d
        JOIN latest_any a ON d.app_driver_id = a.app_driver_id
        WHERE d.vehicle_reg_number IS NULL
        GROUP BY a.allocation_status
    """)).fetchall()
    print("Drivers with vehicle_reg_number IS NULL matching latest allocation grouped by status:", res_all_stat)

    # Let's see: total matching latest_any:
    res_total_matching = conn.execute(text(f"""
        WITH latest_any AS (
            SELECT DISTINCT ON (app_driver_id)
                app_allocation_id, core_allocation_id, app_driver_id, vehicle_number, allocation_date, daily_rental_rate, allocation_status
            FROM app_driver_allocations
            WHERE vehicle_number IS NOT NULL AND vehicle_number != ''
            ORDER BY app_driver_id, 
                     CASE WHEN allocation_status = 'ACTIVE' THEN 1 ELSE 2 END,
                     allocation_date DESC, app_allocation_id DESC
        )
        SELECT count(*)
        FROM app_drivers d
        JOIN latest_any a ON d.app_driver_id = a.app_driver_id
        WHERE d.vehicle_reg_number IS NULL
    """)).scalar()
    print("Total matching latest_any:", res_total_matching)

