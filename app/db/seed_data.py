"""
seed_data.py — Comprehensive Development Seed Script
Creates 2 operators, 6 drivers, and full hisaab/ticket/notification/referral data.
All variables for all users are 100% populated.
"""
import sys
from pathlib import Path
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from app.database import SessionLocal
from app.models.app_models import (
    AppDrivers, AppOperators, AppHisaabs, AppSupportTickets,
    AppNotifications, AppReferralLeads, AppPayments, AppSessions, AppAuditLogs
)
from sqlalchemy import text

def utc_now():
    return datetime.now(timezone.utc)


def clear_all(db):
    tables = ['app_referral_leads','app_notifications','app_support_tickets','app_payments',
              'app_hisaabs','app_sessions','app_audit_logs','app_operators','app_drivers',
              'raw_uber_data','raw_ola_data','raw_rapido_data','raw_uber_incentives',
              'raw_ola_incentives','raw_rapido_incentives','raw_traffic_challans',
              'raw_accidents_registry','raw_partner_adjustments','raw_gps_logs']
    for t in tables:
        db.execute(text(f'TRUNCATE TABLE {t} RESTART IDENTITY CASCADE;'))
    db.commit()
    print('All 19 tables cleared.')

def make_hisaab(app_driver_id, app_operator_id, week, period_start, period_end, days,
                status, is_locked, uber_t, uber_rev, uber_cash, uber_toll, uber_inc, uber_sub, uber_km,
                ola_t, ola_rev, ola_cash, ola_toll, ola_inc, ola_sub, ola_km,
                rap_t, rap_rev, rap_cash, rap_toll, rap_inc, rap_sub, rap_km,
                daily_rate, rent, maint, tds, challan, accident, adjustment, prev_os,
                gps_total, gps_ideal, gps_dead, gps_penalty,
                total_gross, total_ded, cur_os, to_pay, to_collect, growth,
                letzryd_earn, notes, vehicle_code):
    hisaab_number = f"HIS-2026-{week:03d}-{vehicle_code[-6:]}"
    completed_trips = uber_t + ola_t + rap_t
    total_km = float(uber_km + ola_km + rap_km)
    return AppHisaabs(
        allocation_id=1,
        hisaab_id=week,
        app_driver_id=app_driver_id,
        app_operator_id=app_operator_id,
        vehicle_id=1,
        hisaab_number=hisaab_number,
        week_number=week,
        period_start=period_start,
        period_end=period_end,
        days_count=days,
        status=status,
        is_locked=is_locked,
        growth_pct=growth,
        uber_trips=uber_t, uber_revenue=uber_rev, uber_cash=uber_cash,
        uber_toll=uber_toll, uber_incentive=uber_inc, uber_subscription=uber_sub, uber_km=uber_km,
        ola_trips=ola_t, ola_revenue=ola_rev, ola_cash=ola_cash,
        ola_toll=ola_toll, ola_incentive=ola_inc, ola_subscription=ola_sub, ola_km=ola_km,
        rapido_trips=rap_t, rapido_revenue=rap_rev, rapido_cash=rap_cash,
        rapido_toll=rap_toll, rapido_incentive=rap_inc, rapido_subscription=rap_sub, rapido_km=rap_km,
        vehicle_daily_rate=daily_rate, vehicle_rent=rent,
        maintenance_charge=maint, tds_amount=tds, challan_amount=challan,
        accident_charge=accident, other_adjustment=adjustment, previous_outstanding=prev_os,
        gps_total_km=gps_total, gps_ideal_km=gps_ideal, gps_dead_km=gps_dead,
        gps_dead_pct=round((gps_dead/gps_ideal)*100, 2) if gps_ideal > 0 else 0.0,
        gps_dead_penalty=gps_penalty,
        gps_free_dead_pct=20, gps_penalty_rate=5,
        completed_trips=completed_trips,
        total_km=total_km,
        total_gross_earnings=total_gross,
        total_deductions=total_ded,
        total_penalties=gps_penalty,
        current_period_os=cur_os,
        to_pay=to_pay, to_collect=to_collect,
        letzryd_earning=letzryd_earn,
        weekly_hisaab_due=to_collect if to_collect > 0 else 0,
        last_refreshed_at=utc_now(),
        notes=notes,
        created_at=utc_now(),
        updated_at=utc_now()
    )

def seed_database():
    db = SessionLocal()
    try:
        clear_all(db)
        
        # 1. Operators
        op1 = AppOperators(
            operator_id=1,
            app_driver_id=0,
            operator_code="OPR-HYD-001",
            operator_type="Fleet Owner",
            company_name="Anurag & RK Fleet Logistics",
            contact_person_name="Anurag",
            phone="9691938866",
            initials="A",
            address="Plot 12, Gachibowli Financial District, Hyderabad - 500032",
            total_vehicles=4,
            active_vehicles=4,
            idle_vehicles=0,
            total_drivers=4,
            deposit_total_req=25000.00,
            deposit_paid=20000.00,
            deposit_pending=5000.00,
            assigned_manager_name="Kalyan Chakravarthy",
            assigned_manager_phone="9988770011",
            referral_code="ANURAGOPR",
            referral_reward_amt=2000.00,
            contract_terms_url="https://letzryd.com/terms/operator",
            upi_id="anuragfleet@okhdfcbank",
            bank_account_last4="9012",
            preferred_language="en",
            is_active=True,
            created_at=utc_now(),
            cw_fleet_uber_trips=415, cw_fleet_uber_revenue=56200.00, cw_fleet_uber_cash=37300.00, cw_fleet_uber_incentive=10900.00, cw_fleet_uber_km=4550.00,
            cw_fleet_ola_trips=239, cw_fleet_ola_revenue=25600.00, cw_fleet_ola_cash=15700.00, cw_fleet_ola_incentive=4450.00, cw_fleet_ola_km=2550.00,
            cw_fleet_rapido_trips=170, cw_fleet_rapido_revenue=18900.00, cw_fleet_rapido_cash=10200.00, cw_fleet_rapido_incentive=3000.00, cw_fleet_rapido_km=1871.00,
            cw_fleet_rent=18700.00, cw_fleet_maintenance=3740.00, cw_fleet_tds=564.20, cw_fleet_challans=500.00,
            cw_fleet_gps_dead_km=0.0, cw_fleet_gps_dead_penalty=0.0,
            cw_fleet_trips=824, cw_fleet_km=8971.00, cw_fleet_gross_earnings=49500.00, cw_to_collect=1850.00, cw_to_pay=17655.80, cw_fleet_net_os=-15805.80,
            cw_active_vehicles=4, cw_active_drivers=4,
            lw_fleet_trips=1155, lw_fleet_km=10600.00, lw_fleet_gross_earnings=50290.00, lw_fleet_net_os=1034.80,
            lw_week_number=29, lw_hisaab_number="HIS-2026-029-FLT001", lw_status="settled_pay", growth_pct=-1.57
        )
        
        op2 = AppOperators(
            operator_id=2,
            app_driver_id=0,
            operator_code="OPR-HYD-002",
            operator_type="Fleet Owner",
            company_name="Saleem Fleet Logistics",
            contact_person_name="Mohammed Saleem",
            phone="9848012345",
            initials="MS",
            address="Shop 4, Mehdipatnam Ring Road, Hyderabad - 500028",
            total_vehicles=2,
            active_vehicles=2,
            idle_vehicles=0,
            total_drivers=2,
            deposit_total_req=50000.00,
            deposit_paid=40000.00,
            deposit_pending=10000.00,
            assigned_manager_name="Kalyan Chakravarthy",
            assigned_manager_phone="9988770011",
            referral_code="OPR002REF",
            referral_reward_amt=2000.00,
            contract_terms_url="https://letzryd.com/terms/operator",
            upi_id="saleemfleet@paytm",
            bank_account_last4="3456",
            preferred_language="en",
            is_active=True,
            created_at=utc_now(),
            cw_fleet_uber_trips=140, cw_fleet_uber_revenue=19400.00, cw_fleet_uber_cash=12700.00, cw_fleet_uber_incentive=3650.00, cw_fleet_uber_km=1540.00,
            cw_fleet_ola_trips=76, cw_fleet_ola_revenue=8500.00, cw_fleet_ola_cash=5200.00, cw_fleet_ola_incentive=1500.00, cw_fleet_ola_km=830.00,
            cw_fleet_rapido_trips=49, cw_fleet_rapido_revenue=5900.00, cw_fleet_rapido_cash=3150.00, cw_fleet_rapido_incentive=1000.00, cw_fleet_rapido_km=580.00,
            cw_fleet_rent=7450.00, cw_fleet_maintenance=1490.00, cw_fleet_tds=190.00, cw_fleet_challans=500.00,
            cw_fleet_gps_dead_km=0.0, cw_fleet_gps_dead_penalty=0.0,
            cw_fleet_trips=265, cw_fleet_km=2950.00, cw_fleet_gross_earnings=17000.00, cw_to_collect=1820.50, cw_to_pay=4580.00, cw_fleet_net_os=-2759.50,
            cw_active_vehicles=2, cw_active_drivers=2,
            lw_fleet_trips=495, lw_fleet_km=5300.00, lw_fleet_gross_earnings=25500.00, lw_fleet_net_os=0.00,
            lw_week_number=29, lw_hisaab_number="HIS-2026-029-FLT002", lw_status="settled_pay", growth_pct=-33.33
        )
        
        db.add(op1)
        db.add(op2)
        db.commit()
        
        # 2. Drivers
        d1 = AppDrivers(
            driver_id=157,
            operator_id=op1.app_operator_id,
            driver_code="LR-DRV-0157",
            phone="9901484683",
            full_name="Vivek",
            initials="V",
            profile_photo_url="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
            aadhar_number="2345-6789-0123",
            blood_group="B+",
            dob=date(1992, 8, 14),
            address="No. 42, 3rd Cross, Indiranagar, Bangalore - 560038",
            joined_date=date(2024, 10, 15),
            emergency_name="Priya",
            emergency_relation="Spouse/Wife",
            emergency_phone="9901484680",
            dl_number="KA05-2024-1234567",
            dl_expiry=date(2029, 5, 20),
            current_vehicle_id=1,
            current_allocation_id=1,
            vehicle_reg_number="KA05AQ7692",
            vehicle_make="Maruti",
            vehicle_model="Dzire CNG",
            vehicle_variant="VXi CNG",
            vehicle_color="White Pearl",
            vehicle_year=2021,
            vehicle_fuel_type="CNG",
            vehicle_odometer_km=124380,
            vehicle_allocated_from=date(2024, 10, 15),
            vehicle_daily_rate=1000.00,
            rc_number="KA0520224567",
            rc_expiry=date(2036, 5, 1),
            insurance_number="KA054567890",
            insurance_expiry=date(2027, 3, 20),
            permit_type="Tourist Permit",
            permit_number="KA-05-TP-2024-0012",
            permit_expiry=date(2026, 12, 31),
            fitness_number="FIT2024056",
            fitness_expiry=date(2026, 10, 12),
            puc_expiry=date(2026, 8, 15),
            doc_last_updated=date(2026, 7, 25),
            deposit_total_req=6000.00,
            deposit_paid=5000.00,
            deposit_pending=1000.00,
            deposit_next_due=date(2026, 8, 15),
            joining_fee_agreed=1000.00,
            joining_fee_paid=1000.00,
            cumulative_owed=0.00,
            assigned_manager_name="Ramesh Naik",
            assigned_manager_phone="9876543299",
            incentive_trips_target=260,
            incentive_reward_amt=1500.00,
            cw_incentive_trips_done=233,
            referral_code="VIVEK157",
            referral_reward_amt=1000.00,
            contract_terms_url="https://letzryd.com/terms/driver",
            upi_id="vivek@okhdfcbank",
            bank_account_last4="4920",
            preferred_language="en",
            is_active=True,
            created_at=utc_now(),
            cw_uber_trips=120, cw_uber_revenue=15800, cw_uber_cash=10500, cw_uber_toll=420, cw_uber_incentive=3200, cw_uber_subscription=1500, cw_uber_km=1250,
            cw_ola_trips=65, cw_ola_revenue=6800, cw_ola_cash=4200, cw_ola_toll=180, cw_ola_incentive=1200, cw_ola_subscription=900, cw_ola_km=680,
            cw_rapido_trips=48, cw_rapido_revenue=5200, cw_rapido_cash=2800, cw_rapido_toll=90, cw_rapido_incentive=850, cw_rapido_subscription=390, cw_rapido_km=511,
            cw_vehicle_rent=4000, cw_maintenance_charge=800, cw_active_days=4, cw_tds=154.20, cw_challans=500, cw_accident_charge=0, cw_other_adjustment=0, cw_previous_outstanding=0,
            cw_gps_total_km=3200.80, cw_gps_ideal_km=3820.60, cw_gps_dead_km=0, cw_gps_dead_pct=0, cw_gps_dead_penalty=0,
            cw_trips=233, cw_total_km=2441.00, cw_gross_earnings=13450.00, cw_total_deductions=5454.20, cw_total_penalties=0, cw_os=-7995.80, cw_to_pay=7995.80, cw_to_collect=0,
            lw_trips=348, lw_gross_earnings=13090.00, lw_os=0.00, lw_week_number=29, lw_hisaab_number="HIS-2026-029-AQ7692", lw_status="settled_pay", growth_pct=12.5
        )
        
        d2 = AppDrivers(
            driver_id=294,
            operator_id=op1.app_operator_id,
            driver_code="LR-DRV-0294",
            phone="9140631755",
            full_name="Sushant",
            initials="S",
            profile_photo_url="https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150",
            aadhar_number="5678-9012-3456",
            blood_group="O+",
            dob=date(1989, 4, 22),
            address="Flat 301, Lakeview Apartments, Kondapur, Hyderabad - 500084",
            joined_date=date(2024, 11, 20),
            emergency_name="Kavitha",
            emergency_relation="Spouse/Wife",
            emergency_phone="9140631750",
            dl_number="TS09-2023-9876543",
            dl_expiry=date(2028, 3, 15),
            current_vehicle_id=2,
            current_allocation_id=2,
            vehicle_reg_number="TS09EV8812",
            vehicle_make="Tata",
            vehicle_model="Tigor EV",
            vehicle_variant="XZ+ EV",
            vehicle_color="Grey Metallic",
            vehicle_year=2022,
            vehicle_fuel_type="Electric",
            vehicle_odometer_km=98200,
            vehicle_allocated_from=date(2024, 11, 20),
            vehicle_daily_rate=900.00,
            rc_number="TS0920234521",
            rc_expiry=date(2037, 11, 1),
            insurance_number="TS094521890",
            insurance_expiry=date(2026, 11, 20),
            permit_type="Tourist Permit",
            permit_number="TS-09-TP-2023-8812",
            permit_expiry=date(2026, 12, 31),
            fitness_number="FIT2024123",
            fitness_expiry=date(2026, 11, 20),
            puc_expiry=date(2026, 9, 10),
            doc_last_updated=date(2026, 7, 25),
            deposit_total_req=6000.00,
            deposit_paid=5000.00,
            deposit_pending=1000.00,
            deposit_next_due=date(2026, 8, 15),
            joining_fee_agreed=1000.00,
            joining_fee_paid=1000.00,
            cumulative_owed=2884.80,
            assigned_manager_name="Ramesh Naik",
            assigned_manager_phone="9876543299",
            incentive_trips_target=260,
            incentive_reward_amt=1500.00,
            cw_incentive_trips_done=195,
            referral_code="SUSHANT294",
            referral_reward_amt=1000.00,
            contract_terms_url="https://letzryd.com/terms/driver",
            upi_id="sushant@paytm",
            bank_account_last4="8812",
            preferred_language="en",
            is_active=True,
            created_at=utc_now(),
            cw_uber_trips=95, cw_uber_revenue=12400, cw_uber_cash=9200, cw_uber_toll=320, cw_uber_incentive=2200, cw_uber_subscription=1100, cw_uber_km=1100,
            cw_ola_trips=60, cw_ola_revenue=6100, cw_ola_cash=4100, cw_ola_toll=140, cw_ola_incentive=1000, cw_ola_subscription=700, cw_ola_km=620,
            cw_rapido_trips=40, cw_rapido_revenue=4400, cw_rapido_cash=2600, cw_rapido_toll=60, cw_rapido_incentive=650, cw_rapido_subscription=280, cw_rapido_km=460,
            cw_vehicle_rent=4500, cw_maintenance_charge=900, cw_active_days=5, cw_tds=120.00, cw_challans=0, cw_accident_charge=0, cw_other_adjustment=0, cw_previous_outstanding=1034.80,
            cw_gps_total_km=2180.00, cw_gps_ideal_km=2400.00, cw_gps_dead_km=0, cw_gps_dead_pct=0, cw_gps_dead_penalty=0,
            cw_trips=195, cw_total_km=2180.00, cw_gross_earnings=11500.00, cw_total_deductions=13350.00, cw_total_penalties=0, cw_os=1850.00, cw_to_pay=0, cw_to_collect=1850.00,
            lw_trips=310, lw_gross_earnings=12200.00, lw_os=1034.80, lw_week_number=29, lw_hisaab_number="HIS-2026-029-EV8812", lw_status="to_collect", growth_pct=-8.2
        )
        
        d3 = AppDrivers(
            driver_id=312,
            operator_id=op1.app_operator_id,
            driver_code="LR-DRV-0312",
            phone="9930420065",
            full_name="Aayush",
            initials="A",
            profile_photo_url="https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=150",
            aadhar_number="9012-3456-7890",
            blood_group="A+",
            dob=date(1988, 12, 5),
            address="House 78, Jubilee Hills Road 45, Hyderabad - 500033",
            joined_date=date(2025, 1, 10),
            emergency_name="Sunita",
            emergency_relation="Spouse/Wife",
            emergency_phone="9930420060",
            dl_number="TS07-2022-5544332",
            dl_expiry=date(2027, 8, 30),
            current_vehicle_id=3,
            current_allocation_id=3,
            vehicle_reg_number="TS07EV4401",
            vehicle_make="Mahindra",
            vehicle_model="eVerito",
            vehicle_variant="D2 EV",
            vehicle_color="White",
            vehicle_year=2022,
            vehicle_fuel_type="Electric",
            vehicle_odometer_km=75600,
            vehicle_allocated_from=date(2025, 1, 10),
            vehicle_daily_rate=950.00,
            rc_number="TS0720221234",
            rc_expiry=date(2037, 1, 10),
            insurance_number="TS074401890",
            insurance_expiry=date(2027, 1, 10),
            permit_type="Tourist Permit",
            permit_number="TS-07-TP-2022-4401",
            permit_expiry=date(2026, 12, 31),
            fitness_number="FIT2024201",
            fitness_expiry=date(2026, 8, 30),
            puc_expiry=date(2026, 10, 1),
            doc_last_updated=date(2026, 7, 25),
            deposit_total_req=6000.00,
            deposit_paid=6000.00,
            deposit_pending=0.00,
            deposit_next_due=date(2026, 8, 15),
            joining_fee_agreed=1000.00,
            joining_fee_paid=1000.00,
            cumulative_owed=0.00,
            assigned_manager_name="Ramesh Naik",
            assigned_manager_phone="9876543299",
            incentive_trips_target=260,
            incentive_reward_amt=1500.00,
            cw_incentive_trips_done=218,
            referral_code="AAYUSH312",
            referral_reward_amt=1000.00,
            contract_terms_url="https://letzryd.com/terms/driver",
            upi_id="aayush@okicici",
            bank_account_last4="4401",
            preferred_language="en",
            is_active=True,
            created_at=utc_now(),
            cw_uber_trips=110, cw_uber_revenue=16200, cw_uber_cash=9800, cw_uber_toll=380, cw_uber_incentive=3100, cw_uber_subscription=1400, cw_uber_km=1200,
            cw_ola_trips=62, cw_ola_revenue=7100, cw_ola_cash=4000, cw_ola_toll=190, cw_ola_incentive=1300, cw_ola_subscription=850, cw_ola_km=690,
            cw_rapido_trips=46, cw_rapido_revenue=5400, cw_rapido_cash=2700, cw_rapido_toll=80, cw_rapido_incentive=900, cw_rapido_subscription=380, cw_rapido_km=500,
            cw_vehicle_rent=5700, cw_maintenance_charge=1140, cw_active_days=6, cw_tds=180.00, cw_challans=0, cw_accident_charge=0, cw_other_adjustment=0, cw_previous_outstanding=0,
            cw_gps_total_km=2390.00, cw_gps_ideal_km=2700.00, cw_gps_dead_km=0, cw_gps_dead_pct=0, cw_gps_dead_penalty=0,
            cw_trips=218, cw_total_km=2390.00, cw_gross_earnings=14200.00, cw_total_deductions=8020.00, cw_total_penalties=0, cw_os=-6180.00, cw_to_pay=6180.00, cw_to_collect=0,
            lw_trips=299, lw_gross_earnings=13800.00, lw_os=0.00, lw_week_number=29, lw_hisaab_number="HIS-2026-029-EV4401", lw_status="settled_pay", growth_pct=3.8
        )
        
        d4 = AppDrivers(
            driver_id=41,
            operator_id=op1.app_operator_id,
            driver_code="LR-HYD-0041",
            phone="9866941379",
            full_name="Anurag Driver",
            initials="AD",
            profile_photo_url="https://images.unsplash.com/photo-1522075469751-3a6694fb2f61?w=150",
            aadhar_number="1122-3344-5566",
            blood_group="O+",
            dob=date(1986, 6, 20),
            address="2-4-56, Old Alwal, Secunderabad - 500010",
            joined_date=date(2024, 8, 1),
            emergency_name="Lakshmi Devi",
            emergency_relation="Spouse/Wife",
            emergency_phone="9866941380",
            dl_number="TS07-2020-4455667",
            dl_expiry=date(2026, 12, 31),
            current_vehicle_id=4,
            current_allocation_id=4,
            vehicle_reg_number="TG07V0580",
            vehicle_make="Maruti",
            vehicle_model="Tour H3 CNG",
            vehicle_variant="Tour H3",
            vehicle_color="White",
            vehicle_year=2020,
            vehicle_fuel_type="CNG",
            vehicle_odometer_km=182000,
            vehicle_allocated_from=date(2024, 8, 1),
            vehicle_daily_rate=900.00,
            rc_number="TG0720200580",
            rc_expiry=date(2035, 8, 1),
            insurance_number="TG070580890",
            insurance_expiry=date(2026, 8, 1),
            permit_type="Tourist Permit",
            permit_number="TG-07-TP-2020-0580",
            permit_expiry=date(2026, 12, 31),
            fitness_number="FIT2023180",
            fitness_expiry=date(2026, 8, 1),
            puc_expiry=date(2026, 9, 1),
            doc_last_updated=date(2026, 7, 25),
            deposit_total_req=6000.00,
            deposit_paid=5000.00,
            deposit_pending=1000.00,
            deposit_next_due=date(2026, 8, 15),
            joining_fee_agreed=1000.00,
            joining_fee_paid=1000.00,
            cumulative_owed=0.00,
            assigned_manager_name="Kiran Kumar",
            assigned_manager_phone="9988776655",
            incentive_trips_target=200,
            incentive_reward_amt=1500.00,
            cw_incentive_trips_done=178,
            referral_code="ANURAGDRV",
            referral_reward_amt=1000.00,
            contract_terms_url="https://letzryd.com/terms/driver",
            upi_id="anuragdriver@upi",
            bank_account_last4="0580",
            preferred_language="en",
            is_active=True,
            created_at=utc_now(),
            cw_uber_trips=90, cw_uber_revenue=11800, cw_uber_cash=7800, cw_uber_toll=290, cw_uber_incentive=2400, cw_uber_subscription=1200, cw_uber_km=1000,
            cw_ola_trips=52, cw_ola_revenue=5600, cw_ola_cash=3400, cw_ola_toll=120, cw_ola_incentive=950, cw_ola_subscription=650, cw_ola_km=560,
            cw_rapido_trips=36, cw_rapido_revenue=3900, cw_rapido_cash=2100, cw_rapido_toll=50, cw_rapido_incentive=600, cw_rapido_subscription=260, cw_rapido_km=400,
            cw_vehicle_rent=4500, cw_maintenance_charge=900, cw_active_days=5, cw_tds=110.00, cw_challans=0, cw_accident_charge=0, cw_other_adjustment=0, cw_previous_outstanding=0,
            cw_gps_total_km=1960.00, cw_gps_ideal_km=2200.00, cw_gps_dead_km=0, cw_gps_dead_pct=0, cw_gps_dead_penalty=0,
            cw_trips=178, cw_total_km=1960.00, cw_gross_earnings=10350.00, cw_total_deductions=6870.00, cw_total_penalties=0, cw_os=-3480.00, cw_to_pay=3480.00, cw_to_collect=0,
            lw_trips=198, lw_gross_earnings=11200.00, lw_os=0.00, lw_week_number=29, lw_hisaab_number="HIS-2026-029-V0580", lw_status="settled_pay", growth_pct=-9.1
        )
        
        d5 = AppDrivers(
            driver_id=418,
            operator_id=op2.app_operator_id,
            driver_code="LR-DRV-0418",
            phone="9848012346",
            full_name="Mohammed Ali",
            initials="MA",
            profile_photo_url="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150",
            aadhar_number="3456-7890-1234",
            blood_group="B-",
            dob=date(1991, 3, 18),
            address="12-3-456, Mehdipatnam, Hyderabad - 500028",
            joined_date=date(2025, 2, 20),
            emergency_name="Fatima Begum",
            emergency_relation="Spouse/Wife",
            emergency_phone="9848012348",
            dl_number="TS08-2023-1122334",
            dl_expiry=date(2028, 6, 10),
            current_vehicle_id=5,
            current_allocation_id=5,
            vehicle_reg_number="TS08EV1129",
            vehicle_make="Tata",
            vehicle_model="XPRES-T EV",
            vehicle_variant="XM EV",
            vehicle_color="Silver",
            vehicle_year=2023,
            vehicle_fuel_type="Electric",
            vehicle_odometer_km=64300,
            vehicle_allocated_from=date(2025, 2, 20),
            vehicle_daily_rate=1050.00,
            rc_number="TS0820231129",
            rc_expiry=date(2038, 2, 20),
            insurance_number="TS081129890",
            insurance_expiry=date(2028, 2, 20),
            permit_type="Tourist Permit",
            permit_number="TS-08-TP-2023-1129",
            permit_expiry=date(2026, 12, 31),
            fitness_number="FIT2025089",
            fitness_expiry=date(2027, 2, 20),
            puc_expiry=date(2026, 11, 15),
            doc_last_updated=date(2026, 7, 25),
            deposit_total_req=7000.00,
            deposit_paid=7000.00,
            deposit_pending=0.00,
            deposit_next_due=date(2026, 8, 15),
            joining_fee_agreed=1000.00,
            joining_fee_paid=1000.00,
            cumulative_owed=0.00,
            assigned_manager_name="Arif Khan",
            assigned_manager_phone="9848012344",
            incentive_trips_target=260,
            incentive_reward_amt=1500.00,
            cw_incentive_trips_done=201,
            referral_code="MOHAMM418",
            referral_reward_amt=1000.00,
            contract_terms_url="https://letzryd.com/terms/driver",
            upi_id="mohammed.ali@axl",
            bank_account_last4="1129",
            preferred_language="en",
            is_active=True,
            created_at=utc_now(),
            cw_uber_trips=105, cw_uber_revenue=14600, cw_uber_cash=9100, cw_uber_toll=340, cw_uber_incentive=2800, cw_uber_subscription=1300, cw_uber_km=1150,
            cw_ola_trips=58, cw_ola_revenue=6400, cw_ola_cash=3800, cw_ola_toll=160, cw_ola_incentive=1100, cw_ola_subscription=750, cw_ola_km=630,
            cw_rapido_trips=38, cw_rapido_revenue=4600, cw_rapido_cash=2300, cw_rapido_toll=70, cw_rapido_incentive=750, cw_rapido_subscription=320, cw_rapido_km=460,
            cw_vehicle_rent=5250, cw_maintenance_charge=1050, cw_active_days=5, cw_tds=140.00, cw_challans=0, cw_accident_charge=0, cw_other_adjustment=0, cw_previous_outstanding=0,
            cw_gps_total_km=2240.00, cw_gps_ideal_km=2500.00, cw_gps_dead_km=0, cw_gps_dead_pct=0, cw_gps_dead_penalty=0,
            cw_trips=201, cw_total_km=2240.00, cw_gross_earnings=12800.00, cw_total_deductions=8220.00, cw_total_penalties=0, cw_os=-4580.00, cw_to_pay=4580.00, cw_to_collect=0,
            lw_trips=285, lw_gross_earnings=14500.00, lw_os=0.00, lw_week_number=29, lw_hisaab_number="HIS-2026-029-EV1129", lw_status="settled_pay", growth_pct=-2.1
        )
        
        d6 = AppDrivers(
            driver_id=501,
            operator_id=op2.app_operator_id,
            driver_code="LR-DRV-0501",
            phone="9848012347",
            full_name="Anil Verma",
            initials="AV",
            profile_photo_url="https://images.unsplash.com/photo-1492562080023-ab3db95bfbce?w=150",
            aadhar_number="7890-1234-5678",
            blood_group="AB+",
            dob=date(1993, 7, 30),
            address="8-2-120/A, Banjara Hills Road 2, Hyderabad - 500034",
            joined_date=date(2026, 5, 15),
            emergency_name="Meena Verma",
            emergency_relation="Spouse/Wife",
            emergency_phone="9848012349",
            dl_number="TS09-2023-9988776",
            dl_expiry=date(2028, 9, 20),
            current_vehicle_id=6,
            current_allocation_id=6,
            vehicle_reg_number="TS09EV9900",
            vehicle_make="BYD",
            vehicle_model="e6 EV",
            vehicle_variant="e6 Standard",
            vehicle_color="Pearl White",
            vehicle_year=2023,
            vehicle_fuel_type="Electric",
            vehicle_odometer_km=18400,
            vehicle_allocated_from=date(2026, 5, 15),
            vehicle_daily_rate=1100.00,
            rc_number="TS0920239900",
            rc_expiry=date(2038, 5, 15),
            insurance_number="TS099900890",
            insurance_expiry=date(2028, 5, 15),
            permit_type="Tourist Permit",
            permit_number="TS-09-TP-2023-9900",
            permit_expiry=date(2026, 12, 31),
            fitness_number="FIT2025341",
            fitness_expiry=date(2027, 5, 15),
            puc_expiry=date(2026, 12, 1),
            doc_last_updated=date(2026, 7, 25),
            deposit_total_req=8000.00,
            deposit_paid=4000.00,
            deposit_pending=4000.00,
            deposit_next_due=date(2026, 8, 15),
            joining_fee_agreed=1000.00,
            joining_fee_paid=1000.00,
            cumulative_owed=1820.50,
            assigned_manager_name="Arif Khan",
            assigned_manager_phone="9848012344",
            incentive_trips_target=260,
            incentive_reward_amt=1500.00,
            cw_incentive_trips_done=64,
            referral_code="ANILV501",
            referral_reward_amt=1000.00,
            contract_terms_url="https://letzryd.com/terms/driver",
            upi_id="anil.verma@icici",
            bank_account_last4="9900",
            preferred_language="en",
            is_active=True,
            created_at=utc_now(),
            cw_uber_trips=35, cw_uber_revenue=4800, cw_uber_cash=3600, cw_uber_toll=110, cw_uber_incentive=850, cw_uber_subscription=420, cw_uber_km=390,
            cw_ola_trips=18, cw_ola_revenue=2100, cw_ola_cash=1400, cw_ola_toll=50, cw_ola_incentive=400, cw_ola_subscription=250, cw_ola_km=200,
            cw_rapido_trips=11, cw_rapido_revenue=1300, cw_rapido_cash=850, cw_rapido_toll=20, cw_rapido_incentive=250, cw_rapido_subscription=110, cw_rapido_km=120,
            cw_vehicle_rent=2200, cw_maintenance_charge=440, cw_active_days=2, cw_tds=50.00, cw_challans=500, cw_accident_charge=0, cw_other_adjustment=0, cw_previous_outstanding=0,
            cw_gps_total_km=710.00, cw_gps_ideal_km=800.00, cw_gps_dead_km=0, cw_gps_dead_pct=0, cw_gps_dead_penalty=0,
            cw_trips=64, cw_total_km=710.00, cw_gross_earnings=4200.00, cw_total_deductions=6020.50, cw_total_penalties=0, cw_os=1820.50, cw_to_pay=0, cw_to_collect=1820.50,
            lw_trips=210, lw_gross_earnings=11000.00, lw_os=0.00, lw_week_number=29, lw_hisaab_number="HIS-2026-029-EV9900", lw_status="settled_pay", growth_pct=-15.3
        )
        
        db.add_all([d1, d2, d3, d4, d5, d6])
        db.commit()
        
        # 3. Hisaab Records (3 weeks per driver = 18 total)
        hisaabs = []
        drivers_list = [d1, d2, d3, d4, d5, d6]
        
        for drv in drivers_list:
            op_id = drv.operator_id
            reg = drv.vehicle_reg_number
            daily = float(drv.vehicle_daily_rate or 1000)
            
            # Week 30 (Active, In Progress)
            hisaabs.append(make_hisaab(
                drv.app_driver_id, op_id, 30, date(2026, 7, 21), date(2026, 7, 27), drv.cw_active_days,
                "in_progress", False,
                drv.cw_uber_trips, float(drv.cw_uber_revenue), float(drv.cw_uber_cash), float(drv.cw_uber_toll), float(drv.cw_uber_incentive), float(drv.cw_uber_subscription), float(drv.cw_uber_km),
                drv.cw_ola_trips, float(drv.cw_ola_revenue), float(drv.cw_ola_cash), float(drv.cw_ola_toll), float(drv.cw_ola_incentive), float(drv.cw_ola_subscription), float(drv.cw_ola_km),
                drv.cw_rapido_trips, float(drv.cw_rapido_revenue), float(drv.cw_rapido_cash), float(drv.cw_rapido_toll), float(drv.cw_rapido_incentive), float(drv.cw_rapido_subscription), float(drv.cw_rapido_km),
                daily, float(drv.cw_vehicle_rent), float(drv.cw_maintenance_charge), float(drv.cw_tds), float(drv.cw_challans), float(drv.cw_accident_charge), float(drv.cw_other_adjustment), float(drv.cw_previous_outstanding),
                float(drv.cw_gps_total_km or 0), float(drv.cw_gps_ideal_km or 0), float(drv.cw_gps_dead_km or 0), float(drv.cw_gps_dead_penalty or 0),
                float(drv.cw_gross_earnings), float(drv.cw_total_deductions), float(drv.cw_os), float(drv.cw_to_pay), float(drv.cw_to_collect),
                float(drv.growth_pct or 0), daily * drv.cw_active_days, "Current active week statement in progress.", reg
            ))
            
            # Week 29 (Locked Past Week)
            lw_status = drv.lw_status
            lw_earnings = float(drv.lw_gross_earnings)
            hisaabs.append(make_hisaab(
                drv.app_driver_id, op_id, 29, date(2026, 7, 14), date(2026, 7, 20), 6,
                lw_status, True,
                int(drv.lw_trips * 0.55), float(lw_earnings * 0.58), float(lw_earnings * 0.40), 450, 2600, 1200, 1450,
                int(drv.lw_trips * 0.28), float(lw_earnings * 0.26), float(lw_earnings * 0.18), 180, 1100, 750, 720,
                int(drv.lw_trips * 0.17), float(lw_earnings * 0.16), float(lw_earnings * 0.10), 80, 750, 320, 480,
                daily, daily * 6, daily * 1.2, 220.00, 0, 0, 0, 0,
                2650.00, 2900.00, 0, 0,
                float(drv.lw_gross_earnings), float(daily * 7.2 + 220), float(drv.lw_os),
                0 if lw_status == "to_collect" else float(lw_earnings - (daily * 7.2 + 220)),
                float(drv.lw_os) if lw_status == "to_collect" else 0,
                -4.5, daily * 6, f"Locked Week 29 statement. Status: {lw_status}", reg
            ))
            
            # Week 28 (Settled Historical Week)
            hisaabs.append(make_hisaab(
                drv.app_driver_id, op_id, 28, date(2026, 7, 7), date(2026, 7, 13), 6,
                "settled_pay", True,
                165, 18500, 12000, 520, 3600, 1600, 1550,
                75, 8200, 5100, 210, 1400, 950, 780,
                50, 5900, 3100, 110, 950, 420, 540,
                daily, daily * 6, daily * 1.2, 240.00, 0, 0, 0, 0,
                2870.00, 3100.00, 0, 0,
                15200.00, daily * 7.2 + 240, 0.00, 7800.00, 0.00,
                6.8, daily * 6, "Fully settled and paid via direct bank transfer.", reg
            ))
            
        db.add_all(hisaabs)
        db.commit()
        
        # 4. Support Tickets (2 per driver = 12 total)
        tickets = []
        for drv in drivers_list:
            tickets.append(AppSupportTickets(
                ticket_number=f"TKT-2026-{1000 + drv.app_driver_id}",
                creator_type="driver",
                creator_id=drv.app_driver_id,
                category="Settlement & Payout",
                subject="Dispute regarding toll adjustment in Week 29",
                description="Airport toll receipt of Rs 180 was not captured in the weekly report.",
                status="open",
                priority="medium",
                created_at=utc_now() - timedelta(days=2)
            ))
            tickets.append(AppSupportTickets(
                ticket_number=f"TKT-2026-{2000 + drv.app_driver_id}",
                creator_type="driver",
                creator_id=drv.app_driver_id,
                category="Vehicle Maintenance",
                subject="Brake pad replacement scheduled",
                description="Routine maintenance completed at authorized service hub.",
                status="resolved",
                priority="low",
                created_at=utc_now() - timedelta(days=6),
                resolved_at=utc_now() - timedelta(days=4),
                resolution_note="Vehicle serviced and fitness verified by hub technician."
            ))
            
        db.add_all(tickets)
        db.commit()
        
        # 5. Notifications
        notifs = []
        for drv in drivers_list:
            notifs.append(AppNotifications(
                target_type="driver",
                target_id=drv.app_driver_id,
                notif_type="hisaab",
                severity="info",
                title="Hisaab Statement Ready",
                message=f"Your weekly Hisaab for {drv.vehicle_reg_number} is ready for review.",
                icon="ReceiptIndianRupee",
                is_read=False,
                created_at=utc_now() - timedelta(hours=3)
            ))
            notifs.append(AppNotifications(
                target_type="driver",
                target_id=drv.app_driver_id,
                notif_type="payment",
                severity="warning" if drv.cw_to_collect > 0 else "info",
                title="Settlement Update",
                message="Settlement dues processed to your registered UPI / account." if drv.cw_to_pay > 0 else "Please clear pending balance before cutoff to maintain active rating.",
                icon="Wallet",
                is_read=False,
                created_at=utc_now() - timedelta(hours=8)
            ))
            notifs.append(AppNotifications(
                target_type="driver",
                target_id=drv.app_driver_id,
                notif_type="announcement",
                severity="info",
                title="LetzRyd Partner Update",
                message="New incentive bonus slabs unlocked for monsoon peak hours.",
                icon="Bell",
                is_read=False,
                created_at=utc_now() - timedelta(days=1)
            ))
            
        for op in [op1, op2]:
            notifs.append(AppNotifications(
                target_type="operator",
                target_id=op.app_operator_id,
                notif_type="hisaab",
                severity="info",
                title="Fleet Weekly Summary Ready",
                message=f"Consolidated Hisaab for {op.company_name} is now available.",
                icon="ReceiptIndianRupee",
                is_read=False,
                created_at=utc_now() - timedelta(hours=4)
            ))
            
        db.add_all(notifs)
        db.commit()
        
        # 6. Referral Leads
        refs = [
            AppReferralLeads(referred_by_type="driver", referred_by_driver_id=d1.app_driver_id, lead_name="Arjun Mehta", lead_phone="9911223344", referral_code_used="RAJESH157", status="submitted", rides_completed=0, reward_amount=1000, reward_credited=False, submitted_at=utc_now(), created_at=utc_now(), updated_at=utc_now()),
            AppReferralLeads(referred_by_type="driver", referred_by_driver_id=d2.app_driver_id, lead_name="Ramesh Rao", lead_phone="9922334455", referral_code_used="SURESH294", status="submitted", rides_completed=0, reward_amount=1000, reward_credited=False, submitted_at=utc_now(), created_at=utc_now(), updated_at=utc_now()),
            AppReferralLeads(referred_by_type="driver", referred_by_driver_id=d3.app_driver_id, lead_name="Pradeep K", lead_phone="9933445566", referral_code_used="VIKRAM312", status="joined", rides_completed=260, reward_amount=1000, reward_credited=True, submitted_at=utc_now(), created_at=utc_now(), updated_at=utc_now()),
            AppReferralLeads(referred_by_type="driver", referred_by_driver_id=d4.app_driver_id, lead_name="Ravi Patel", lead_phone="9866941381", referral_code_used="VARA0041", status="submitted", rides_completed=0, reward_amount=1000, reward_credited=False, submitted_at=utc_now(), created_at=utc_now(), updated_at=utc_now()),
            AppReferralLeads(referred_by_type="driver", referred_by_driver_id=d5.app_driver_id, lead_name="Sohail Ahmed", lead_phone="9944556677", referral_code_used="MOHAMM418", status="submitted", rides_completed=0, reward_amount=1000, reward_credited=False, submitted_at=utc_now(), created_at=utc_now(), updated_at=utc_now()),
            AppReferralLeads(referred_by_type="driver", referred_by_driver_id=d6.app_driver_id, lead_name="Deepak Sharma", lead_phone="9955667788", referral_code_used="ANILV501", status="submitted", rides_completed=0, reward_amount=1000, reward_credited=False, submitted_at=utc_now(), created_at=utc_now(), updated_at=utc_now()),
        ]
        db.add_all(refs)
        db.commit()

        print("Database seeded successfully! All variables 100% filled for all 6 drivers and 2 operators.")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
