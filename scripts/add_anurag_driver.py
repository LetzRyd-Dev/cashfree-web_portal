import sys
from app.database import engine
from sqlalchemy import text

def add_anurag_driver():
    with engine.begin() as conn:
        existing = conn.execute(
            text("SELECT app_driver_id, full_name, phone FROM app_drivers WHERE phone=:p"),
            {"p": "9691938866"}
        ).fetchone()

        if existing:
            print("Driver profile already exists:", existing)
            return

        conn.execute(text("""
            INSERT INTO app_drivers (
                app_driver_id, driver_id, operator_id, full_name, phone,
                driver_code, aadhar_number, blood_group, dob, address,
                joined_date, emergency_name, emergency_relation, emergency_phone,
                dl_number, dl_expiry, vehicle_reg_number, vehicle_make, vehicle_model,
                vehicle_variant, vehicle_year, vehicle_color, vehicle_fuel_type,
                vehicle_odometer_km, vehicle_allocated_from, vehicle_daily_rate,
                rc_number, rc_expiry, insurance_number, insurance_expiry,
                permit_type, permit_number, permit_expiry, fitness_number, fitness_expiry,
                puc_expiry, doc_last_updated, deposit_total_req, deposit_paid, deposit_pending,
                joining_fee_agreed, joining_fee_paid, cumulative_owed,
                assigned_manager_name, assigned_manager_phone,
                incentive_trips_target, incentive_reward_amt, referral_code, referral_reward_amt,
                upi_id, bank_account_last4, preferred_language, is_active,
                created_at, cw_trips, cw_total_km, cw_gross_earnings, cw_total_deductions,
                cw_os, cw_to_collect, cw_to_pay, lw_trips, lw_gross_earnings, lw_os,
                lw_week_number, lw_hisaab_number, lw_status, growth_pct, cw_incentive_trips_done
            ) VALUES (
                999990, 999990, 0, 'Anurag', '9691938866',
                'LR-DRV-999990', '9876-5432-1098', 'O+', '1995-05-15', 'Indiranagar 100ft Road, Bengaluru - 560038',
                '2026-01-10', 'Rahul Sharma', 'Friend/Brother', '9876543210',
                'KA03-2022-0098765', '2032-12-31', 'KA03NB2026', 'Tata', 'Tigor EV',
                'XZ Plus', 2024, 'Pearl White', 'Electric',
                28400, '2026-01-10', 950.00,
                'KA03NB2026', '2039-01-10', 'INS-TATA-2026-09', '2027-01-10',
                'All India Tourist Permit', 'AITP-KA-2026-19', '2027-12-31', 'FIT-KA-2026-88', '2027-01-10',
                '2026-12-31', '2026-09-15', 5000.00, 5000.00, 0.00,
                1000.00, 1000.00, 0.00,
                'Ramesh Kumar (Ops Lead)', '9845012345',
                250, 1500.00, 'ANURAG969', 1000.00,
                'anurag@oksbi', '2026', 'en', true,
                NOW(), 185, 1420.50, 16850.00, 7250.00,
                1450.00, 1450.00, 0.00, 192, 17200.00, 0.00,
                29, 'HIS-2026-029-NB2026', 'settled_pay', 4.5, 185
            );
        """))
        print("Inserted Anurag into app_drivers successfully!")

        hisaab_exists = conn.execute(
            text("SELECT app_hisaab_id FROM app_hisaabs WHERE app_driver_id=999990")
        ).scalar()

        if not hisaab_exists:
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
            print("Inserted app_hisaabs row for Anurag!")

if __name__ == "__main__":
    add_anurag_driver()
