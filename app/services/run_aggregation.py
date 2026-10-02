"""
run_aggregation.py — Production Data Population & Aggregator Script
=====================================================================
Executes the aggregation engine against Final Tables & Output/Hisaab Tables
(core_partner_onboarding, core_vehicle_allocation, core_vehicle_onboarding,
hisaab_vehicle_weekly, hisaab_partner_weekly, etc.).
"""

import sys
from pathlib import Path
from sqlalchemy import text

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from app.database import SessionLocal
from app.services.platform_aggregator import aggregate_raw_platform_data

def run_live_aggregation(week_number=None, truncate_first=False):
    db = SessionLocal()
    print("=" * 70)
    print("RUNNING APP TABLES SYNC FROM FINAL & OUTPUT / HISAAB TABLES")
    print("=" * 70)
    try:
        # Check if stored procedure exists
        check_proc = db.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM pg_proc WHERE proname = 'sp_populate_all_app_tables'
            );
        """)).scalar()

        if check_proc:
            print(f"Calling public.sp_populate_all_app_tables(truncate_first={truncate_first})...")
            db.execute(text(f"CALL public.sp_populate_all_app_tables({str(truncate_first).lower()});"))
            db.commit()
            print("Successfully populated and synchronized App Tables via stored procedure!")
        else:
            print("Running fallback python aggregator...")
            count = aggregate_raw_platform_data(db, week_number=week_number)
            print(f"Processed {count} vehicle-week records into app_hisaabs, app_drivers, and app_operators!")
    except Exception as e:
        print(f"Error during aggregation: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    week_num = None
    trunc = False
    if "--truncate" in sys.argv:
        trunc = True
    for arg in sys.argv[1:]:
        try:
            week_num = int(arg)
        except ValueError:
            pass
    run_live_aggregation(week_number=week_num, truncate_first=trunc)
