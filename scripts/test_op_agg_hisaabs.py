from app.database import SessionLocal
from sqlalchemy import text
from app.models.app_models import AppHisaabs, AppOperators
from app.schemas.app_schemas import HisaabBreakdownResponse
import datetime
from decimal import Decimal

db = SessionLocal()

def get_operator_aggregated_hisaabs(op_id: int):
    op = db.query(AppOperators).filter((AppOperators.app_operator_id == op_id) | (AppOperators.operator_id == op_id)).first()
    if not op:
        return []
    
    # Query distinct weeks for this operator
    rows = db.execute(text("""
        SELECT 
            week_number,
            MIN(period_start) as period_start,
            MAX(period_end) as period_end,
            COUNT(DISTINCT app_driver_id) as active_vehicles,
            SUM(COALESCE(completed_trips, 0)) as completed_trips,
            SUM(COALESCE(total_gross_earnings, 0.00)) as total_gross_earnings,
            SUM(COALESCE(total_deductions, 0.00)) as total_deductions,
            SUM(COALESCE(total_penalties, 0.00)) as total_penalties,
            SUM(COALESCE(vehicle_rent, 0.00)) as vehicle_rent,
            SUM(COALESCE(maintenance_charge, 0.00)) as maintenance_charge,
            SUM(COALESCE(tds_amount, 0.00)) as tds_amount,
            SUM(COALESCE(challan_amount, 0.00)) as challan_amount,
            SUM(COALESCE(accident_charge, 0.00)) as accident_charge,
            SUM(COALESCE(other_adjustment, 0.00)) as other_adjustment,
            SUM(COALESCE(previous_outstanding, 0.00)) as previous_outstanding,
            SUM(COALESCE(to_pay, 0.00)) as to_pay,
            SUM(COALESCE(to_collect, 0.00)) as to_collect,
            SUM(COALESCE(uber_trips, 0)) as uber_trips,
            SUM(COALESCE(uber_revenue, 0.00)) as uber_revenue,
            SUM(COALESCE(uber_cash, 0.00)) as uber_cash,
            SUM(COALESCE(uber_toll, 0.00)) as uber_toll,
            SUM(COALESCE(uber_incentive, 0.00)) as uber_incentive,
            SUM(COALESCE(uber_subscription, 0.00)) as uber_subscription,
            SUM(COALESCE(ola_trips, 0)) as ola_trips,
            SUM(COALESCE(ola_revenue, 0.00)) as ola_revenue,
            SUM(COALESCE(ola_cash, 0.00)) as ola_cash,
            SUM(COALESCE(ola_toll, 0.00)) as ola_toll,
            SUM(COALESCE(ola_incentive, 0.00)) as ola_incentive,
            SUM(COALESCE(ola_subscription, 0.00)) as ola_subscription,
            SUM(COALESCE(rapido_trips, 0)) as rapido_trips,
            SUM(COALESCE(rapido_revenue, 0.00)) as rapido_revenue,
            SUM(COALESCE(rapido_cash, 0.00)) as rapido_cash,
            SUM(COALESCE(rapido_toll, 0.00)) as rapido_toll,
            SUM(COALESCE(rapido_incentive, 0.00)) as rapido_incentive,
            SUM(COALESCE(rapido_subscription, 0.00)) as rapido_subscription
        FROM app_hisaabs
        WHERE app_operator_id = :op_id
        GROUP BY week_number
        ORDER BY week_number DESC
    """), {"op_id": op.app_operator_id}).mappings().fetchall()
    
    result = []
    for r in rows:
        w_num = r['week_number']
        net_diff = r['total_gross_earnings'] - r['total_deductions']
        stat = "settled" if w_num < 40 else "in_progress"
        h_no = f"HIS-OP-2026-{w_num:03d}-{op.operator_code or str(op.app_operator_id)}"
        
        result.append({
            "week_number": w_num,
            "hisaab_number": h_no,
            "period_start": str(r['period_start']),
            "period_end": str(r['period_end']),
            "status": stat,
            "active_vehicles": r['active_vehicles'],
            "completed_trips": r['completed_trips'],
            "total_gross_earnings": float(r['total_gross_earnings']),
            "total_deductions": float(r['total_deductions']),
            "to_pay": float(r['to_pay']),
            "to_collect": float(r['to_collect']),
            "vehicle_rent": float(r['vehicle_rent']),
            "uber_revenue": float(r['uber_revenue']),
            "uber_trips": r['uber_trips']
        })
    return result

for test_id in [475, 1, 742]:
    res = get_operator_aggregated_hisaabs(test_id)
    print(f"Op {test_id} aggregated weeks: {len(res)}")
    for row in res[:3]:
        print(" ", row)

db.close()
