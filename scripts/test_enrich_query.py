from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    print("=== Testing Sync query for app_drivers ===")

    # Let's inspect latest allocation per driver in app_driver_allocations
    # Note: What if a driver's allocation_status is 'ACTIVE' vs 'RETURNED'?
    # Remember: earlier we checked:
    # 'ACTIVE': 8
    # 'RETURNED': 1887
    # If we filter ONLY `allocation_status = 'ACTIVE'`, only 8 drivers would get updated!
    # BUT the prompt title says: "Fix 1,876 Drivers Missing Vehicle Reg" (1876 ~ 1895)!
    # Let's check why almost all allocations are 'RETURNED'.
    # In app_tables_full_setup.sql:
    # CASE WHEN dr.return_date IS NOT NULL AND dr.return_date >= a.allocation_date THEN 'RETURNED'
    # Wait! In core_dropoffs or core_vehicle_allocation, many allocations were marked RETURNED because dropoffs exist.
    # But for a driver whose vehicle_reg_number IS NULL, their latest allocation in app_driver_allocations has their vehicle!
    # Let's check:
    q_check_stat = """
        SELECT a.allocation_status, count(*)
        FROM (
            SELECT DISTINCT ON (app_driver_id)
                app_driver_id, vehicle_number, allocation_date, daily_rental_rate, allocation_status, app_allocation_id
            FROM app_driver_allocations
            WHERE vehicle_number IS NOT NULL AND vehicle_number != ''
            ORDER BY app_driver_id, allocation_date DESC, app_allocation_id DESC
        ) a
        JOIN app_drivers d ON d.app_driver_id = a.app_driver_id
        WHERE d.vehicle_reg_number IS NULL
        GROUP BY a.allocation_status;
    """
    print("Statuses of latest allocation for NULL vehicle drivers:")
    for r in conn.execute(text(q_check_stat)).fetchall():
        print(" ", r)

    # What if we order by:
    # ORDER BY app_driver_id, CASE WHEN allocation_status = 'ACTIVE' THEN 1 ELSE 2 END, allocation_date DESC, app_allocation_id DESC
    # That picks ACTIVE if available, otherwise latest allocation!
    # Let's see if there are drivers where allocation_status = 'ACTIVE' vs 'RETURNED'
    
    # Let's inspect what make, model, variant we get from core_vehicle_onboarding vs vehicles
    q_enrich = """
        WITH latest_alloc AS (
            SELECT DISTINCT ON (app_driver_id)
                app_allocation_id,
                core_allocation_id,
                app_driver_id,
                vehicle_number,
                allocation_date,
                daily_rental_rate,
                allocation_status
            FROM app_driver_allocations
            WHERE vehicle_number IS NOT NULL AND vehicle_number != ''
            ORDER BY app_driver_id,
                     CASE WHEN allocation_status = 'ACTIVE' THEN 1 ELSE 2 END,
                     allocation_date DESC,
                     app_allocation_id DESC
        )
        SELECT 
            la.vehicle_number,
            la.allocation_date,
            la.daily_rental_rate,
            COALESCE(v.vehicle_brand, vo.registered_owner_name, vo.dealer_name, 'Maruti') as make,
            COALESCE(v.vehicle_model, vo.model, cva.car_model, 'Dzire CNG') as model,
            COALESCE(vo.model, v.vehicle_model, cva.car_model, 'VXi') as variant
        FROM latest_alloc la
        JOIN app_drivers d ON d.app_driver_id = la.app_driver_id
        LEFT JOIN core_vehicle_allocation cva ON cva.id = la.core_allocation_id
        LEFT JOIN vehicles v ON UPPER(REGEXP_REPLACE(v.vehicle_number, '[^A-Za-z0-9]', '', 'g')) = UPPER(REGEXP_REPLACE(la.vehicle_number, '[^A-Za-z0-9]', '', 'g'))
        LEFT JOIN core_vehicle_onboarding vo ON UPPER(REGEXP_REPLACE(vo.registration_no, '[^A-Za-z0-9]', '', 'g')) = UPPER(REGEXP_REPLACE(la.vehicle_number, '[^A-Za-z0-9]', '', 'g'))
        WHERE d.vehicle_reg_number IS NULL
        LIMIT 10;
    """
    sample_enriched = conn.execute(text(q_enrich)).fetchall()
    print("\nSample enriched rows (first 10):")
    for se in sample_enriched:
        print(" ", se)

