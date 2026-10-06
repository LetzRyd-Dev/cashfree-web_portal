from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Union
from app.database import get_db
from app.models.app_models import AppHisaabs, AppDrivers, AppOperators
from app.schemas.app_schemas import HisaabBreakdownResponse
from app.services.platform_aggregator import aggregate_raw_platform_data
from app.services.helpers import clean_phone_number, resolve_driver, resolve_operator

router = APIRouter(prefix="/hisaabs", tags=["Hisaabs Ledger"])

@router.get("/driver/by-phone/{phone}")
@router.get("/driver/phone/{phone}")
def get_hisaabs_by_driver_phone(phone: str, db: Session = Depends(get_db)):
    clean = clean_phone_number(phone)
    driver = resolve_driver(clean, db)
    if not driver:
        raise HTTPException(status_code=404, detail=f"No driver found with phone {phone}")
    target_ids = [driver.app_driver_id]
    if driver.driver_id:
        target_ids.append(driver.driver_id)
    hisaabs = db.query(AppHisaabs).filter(AppHisaabs.app_driver_id.in_(target_ids)).order_by(AppHisaabs.week_number.desc()).all()
    if not hisaabs and driver.vehicle_reg_number:
        clean_v = driver.vehicle_reg_number.replace(' ', '').replace('-', '').upper()
        hisaabs = db.query(AppHisaabs).filter(
            AppHisaabs.hisaab_number.ilike(f"%{clean_v}%")
        ).order_by(AppHisaabs.week_number.desc()).all()
    return {"driver_id": driver.app_driver_id, "count": len(hisaabs), "data": [_map_hisaab(h) for h in hisaabs]}

@router.get("/driver/{driver_id}")
def get_driver_hisaabs(driver_id: Union[int, str], db: Session = Depends(get_db)):
    driver = resolve_driver(str(driver_id), db)
    target_ids = []
    if driver:
        if driver.app_driver_id:
            target_ids.append(driver.app_driver_id)
        if driver.driver_id:
            target_ids.append(driver.driver_id)
    elif str(driver_id).isdigit():
        target_ids.append(int(driver_id))

    hisaabs = []
    if target_ids:
        hisaabs = db.query(AppHisaabs).filter(
            AppHisaabs.app_driver_id.in_(target_ids)
        ).order_by(AppHisaabs.week_number.desc()).all()

    if not hisaabs and driver and driver.vehicle_reg_number:
        clean_v = driver.vehicle_reg_number.replace(' ', '').replace('-', '').upper()
        hisaabs = db.query(AppHisaabs).filter(
            AppHisaabs.hisaab_number.ilike(f"%{clean_v}%")
        ).order_by(AppHisaabs.week_number.desc()).all()
    return {"driver_id": driver.app_driver_id if driver else (target_ids[0] if target_ids else driver_id), "count": len(hisaabs), "data": [_map_hisaab(h) for h in hisaabs]}

@router.get("/vehicle/{vehicle_number}")
def get_vehicle_hisaabs(vehicle_number: str, db: Session = Depends(get_db)):
    clean_v = vehicle_number.replace(' ', '').replace('-', '').upper()
    hisaabs = db.query(AppHisaabs).filter(
        AppHisaabs.hisaab_number.ilike(f"%{clean_v}%")
    ).order_by(AppHisaabs.week_number.desc()).all()
    return {"vehicle_number": vehicle_number, "count": len(hisaabs), "data": [_map_hisaab(h) for h in hisaabs]}

from sqlalchemy import text

@router.get("/operator/{operator_id}")
def get_operator_hisaabs(operator_id: Union[int, str], db: Session = Depends(get_db)):
    op = resolve_operator(str(operator_id), db)
    target_op_id = op.app_operator_id if op else (int(operator_id) if str(operator_id).isdigit() else None)
    core_op_id = op.operator_id if (op and op.operator_id) else target_op_id
    if target_op_id is None:
        return {"operator_id": operator_id, "count": 0, "data": []}
    
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
            SUM(COALESCE(uber_km, 0.00)) as uber_km,
            SUM(COALESCE(ola_trips, 0)) as ola_trips,
            SUM(COALESCE(ola_revenue, 0.00)) as ola_revenue,
            SUM(COALESCE(ola_cash, 0.00)) as ola_cash,
            SUM(COALESCE(ola_toll, 0.00)) as ola_toll,
            SUM(COALESCE(ola_incentive, 0.00)) as ola_incentive,
            SUM(COALESCE(ola_subscription, 0.00)) as ola_subscription,
            SUM(COALESCE(ola_km, 0.00)) as ola_km,
            SUM(COALESCE(rapido_trips, 0)) as rapido_trips,
            SUM(COALESCE(rapido_revenue, 0.00)) as rapido_revenue,
            SUM(COALESCE(rapido_cash, 0.00)) as rapido_cash,
            SUM(COALESCE(rapido_toll, 0.00)) as rapido_toll,
            SUM(COALESCE(rapido_incentive, 0.00)) as rapido_incentive,
            SUM(COALESCE(rapido_subscription, 0.00)) as rapido_subscription,
            SUM(COALESCE(rapido_km, 0.00)) as rapido_km,
            SUM(COALESCE(total_km, 0.00)) as total_km,
            SUM(COALESCE(letzryd_earning, 0.00)) as letzryd_earning,
            SUM(COALESCE(paid_amount, 0.00)) as paid_amount
        FROM app_hisaabs
        WHERE app_operator_id IN (:op_id, :core_op_id)
        GROUP BY week_number
        ORDER BY week_number DESC
    """), {"op_id": target_op_id, "core_op_id": core_op_id}).mappings().fetchall()

    op_code = op.operator_code if op else str(target_op_id)
    data = []
    for r in rows:
        w_num = r['week_number']
        stat = "settled" if w_num < 40 else "in_progress"
        h_no = f"HIS-OP-2026-{w_num:03d}-{op_code}"
        to_pay_val = float(r['to_pay'] or 0.0)
        to_collect_val = float(r['to_collect'] or 0.0)
        
        data.append(HisaabBreakdownResponse(
            app_hisaab_id=w_num,
            app_driver_id=0,
            app_operator_id=target_op_id,
            hisaab_number=h_no,
            week_number=w_num,
            period_start=r['period_start'],
            period_end=r['period_end'],
            days_count=7,
            status=stat,
            is_locked=False,
            growth_pct=0.0,
            uber_trips=int(r['uber_trips'] or 0),
            uber_revenue=float(r['uber_revenue'] or 0.0),
            uber_cash=float(r['uber_cash'] or 0.0),
            uber_toll=float(r['uber_toll'] or 0.0),
            uber_incentive=float(r['uber_incentive'] or 0.0),
            uber_subscription=float(r['uber_subscription'] or 0.0),
            uber_km=float(r['uber_km'] or 0.0),
            ola_trips=int(r['ola_trips'] or 0),
            ola_revenue=float(r['ola_revenue'] or 0.0),
            ola_cash=float(r['ola_cash'] or 0.0),
            ola_toll=float(r['ola_toll'] or 0.0),
            ola_incentive=float(r['ola_incentive'] or 0.0),
            ola_subscription=float(r['ola_subscription'] or 0.0),
            ola_km=float(r['ola_km'] or 0.0),
            rapido_trips=int(r['rapido_trips'] or 0),
            rapido_revenue=float(r['rapido_revenue'] or 0.0),
            rapido_cash=float(r['rapido_cash'] or 0.0),
            rapido_toll=float(r['rapido_toll'] or 0.0),
            rapido_incentive=float(r['rapido_incentive'] or 0.0),
            rapido_subscription=float(r['rapido_subscription'] or 0.0),
            rapido_km=float(r['rapido_km'] or 0.0),
            vehicle_daily_rate=0.0,
            vehicle_rent=float(r['vehicle_rent'] or 0.0),
            maintenance_charge=float(r['maintenance_charge'] or 0.0),
            tds_amount=float(r['tds_amount'] or 0.0),
            challan_amount=float(r['challan_amount'] or 0.0),
            accident_charge=float(r['accident_charge'] or 0.0),
            other_adjustment=float(r['other_adjustment'] or 0.0),
            previous_outstanding=float(r['previous_outstanding'] or 0.0),
            gps_total_km=0.0,
            gps_ideal_km=0.0,
            gps_dead_km=0.0,
            gps_dead_pct=0.0,
            gps_dead_penalty=0.0,
            gps_free_dead_pct=20.0,
            gps_penalty_rate=5.0,
            completed_trips=int(r['completed_trips'] or 0),
            total_km=float(r['total_km'] or 0.0),
            total_gross_earnings=float(r['total_gross_earnings'] or 0.0),
            total_deductions=float(r['total_deductions'] or 0.0),
            total_penalties=float(r['total_penalties'] or 0.0),
            current_period_os=float(to_collect_val - to_pay_val),
            to_collect=to_collect_val,
            to_pay=to_pay_val,
            letzryd_earning=float(r['letzryd_earning'] or 0.0),
            notes=f"Fleet aggregate across {r['active_vehicles']} vehicles",
            last_refreshed_at=None,
            paid_amount=float(r['paid_amount'] or 0.0),
            payment_status="settled" if stat == "settled" else "unpaid"
        ))
    return {"operator_id": target_op_id, "count": len(data), "data": data}

@router.get("/{hisaab_id}", response_model=HisaabBreakdownResponse)
def get_hisaab_by_id(hisaab_id: Union[int, str], db: Session = Depends(get_db)):
    hid_str = str(hisaab_id).strip()
    hisaab = None
    if hid_str.isdigit():
        hisaab = db.query(AppHisaabs).filter(AppHisaabs.app_hisaab_id == int(hid_str)).first()
        if not hisaab:
            hisaab = db.query(AppHisaabs).filter(AppHisaabs.hisaab_id == int(hid_str)).first()
    if not hisaab:
        hisaab = db.query(AppHisaabs).filter(AppHisaabs.hisaab_number == hid_str).first()
    if not hisaab:
        raise HTTPException(status_code=404, detail="Hisaab record not found")
    return _map_hisaab(hisaab)

@router.post("/recalculate")
def trigger_raw_recalculation(week_number: int = 30, db: Session = Depends(get_db)):
    processed = aggregate_raw_platform_data(db, week_number)
    return {"success": True, "message": f"Processed raw platform data for {processed} vehicles"}

def _map_hisaab(h: AppHisaabs) -> HisaabBreakdownResponse:
    return HisaabBreakdownResponse(
        app_hisaab_id=h.app_hisaab_id,
        app_driver_id=h.app_driver_id,
        hisaab_number=h.hisaab_number or "",
        week_number=h.week_number or 0,
        period_start=h.period_start,
        period_end=h.period_end,
        days_count=h.days_count or 7,
        status=h.status or "in_progress",
        is_locked=h.is_locked or False,
        growth_pct=float(h.growth_pct or 0.0),
        uber_trips=h.uber_trips or 0,
        uber_revenue=float(h.uber_revenue or 0.0),
        uber_cash=float(h.uber_cash or 0.0),
        uber_toll=float(h.uber_toll or 0.0),
        uber_incentive=float(h.uber_incentive or 0.0),
        uber_subscription=float(h.uber_subscription or 0.0),
        uber_km=float(h.uber_km or 0.0),
        ola_trips=h.ola_trips or 0,
        ola_revenue=float(h.ola_revenue or 0.0),
        ola_cash=float(h.ola_cash or 0.0),
        ola_toll=float(h.ola_toll or 0.0),
        ola_incentive=float(h.ola_incentive or 0.0),
        ola_subscription=float(h.ola_subscription or 0.0),
        ola_km=float(h.ola_km or 0.0),
        rapido_trips=h.rapido_trips or 0,
        rapido_revenue=float(h.rapido_revenue or 0.0),
        rapido_cash=float(h.rapido_cash or 0.0),
        rapido_toll=float(h.rapido_toll or 0.0),
        rapido_incentive=float(h.rapido_incentive or 0.0),
        rapido_subscription=float(h.rapido_subscription or 0.0),
        rapido_km=float(h.rapido_km or 0.0),
        vehicle_daily_rate=float(h.vehicle_daily_rate or 1000.0),
        vehicle_rent=float(h.vehicle_rent or 0.0),
        maintenance_charge=float(h.maintenance_charge or 0.0),
        tds_amount=float(h.tds_amount or 0.0),
        challan_amount=float(h.challan_amount or 0.0),
        accident_charge=float(h.accident_charge or 0.0),
        other_adjustment=float(h.other_adjustment or 0.0),
        previous_outstanding=float(h.previous_outstanding or 0.0),
        gps_total_km=float(h.gps_total_km or 0.0),
        gps_ideal_km=float(h.gps_ideal_km or 0.0),
        gps_dead_km=float(h.gps_dead_km or 0.0),
        gps_dead_pct=float(h.gps_dead_pct or 0.0),
        gps_dead_penalty=float(h.gps_dead_penalty or 0.0),
        gps_free_dead_pct=float(h.gps_free_dead_pct or 20.0),
        gps_penalty_rate=float(h.gps_penalty_rate or 5.0),
        completed_trips=h.completed_trips or 0,
        total_km=float(h.total_km or 0.0),
        total_gross_earnings=float(h.total_gross_earnings or 0.0),
        total_deductions=float(h.total_deductions or 0.0),
        total_penalties=float(h.total_penalties or 0.0),
        current_period_os=float(h.current_period_os or 0.0),
        to_collect=float(h.to_collect or 0.0),
        to_pay=float(h.to_pay or 0.0),
        letzryd_earning=float(h.letzryd_earning or 0.0),
        notes=h.notes or "",
        last_refreshed_at=str(h.last_refreshed_at) if h.last_refreshed_at else None,
        paid_amount=float(h.paid_amount or 0.0),
        payment_status=h.payment_status or "unpaid"
    )

