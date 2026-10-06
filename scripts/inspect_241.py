from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    print("=== INSPECTING THE 241 REMAINING NULL DRIVERS ===")
    
    q = """
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
        ),
        enriched_alloc AS (
            SELECT DISTINCT ON (la.app_driver_id)
                la.app_driver_id,
                la.app_allocation_id,
                la.vehicle_number,
                la.allocation_date,
                COALESCE(la.daily_rental_rate, 1000.00) as daily_rate,
                COALESCE(la.start_odometer, 0) as start_odometer,
                COALESCE(v.vehicle_brand, vo.registered_owner_name, vo.dealer_name, 'Maruti') as make,
                COALESCE(v.vehicle_model, vo.model, cva.car_model, 'Dzire CNG') as model,
                COALESCE(vo.model, v.vehicle_model, cva.car_model, 'VXi') as variant,
                COALESCE(vo.color, 'White') as color,
                COALESCE(vo.fuel_type, v.fuel_type, 'CNG') as fuel_type
            FROM latest_alloc la
            LEFT JOIN core_vehicle_allocation cva ON cva.id = la.core_allocation_id
            LEFT JOIN vehicles v ON UPPER(REGEXP_REPLACE(v.vehicle_number, '[^A-Za-z0-9]', '', 'g')) = UPPER(REGEXP_REPLACE(la.vehicle_number, '[^A-Za-z0-9]', '', 'g'))
            LEFT JOIN core_vehicle_onboarding vo ON UPPER(REGEXP_REPLACE(vo.registration_no, '[^A-Za-z0-9]', '', 'g')) = UPPER(REGEXP_REPLACE(la.vehicle_number, '[^A-Za-z0-9]', '', 'g'))
            ORDER BY la.app_driver_id, vo.id DESC NULLS LAST, v.id DESC NULLS LAST
        )
        SELECT d.app_driver_id, d.full_name, d.phone, ea.vehicle_number, ea.daily_rate, ea.make, ea.model, ea.variant
        FROM app_drivers d
        JOIN enriched_alloc ea ON d.app_driver_id = ea.app_driver_id
        WHERE d.vehicle_reg_number IS NULL OR d.vehicle_reg_number = ''
        LIMIT 10;
    """
    rows = conn.execute(text(q)).fetchall()
    print("Sample of the 241 drivers:")
    for r in rows:
        print(" ", r)
