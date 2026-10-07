from typing import Union, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.app_models import AppOperators, AppDrivers, AppHisaabs, AppDriverAllocations
from app.schemas.app_schemas import OperatorProfileResponse, OperatorFleetResponse, FleetVehicleResponse, FleetDriverItemResponse
from app.services.helpers import clean_phone_number, resolve_operator

router = APIRouter(prefix="/operators", tags=["Operators"])

@router.get("/by-phone/{phone}", response_model=OperatorProfileResponse)
@router.get("/phone/{phone}", response_model=OperatorProfileResponse)
def get_operator_by_phone(phone: str, db: Session = Depends(get_db)):
    clean = clean_phone_number(phone)
    op = resolve_operator(clean, db)
    if not op:
        raise HTTPException(status_code=404, detail=f"No operator found with phone {phone}")
    return _map_operator(op, db)

@router.get("/me", response_model=OperatorProfileResponse)
def get_current_operator(phone: str = "9691938866", db: Session = Depends(get_db)):
    clean = clean_phone_number(phone)
    op = resolve_operator(clean, db)
    if not op:
        op = db.query(AppOperators).first()
        if not op:
            raise HTTPException(status_code=404, detail="Operator not found")
    return _map_operator(op, db)

@router.get("/{operator_id}/fleet-summary", response_model=OperatorFleetResponse)
def get_operator_fleet_summary(operator_id: Union[int, str], week_number: Optional[int] = None, db: Session = Depends(get_db)):
    op = resolve_operator(str(operator_id), db)
    if not op:
        raise HTTPException(status_code=404, detail="Operator not found")
    
    drivers = db.query(AppDrivers).filter(
        AppDrivers.operator_id == op.app_operator_id
    ).order_by(AppDrivers.app_driver_id).all()

    vehicles = []
    seen_vehicles = {}
    driver_items = []
    for d in drivers:
        hisaabs = db.query(AppHisaabs).filter(
            AppHisaabs.app_driver_id == d.app_driver_id
        ).order_by(AppHisaabs.week_number.desc()).all()

        veh_num = d.vehicle_reg_number
        if not veh_num:
            alloc = db.query(AppDriverAllocations).filter(
                AppDriverAllocations.app_driver_id == d.app_driver_id
            ).order_by(AppDriverAllocations.app_allocation_id.desc()).first()
            if alloc and alloc.vehicle_number:
                veh_num = alloc.vehicle_number

        if not veh_num:
            veh_num = f"UNASSIGNED-{d.app_driver_id}"

        clean_v = veh_num.replace(' ', '').replace('-', '').upper()

        # Fallback to vehicle number search in hisaabs if driver has none
        if not hisaabs and not veh_num.startswith("UNASSIGNED"):
            hisaabs = db.query(AppHisaabs).filter(
                AppHisaabs.hisaab_number.ilike(f"%{clean_v}%")
            ).order_by(AppHisaabs.week_number.desc()).all()

        cw_os = 0.0
        if hisaabs:
            latest_h = hisaabs[0]
            to_pay = float(latest_h.to_pay if getattr(latest_h, 'to_pay', None) is not None else 0.0)
            to_col = float(latest_h.to_collect if getattr(latest_h, 'to_collect', None) is not None else 0.0)
            if to_pay == 0.0 and to_col == 0.0 and getattr(latest_h, 'current_period_os', None) is not None:
                cpos = float(latest_h.current_period_os)
                if cpos > 0:
                    to_col = cpos
                elif cpos < 0:
                    to_pay = abs(cpos)
            if to_pay > 0 and to_col > 0:
                cw_os = round(to_col - to_pay, 2)
            elif to_pay > 0:
                cw_os = -to_pay
            elif to_col > 0:
                cw_os = to_col
            else:
                cw_os = float(d.cw_os or 0.0)
        elif d.cw_to_pay and float(d.cw_to_pay) > 0:
            cw_os = -float(d.cw_to_pay)
        elif d.cw_to_collect and float(d.cw_to_collect) > 0:
            cw_os = float(d.cw_to_collect)
        else:
            cw_os = float(d.cw_os or 0.0)

        # Build individual driver roster item
        assigned_label = d.vehicle_reg_number if d.vehicle_reg_number else ("Unassigned" if veh_num.startswith("UNASSIGNED") else f"{veh_num} (Alloc)")
        driver_items.append(FleetDriverItemResponse(
            app_driver_id=d.app_driver_id,
            driver_code=d.driver_code or f"DRV-{d.app_driver_id}",
            full_name=d.full_name or "Driver",
            phone=d.phone or "",
            assigned_vehicle=assigned_label,
            vehicle_model=d.vehicle_model or "Maruti Wagonr Tour H3 CNG",
            rental_plan=getattr(d, 'rental_plan', None) or "Fixed",
            current_week_os=cw_os,
            status="active" if d.is_active else "idle",
            hisaab_count=len(hisaabs)
        ))

        if not veh_num.startswith("UNASSIGNED"):
            veh_obj = FleetVehicleResponse(
                vehicle_number=veh_num,
                vehicle_make=d.vehicle_make,
                vehicle_model=d.vehicle_model,
                driver_name=d.full_name or "Driver",
                driver_id=d.app_driver_id,
                driver_phone=d.phone or "",
                daily_rate=float(d.vehicle_daily_rate or 1000.0),
                current_week_os=cw_os,
                status="active" if d.is_active else "idle",
                hisaab_count=len(hisaabs)
            )

            if veh_num not in seen_vehicles:
                seen_vehicles[veh_num] = len(vehicles)
                vehicles.append(veh_obj)
            else:
                idx = seen_vehicles[veh_num]
                existing_v = vehicles[idx]
                if len(hisaabs) > existing_v.hisaab_count:
                    vehicles[idx] = veh_obj
    op_hisaabs = db.query(AppHisaabs).filter(
        AppHisaabs.app_operator_id == op.app_operator_id
    ).order_by(AppHisaabs.week_number.desc()).all()

    latest_week = week_number if week_number is not None else max([h.week_number for h in op_hisaabs], default=40)
    week_hisaabs_by_v = {}
    for h in op_hisaabs:
        if h.week_number == latest_week:
            v_num = None
            parts = h.hisaab_number.split('-') if h.hisaab_number else []
            if len(parts) >= 3 and parts[0] in ('HSB', 'HS'):
                v_num = parts[2].upper()
            elif len(parts) >= 4 and parts[0] == 'HIS':
                v_num = parts[2].upper() if not parts[2].isdigit() and parts[2] != 'OP' else parts[3].upper()
            elif len(parts) >= 2:
                v_num = parts[-1].upper()
            
            if v_num:
                clean_key = v_num.replace(' ', '').replace('-', '').upper()
                week_hisaabs_by_v.setdefault(clean_key, []).append((v_num, h))

    # Re-align current week OS for drivers' assigned vehicles with the latest week hisaab
    matched_keys = set()
    for v in vehicles:
        clean_v = v.vehicle_number.replace(' ', '').replace('-', '').upper()
        matched_key = None
        if clean_v in week_hisaabs_by_v and clean_v not in matched_keys:
            matched_key = clean_v
        else:
            for k, items in week_hisaabs_by_v.items():
                if k in matched_keys:
                    continue
                if clean_v.endswith(k) or k.endswith(clean_v):
                    matched_key = k
                    break

        if matched_key:
            matched_keys.add(matched_key)
            items = week_hisaabs_by_v[matched_key]
            to_pay = 0.0
            to_col = 0.0
            for _, wh in items:
                wh_pay = float(wh.to_pay if getattr(wh, 'to_pay', None) is not None else 0.0)
                wh_col = float(wh.to_collect if getattr(wh, 'to_collect', None) is not None else 0.0)
                if wh_pay == 0.0 and wh_col == 0.0 and getattr(wh, 'current_period_os', None) is not None:
                    cpos = float(wh.current_period_os)
                    if cpos > 0:
                        wh_col = cpos
                    elif cpos < 0:
                        wh_pay = abs(cpos)
                to_pay += wh_pay
                to_col += wh_col
            v.current_week_os = round(to_col - to_pay, 2)
            v.status = "active"
            v.hisaab_count = max(v.hisaab_count, len(items))
        else:
            v.current_week_os = 0.0
            v.status = "idle"

    # Add any remaining vehicles that ran in the current active week
    for clean_key, items in week_hisaabs_by_v.items():
        if clean_key not in matched_keys:
            orig_v_num, wh = items[0]
            drv_name = "Fleet Vehicle"
            drv_phone = ""
            if wh.app_driver_id:
                d_obj = db.query(AppDrivers).filter(AppDrivers.app_driver_id == wh.app_driver_id).first()
                if d_obj:
                    drv_name = d_obj.full_name or "Fleet Driver"
                    drv_phone = d_obj.phone or ""

            to_pay = 0.0
            to_col = 0.0
            for _, w in items:
                w_pay = float(w.to_pay if getattr(w, 'to_pay', None) is not None else 0.0)
                w_col = float(w.to_collect if getattr(w, 'to_collect', None) is not None else 0.0)
                if w_pay == 0.0 and w_col == 0.0 and getattr(w, 'current_period_os', None) is not None:
                    cpos = float(w.current_period_os)
                    if cpos > 0:
                        w_col = cpos
                    elif cpos < 0:
                        w_pay = abs(cpos)
                to_pay += w_pay
                to_col += w_col
            v_cw_os = round(to_col - to_pay, 2)

            seen_vehicles[orig_v_num] = len(vehicles)
            vehicles.append(FleetVehicleResponse(
                vehicle_number=orig_v_num,
                vehicle_make="Maruti",
                vehicle_model=getattr(wh, 'vehicle_model', None) or "WagonR Tour H3 CNG",
                driver_name=drv_name,
                driver_id=wh.app_driver_id or 0,
                driver_phone=drv_phone,
                daily_rate=float(getattr(wh, 'applied_daily_rent', 1000.0) or 1000.0),
                current_week_os=v_cw_os,
                status="active",
                hisaab_count=len(items)
            ))

    latest_week_hisaabs = [h for h in op_hisaabs if h.week_number == latest_week]
    if latest_week_hisaabs:
        cw_to_pay = sum(float(h.to_pay or 0.0) for h in latest_week_hisaabs)
        cw_to_collect = sum(float(h.to_collect or 0.0) for h in latest_week_hisaabs)
        cw_gross = sum(float(h.total_gross_earnings or 0.0) for h in latest_week_hisaabs)
        cw_trips = sum(int(max(h.completed_trips or 0, (h.uber_trips or 0) + (h.ola_trips or 0) + (h.rapido_trips or 0))) for h in latest_week_hisaabs)
    else:
        cw_to_pay = sum(abs(v.current_week_os) for v in vehicles if v.current_week_os < 0)
        cw_to_collect = sum(v.current_week_os for v in vehicles if v.current_week_os > 0)
        cw_gross = sum(float(d.cw_gross_earnings or 0.0) for d in drivers) if drivers else float(op.cw_fleet_gross_earnings or 0.0)
        cw_trips = sum(int(d.cw_trips or 0) for d in drivers) if drivers else int(op.cw_fleet_trips or 0)
    total_veh = len(vehicles) if vehicles else max(len(drivers), (op.total_vehicles or 0))
    active_veh = len([v for v in vehicles if v.status == "active"]) if vehicles else max(len([d for d in drivers if d.is_active]), (op.active_vehicles or 0))
    idle_veh = len([v for v in vehicles if v.status == "idle"]) if vehicles else max(0, total_veh - active_veh)

    # Address resolution: if missing, check if operator exists in app_drivers
    address = op.address
    if not address and db is not None:
        drv_match = db.query(AppDrivers).filter(AppDrivers.phone == op.phone).first()
        if drv_match and drv_match.address:
            address = drv_match.address
    if not address:
        address = "LetzRyd Operations Hub, Bengaluru"

    mgr_name = op.assigned_manager_name or "LetzRyd Fleet Operations"
    mgr_phone = op.assigned_manager_phone or "080-4568-1234"
    company_name = op.company_name or op.contact_person_name or "Fleet Operator"
    contact_person = op.contact_person_name or op.company_name or "Fleet Operator"

    return OperatorFleetResponse(
        app_operator_id=op.app_operator_id,
        operator_code=op.operator_code or f"OPR-{op.app_operator_id}",
        company_name=company_name,
        contact_person_name=contact_person,
        phone=op.phone or "",
        initials=op.initials or (company_name[:2].upper() if company_name else "OP"),
        address=address,
        assigned_manager_name=mgr_name,
        assigned_manager_phone=mgr_phone,
        total_vehicles=total_veh,
        active_vehicles=active_veh,
        idle_vehicles=idle_veh,
        total_drivers=max(len(drivers), (op.total_drivers or 0)),
        deposit_total_req=float(op.deposit_total_req or 0.0),
        deposit_paid=float(op.deposit_paid or 0.0),
        deposit_pending=float(op.deposit_pending or 0.0),
        referral_code=op.referral_code or "",
        referral_reward_amt=float(op.referral_reward_amt or 2000.0),
        upi_id=op.upi_id or "",
        bank_account_last4=op.bank_account_last4 or "",
        cw_fleet_trips=cw_trips,
        cw_fleet_gross_earnings=cw_gross,
        cw_to_collect=cw_to_collect,
        cw_to_pay=cw_to_pay,
        lw_fleet_trips=op.lw_fleet_trips or 0,
        lw_fleet_gross_earnings=float(op.lw_fleet_gross_earnings or 0.0),
        lw_status=op.lw_status or "unpaid",
        vehicles=vehicles,
        drivers=driver_items
    )

@router.get("/{operator_id}/fleet")
def get_operator_fleet(operator_id: Union[int, str], db: Session = Depends(get_db)):
    op = resolve_operator(str(operator_id), db)
    target_op_id = op.app_operator_id if op else (int(operator_id) if str(operator_id).isdigit() else operator_id)
    hisaabs = db.query(AppHisaabs).filter(AppHisaabs.app_operator_id == target_op_id).all()
    mapped = [
        {
            "app_hisaab_id": h.app_hisaab_id,
            "hisaab_number": h.hisaab_number,
            "week_number": h.week_number,
            "period_start": str(h.period_start) if h.period_start else "",
            "period_end": str(h.period_end) if h.period_end else "",
            "total_gross_earnings": float(h.total_gross_earnings or 0.0),
            "weekly_hisaab_due": float(h.weekly_hisaab_due or 0.0),
            "current_period_os": float(h.current_period_os or 0.0),
            "to_collect": float(h.to_collect or 0.0),
            "to_pay": float(h.to_pay or 0.0),
            "paid_amount": float(h.paid_amount or 0.0),
            "payment_status": h.payment_status or "unpaid"
        }
        for h in hisaabs
    ]
    return {"operator_id": target_op_id, "fleet_count": len(mapped), "hisaabs": mapped}

@router.get("/{operator_id}", response_model=OperatorProfileResponse)
def get_operator_by_id(operator_id: Union[int, str], db: Session = Depends(get_db)):
    op = resolve_operator(str(operator_id), db)
    if not op:
        raise HTTPException(status_code=404, detail="Operator not found")
    return _map_operator(op, db)

def _map_operator(op: AppOperators, db: Session = None) -> OperatorProfileResponse:
    cw_to_pay = float(op.cw_to_pay or 0.0)
    cw_to_collect = float(op.cw_to_collect or 0.0)
    total_vehicles = op.total_vehicles or 0
    active_vehicles = op.active_vehicles or 0
    total_drivers = op.total_drivers or 0

    if db is not None:
        drivers = db.query(AppDrivers).filter(
            AppDrivers.operator_id == op.app_operator_id
        ).all()
        
        op_hisaabs = db.query(AppHisaabs).filter(
            AppHisaabs.app_operator_id == op.app_operator_id
        ).order_by(AppHisaabs.week_number.desc()).all()
        
        latest_week = max([h.week_number for h in op_hisaabs], default=40)
        latest_hisaabs = [h for h in op_hisaabs if h.week_number == latest_week]
        
        if latest_hisaabs:
            cw_to_pay = sum(float(h.to_pay or 0.0) for h in latest_hisaabs)
            cw_to_collect = sum(float(h.to_collect or 0.0) for h in latest_hisaabs)
            cw_gross = sum(float(h.total_gross_earnings or 0.0) for h in latest_hisaabs)
            cw_trips = sum(int(h.completed_trips or ((h.uber_trips or 0) + (h.ola_trips or 0) + (h.rapido_trips or 0)) or 0) for h in latest_hisaabs)
        elif drivers:
            cw_to_pay = sum(float(d.cw_to_pay or 0.0) for d in drivers)
            cw_to_collect = sum(float(d.cw_to_collect or 0.0) for d in drivers)
            cw_gross = sum(float(d.cw_gross_earnings or 0.0) for d in drivers)
            cw_trips = sum(int(d.cw_trips or 0) for d in drivers)
        else:
            cw_gross = float(op.cw_fleet_gross_earnings or 0.0)
            cw_trips = int(op.cw_fleet_trips or 0)
            
        if drivers:
            total_vehicles = max(len(drivers), total_vehicles)
            active_vehicles = max(len([d for d in drivers if d.is_active]), active_vehicles)
            total_drivers = max(len(drivers), total_drivers)
    else:
        cw_gross = float(op.cw_fleet_gross_earnings or 0.0)
        cw_trips = int(op.cw_fleet_trips or 0)

    # Address resolution: if missing, check if operator exists in app_drivers
    address = op.address
    if not address and db is not None:
        drv_match = db.query(AppDrivers).filter(AppDrivers.phone == op.phone).first()
        if drv_match and drv_match.address:
            address = drv_match.address
    if not address:
        address = "LetzRyd Operations Hub, Bengaluru"

    # Manager resolution: must not be null
    mgr_name = op.assigned_manager_name or "LetzRyd Fleet Operations"
    mgr_phone = op.assigned_manager_phone or "080-4568-1234"

    # Company name and Contact person must not be null
    company_name = op.company_name or op.contact_person_name or "Fleet Operator"
    contact_person = op.contact_person_name or op.company_name or "Fleet Operator"

    idle_veh = max(0, total_vehicles - active_vehicles) if total_vehicles > active_vehicles else (op.idle_vehicles or 0)

    return OperatorProfileResponse(
        app_operator_id=op.app_operator_id,
        operator_code=op.operator_code or f"OPR-{op.app_operator_id}",
        company_name=company_name,
        contact_person_name=contact_person,
        phone=op.phone or "",
        initials=op.initials or (company_name[:2].upper() if company_name else "OP"),
        address=address,
        assigned_manager_name=mgr_name,
        assigned_manager_phone=mgr_phone,
        total_vehicles=total_vehicles,
        active_vehicles=active_vehicles,
        idle_vehicles=idle_veh,
        total_drivers=total_drivers,
        deposit_total_req=float(op.deposit_total_req or 0.0),
        deposit_paid=float(op.deposit_paid or 0.0),
        deposit_pending=float(op.deposit_pending or 0.0),
        referral_code=op.referral_code or "",
        referral_reward_amt=float(op.referral_reward_amt or 2000.0),
        upi_id=op.upi_id or "",
        bank_account_last4=op.bank_account_last4 or "",
        cw_fleet_trips=cw_trips,
        cw_fleet_gross_earnings=cw_gross,
        cw_to_collect=cw_to_collect,
        cw_to_pay=cw_to_pay,
        lw_fleet_trips=op.lw_fleet_trips or 0,
        lw_fleet_gross_earnings=float(op.lw_fleet_gross_earnings or 0.0),
        lw_status=op.lw_status or "unpaid"
    )
