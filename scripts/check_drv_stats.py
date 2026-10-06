from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()

d_stats = db.execute(text("""
    SELECT 
        count(*) as total_drivers,
        count(cw_to_collect) as not_null_collect,
        count(CASE WHEN cw_to_collect > 0 THEN 1 END) as collect_gt_0,
        count(CASE WHEN cw_to_pay > 0 THEN 1 END) as pay_gt_0,
        count(CASE WHEN cw_to_collect = 0 AND cw_to_pay = 0 THEN 1 END) as both_zero,
        count(CASE WHEN cw_to_collect IS NULL AND cw_to_pay IS NULL THEN 1 END) as both_null
    FROM app_drivers
""")).mappings().first()
print("app_drivers financial stats:", dict(d_stats))

db.close()
