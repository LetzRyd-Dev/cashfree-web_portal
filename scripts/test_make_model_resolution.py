from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    print("=== Testing Nulls in Make/Model/Variant across 1895 drivers ===")
    
    q = """
        WITH latest_alloc AS (
            SELECT DISTINCT ON (app_driver_id)
                app_allocation_id,
                core_allocation_id,
                app_driver_id,
                vehicle_number,
                allocation_date,
                daily_rental_rate,
                start_odometer
            FROM app_driver_allocations
            WHERE vehicle_number IS NOT NULL AND vehicle_number != ''
            ORDER BY app_driver_id,
                     CASE WHEN allocation_status = 'ACTIVE' THEN 1 ELSE 2 END,
                     allocation_date DESC,
                     app_allocation_id DESC
        )
        SELECT 
            d.app_driver_id,
            la.vehicle_number,
            COALESCE(v.vehicle_brand, vo.registered_owner_name, vo.dealer_name, 'Maruti') as make,
            COALESCE(v.vehicle_model, vo.model, cva.car_model, 'Dzire CNG') as model,
            COALESCE(vo.model, v.vehicle_model, cva.car_model, 'VXi') as variant
        FROM latest_alloc la
        JOIN app_drivers d ON d.app_driver_id = la.app_driver_id
        LEFT JOIN core_vehicle_allocation cva ON cva.id = la.core_allocation_id
        LEFT JOIN vehicles v ON UPPER(REGEXP_REPLACE(v.vehicle_number, '[^A-Za-z0-9]', '', 'g')) = UPPER(REGEXP_REPLACE(la.vehicle_number, '[^A-Za-z0-9]', '', 'g'))
        LEFT JOIN core_vehicle_onboarding vo ON UPPER(REGEXP_REPLACE(vo.registration_no, '[^A-Za-z0-9]', '', 'g')) = UPPER(REGEXP_REPLACE(la.vehicle_number, '[^A-Za-z0-9]', '', 'g'))
        WHERE d.vehicle_reg_number IS NULL
    """
    rows = conn.execute(text(q)).fetchall()
    print("Total rows:", len(rows))
    null_make = [r for r in rows if not r[2]]
    null_model = [r for r in rows if not r[3]]
    null_variant = [r for r in rows if not r[4]]
    print("Null make:", len(null_make))
    print("Null model:", len(null_model))
    print("Null variant:", len(null_variant))

    # Check distinct values of make, model, variant
    makes = set(r[2] for r in rows)
    models = set(r[3] for r in rows)
    variants = set(r[4] for r in rows)
    print("\nDistinct makes:", makes)
    print("Distinct models:", models)
    print("Distinct variants:", variants)
