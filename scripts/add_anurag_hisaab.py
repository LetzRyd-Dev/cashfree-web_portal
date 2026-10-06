from app.database import engine
from sqlalchemy import text

def add_hisaab():
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO app_hisaabs (
                app_driver_id, app_operator_id, hisaab_number, week_number, period_start, period_end,
                days_count, status, growth_pct, uber_trips, uber_revenue, uber_cash, uber_toll, uber_incentive, uber_subscription, uber_km,
                ola_trips, ola_revenue, ola_cash, ola_toll, ola_incentive, ola_subscription, ola_km,
                rapido_trips, rapido_revenue, rapido_cash, rapido_toll, rapido_incentive, rapido_subscription, rapido_km,
                vehicle_daily_rate, vehicle_rent, maintenance_daily_rate, maintenance_charge,
                tds_amount, challan_amount, accident_charge, other_adjustment, previous_outstanding,
                completed_trips, total_km, total_gross_earnings, total_deductions, total_penalties,
                current_period_os, to_pay, to_collect, letzryd_earning, weekly_hisaab_due, created_at, updated_at
            ) VALUES (
                999990, 1, 'HIS-2026-030-NB2026', 30, '2026-07-21', '2026-07-27',
                7, 'active', 4.50, 95, 8400.00, 5200.00, 180.00, 1400.00, 650.00, 680.00,
                55, 5200.00, 3100.00, 120.00, 800.00, 420.00, 440.00,
                35, 3250.00, 1800.00, 60.00, 500.00, 240.00, 300.50,
                950.00, 6650.00, 150.00, 1050.00,
                168.50, 0.00, 0.00, 0.00, 0.00,
                185, 1420.50, 16850.00, 15400.00, 0.00,
                1450.00, 0.00, 1450.00, 7700.00, 1450.00, NOW(), NOW()
            );
        """))
        print("Inserted app_hisaabs row successfully!")

if __name__ == "__main__":
    add_hisaab()
