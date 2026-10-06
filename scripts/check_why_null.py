from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    print("=== Testing UPDATE on driver 559 ===")
    
    q_sel = """
        WITH latest_alloc AS (
            SELECT DISTINCT ON (a.app_driver_id)
                a.app_allocation_id,
                a.core_allocation_id,
                a.app_driver_id,
                a.vehicle_number,
                a.allocation_date,
                a.daily_rental_rate,
                a.start_odometer
            FROM app_driver_allocations a
            WHERE a.vehicle_number IS NOT NULL AND a.vehicle_number != ''
            ORDER BY a.app_driver_id,
                     CASE WHEN a.allocation_status = 'ACTIVE' THEN 1 ELSE 2 END,
                     a.allocation_date DESC,
                     a.app_allocation_id DESC
        )
        SELECT 
            la.app_driver_id,
            la.vehicle_number,
            la.allocation_date,
            la.daily_rental_rate,
            la.app_allocation_id,
            COALESCE(v.vehicle_brand, vo.registered_owner_name, vo.dealer_name, 'Maruti') as make,
            COALESCE(v.vehicle_model, vo.model, cva.car_model, 'Dzire CNG') as model,
            COALESCE(vo.model, v.vehicle_model, cva.car_model, 'VXi') as variant
        FROM latest_alloc la
        LEFT JOIN core_vehicle_allocation cva ON cva.id = la.core_allocation_id
        LEFT JOIN vehicles v ON UPPER(REGEXP_REPLACE(v.vehicle_number, '[^A-Za-z0-9]', '', 'g')) = UPPER(REGEXP_REPLACE(la.vehicle_number, '[^A-Za-z0-9]', '', 'g'))
        LEFT JOIN core_vehicle_onboarding vo ON UPPER(REGEXP_REPLACE(vo.registration_no, '[^A-Za-z0-9]', '', 'g')) = UPPER(REGEXP_REPLACE(la.vehicle_number, '[^A-Za-z0-9]', '', 'g'))
        WHERE la.app_driver_id = 559;
    """
    row = conn.execute(text(q_sel)).fetchall()
    print("Select for 559:", row)

    # Now let's see how many total rows latest_alloc produces
    q_tot = """
        WITH latest_alloc AS (
            SELECT DISTINCT ON (a.app_driver_id)
                a.app_allocation_id,
                a.core_allocation_id,
                a.app_driver_id,
                a.vehicle_number,
                a.allocation_date,
                a.daily_rental_rate,
                a.start_odometer
            FROM app_driver_allocations a
            WHERE a.vehicle_number IS NOT NULL AND a.vehicle_number != ''
            ORDER BY a.app_driver_id,
                     CASE WHEN a.allocation_status = 'ACTIVE' THEN 1 ELSE 2 END,
                     a.allocation_date DESC,
                     a.app_allocation_id DESC
        )
        SELECT count(*) FROM latest_alloc;
    """
    print("Total rows in latest_alloc:", conn.execute(text(q_tot)).scalar())

    # How many drivers in app_drivers match latest_alloc where vehicle_reg_number IS NULL?
    q_match_null = """
        WITH latest_alloc AS (
            SELECT DISTINCT ON (a.app_driver_id)
                a.app_allocation_id,
                a.core_allocation_id,
                a.app_driver_id,
                a.vehicle_number,
                a.allocation_date,
                a.daily_rental_rate,
                a.start_odometer
            FROM app_driver_allocations a
            WHERE a.vehicle_number IS NOT NULL AND a.vehicle_number != ''
            ORDER BY a.app_driver_id,
                     CASE WHEN a.allocation_status = 'ACTIVE' THEN 1 ELSE 2 END,
                     a.allocation_date DESC,
                     a.app_allocation_id DESC
        )
        SELECT count(*) 
        FROM app_drivers d
        JOIN latest_alloc la ON d.app_driver_id = la.app_driver_id
        WHERE d.vehicle_reg_number IS NULL OR d.vehicle_reg_number = '';
    """
    print("app_drivers matching latest_alloc with NULL vehicle_reg_number:", conn.execute(text(q_match_null)).scalar())

    # How many drivers in app_drivers have vehicle_reg_number IS NULL now?
    print("Total app_drivers with NULL vehicle_reg_number:", conn.execute(text("SELECT count(*) FROM app_drivers WHERE vehicle_reg_number IS NULL OR vehicle_reg_number = ''")).scalar())
