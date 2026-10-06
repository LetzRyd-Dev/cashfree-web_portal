from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    print("=== Drivers with vehicle_reg_number populated ===")
    sample_drvs = conn.execute(text("""
        SELECT app_driver_id, vehicle_reg_number, vehicle_make, vehicle_model, vehicle_variant, vehicle_daily_rate, vehicle_allocated_from, current_allocation_id
        FROM app_drivers
        WHERE vehicle_reg_number IS NOT NULL AND vehicle_reg_number != ''
        LIMIT 5
    """)).fetchall()
    for d in sample_drvs:
        print(" ", d)

    print("\n=== Make, Model, Variant values in app_drivers ===")
    makes = conn.execute(text("""
        SELECT vehicle_make, count(*) FROM app_drivers WHERE vehicle_reg_number IS NOT NULL GROUP BY vehicle_make
    """)).fetchall()
    print("Makes:", makes)
    models = conn.execute(text("""
        SELECT vehicle_model, count(*) FROM app_drivers WHERE vehicle_reg_number IS NOT NULL GROUP BY vehicle_model
    """)).fetchall()
    print("Models:", models)
    variants = conn.execute(text("""
        SELECT vehicle_variant, count(*) FROM app_drivers WHERE vehicle_reg_number IS NOT NULL GROUP BY vehicle_variant
    """)).fetchall()
    print("Variants:", variants)
    rates = conn.execute(text("""
        SELECT vehicle_daily_rate, count(*) FROM app_drivers WHERE vehicle_reg_number IS NOT NULL GROUP BY vehicle_daily_rate
    """)).fetchall()
    print("Rates:", rates)
