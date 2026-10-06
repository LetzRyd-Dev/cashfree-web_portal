from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    print("=== CHECKING ALL ALLOCATED DRIVERS WITH NULL VEHICLE ===")
    q = """
        SELECT count(DISTINCT d.app_driver_id)
        FROM app_drivers d
        JOIN app_driver_allocations a ON d.app_driver_id = a.app_driver_id
        WHERE d.vehicle_reg_number IS NULL OR d.vehicle_reg_number = ''
    """
    cnt = conn.execute(text(q)).scalar()
    print("Count:", cnt)

    # If cnt > 0, let's see what happens when we update them with a simple subquery:
    q_sub = """
        SELECT d.app_driver_id, sub.vehicle_number
        FROM app_drivers d
        JOIN (
            SELECT DISTINCT ON (app_driver_id) app_driver_id, vehicle_number
            FROM app_driver_allocations
            WHERE vehicle_number IS NOT NULL AND vehicle_number != ''
            ORDER BY app_driver_id, CASE WHEN allocation_status = 'ACTIVE' THEN 1 ELSE 2 END, allocation_date DESC, app_allocation_id DESC
        ) sub ON d.app_driver_id = sub.app_driver_id
        WHERE d.vehicle_reg_number IS NULL OR d.vehicle_reg_number = ''
        LIMIT 5;
    """
    rows = conn.execute(text(q_sub)).fetchall()
    print("Sample matching subquery:", rows)
