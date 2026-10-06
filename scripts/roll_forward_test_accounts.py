import datetime
from decimal import Decimal
from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

weeks = [
    (36, datetime.date(2026, 8, 31), datetime.date(2026, 9, 6), "settled"),
    (37, datetime.date(2026, 9, 7), datetime.date(2026, 9, 13), "settled"),
    (38, datetime.date(2026, 9, 14), datetime.date(2026, 9, 20), "settled"),
    (39, datetime.date(2026, 9, 21), datetime.date(2026, 9, 27), "settled"),
    (40, datetime.date(2026, 9, 28), datetime.date(2026, 10, 4), "in_progress"),
]

# Drivers config
# (app_driver_id, car_suffix, reg, op_id, daily_rate, rent_days, base_trips, base_earnings, base_deduct)
drivers_cfg = [
    (1, "AQ7692", "KA05AQ7692", 1, 1000, 6, 142, Decimal("15200.00"), Decimal("7300.00")), # Vivek -> to_pay ~ 7900
    (2, "EV8812", "TS09EV8812", 1, 1000, 5, 115, Decimal("11400.00"), Decimal("13200.00")), # Sushant -> to_collect ~ 1800
    (3, "DE1234", "MH01DE1234", 1, 1100, 6, 130, Decimal("14100.00"), Decimal("8500.00")),  # Aayush -> to_pay ~ 5600
    (4, "UB5678", "TS09UB5678", 1, 1050, 6, 120, Decimal("13500.00"), Decimal("7800.00")),  # Anurag Drv -> to_pay ~ 5700
    (999990, "NB2026", "KA03NB2026", 0, 1000, 5, 110, Decimal("10800.00"), Decimal("12250.00")), # Anurag -> to_collect ~ 1450
]

for w_num, p_start, p_end, default_status in weeks:
    for did, suffix, reg, op_id, rate, rdays, trips, earnings, deduct in drivers_cfg:
        exists = db.execute(text("SELECT app_hisaab_id FROM app_hisaabs WHERE app_driver_id = :did AND week_number = :w"), {"did": did, "w": w_num}).scalar()
        if exists:
            print(f"Driver {did} Week {w_num} already exists.")
            continue
        
        rent = Decimal(str(rate * rdays))
        tot_deduct = rent + (deduct - rent)
        net = earnings - tot_deduct
        if net >= 0:
            to_pay = net
            to_collect = Decimal("0.00")
            stat = "settled_pay" if default_status == "settled" else "in_progress"
        else:
            to_pay = Decimal("0.00")
            to_collect = abs(net)
            stat = "settled_collect" if default_status == "settled" else "to_collect"
        
        hisaab_no = f"HIS-2026-{w_num:03d}-{suffix}"
        
        db.execute(text("""
            INSERT INTO app_hisaabs (
                app_driver_id, app_operator_id, hisaab_number, week_number,
                period_start, period_end, days_count, status, is_locked,
                completed_trips, total_gross_earnings, total_deductions,
                vehicle_daily_rate, vehicle_rent, current_period_os,
                to_pay, to_collect, total_km, weekly_hisaab_due,
                uber_trips, uber_revenue, ola_trips, ola_revenue,
                created_at, updated_at
            ) VALUES (
                :did, :op_id, :hisaab_no, :w_num,
                :p_start, :p_end, 7, :stat, false,
                :trips, :earnings, :tot_deduct,
                :rate, :rent, 0.00,
                :to_pay, :to_collect, :trips * 12, :tot_deduct,
                :trips, :earnings, 0, 0.00,
                NOW(), NOW()
            )
        """), {
            "did": did, "op_id": op_id, "hisaab_no": hisaab_no, "w_num": w_num,
            "p_start": p_start, "p_end": p_end, "stat": stat,
            "trips": trips, "earnings": earnings, "tot_deduct": tot_deduct,
            "rate": rate, "rent": rent, "to_pay": to_pay, "to_collect": to_collect
        })
        print(f"Inserted Hisaab Week {w_num} for driver {did} ({hisaab_no})")

db.commit()

# Update app_drivers current week (cw_...) columns for Driver 1 and 2 to match Week 40
db.execute(text("""
    UPDATE app_drivers
    SET cw_trips = 118,
        cw_gross_earnings = 11500.00,
        cw_total_deductions = 13350.00,
        cw_to_collect = 1850.00,
        cw_to_pay = 0.00,
        cw_os = 1850.00,
        lw_week_number = 39,
        lw_trips = 115,
        lw_gross_earnings = 11400.00,
        lw_os = 1800.00,
        lw_status = 'settled_collect'
    WHERE app_driver_id = 2
"""))

db.execute(text("""
    UPDATE app_drivers
    SET cw_trips = 145,
        cw_gross_earnings = 15435.80,
        cw_total_deductions = 7440.00,
        cw_to_collect = 0.00,
        cw_to_pay = 7995.80,
        cw_os = 7995.80,
        lw_week_number = 39,
        lw_trips = 142,
        lw_gross_earnings = 15200.00,
        lw_os = 7900.00,
        lw_status = 'settled_pay'
    WHERE app_driver_id = 1
"""))

# Update app_operators current week columns for Operator 1
db.execute(text("""
    UPDATE app_operators
    SET cw_fleet_trips = 507,
        cw_fleet_gross_earnings = 54200.00,
        cw_fleet_net_os = 17400.00,
        cw_to_pay = 17400.00,
        cw_to_collect = 0.00,
        cw_active_vehicles = 4,
        cw_active_drivers = 4,
        lw_week_number = 39,
        lw_fleet_trips = 500,
        lw_fleet_gross_earnings = 53800.00,
        lw_status = 'settled'
    WHERE app_operator_id = 1
"""))

db.commit()
print("All Week 36-40 test hisaabs committed successfully.")
db.close()
