from typing import Union, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.app_models import AppOperators, AppDrivers, AppHisaabs, AppDriverAllocations
from app.schemas.app_schemas import OperatorProfileResponse, OperatorFleetResponse, FleetVehicleResponse
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
def get_operator_fleet_summary(operator_id: Union[int, str], db: Session = Depends(get_db)):
    op = resolve_operator(str(operator_id), db)
    if not op:
        raise HTTPException(status_code=404, detail="Operator not found")
    
    drivers = db.query(AppDrivers).filter(
        AppDrivers.operator_id == op.app_operator_id
    ).order_by(AppDrivers.app_driver_id).all()

    vehicles = []
    seen_vehicles = {}
    for d in drivers:
        driver_ids = [d.app_driver_id]
        if d.driver_id:
            driver_ids.append(d.driver_id)

        hisaabs = db.query(AppHisaabs).filter(
            AppHisaabs.app_driver_id.in_(driver_ids)
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
            to_pay = float(getattr(latest_h, 'to_pay', 0) or 0.0)
            to_col = float(getattr(latest_h, 'to_collect', 0) or getattr(latest_h, 'current_period_os', 0) or 0.0)
            if to_pay > 0:
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
            elif len(hisaabs) == existing_v.hisaab_count:
                if cw_os != 0 and existing_v.current_week_os == 0:
                    vehicles[idx] = veh_obj

    cw_to_pay = sum(float(d.cw_to_pay or 0.0) for d in drivers) if drivers else float(op.cw_to_pay or 0.0)
    cw_to_collect = sum(float(d.cw_to_collect or 0.0) for d in drivers) if drivers else float(op.cw_to_collect or 0.0)
    cw_gross = sum(float(d.cw_gross_earnings or 0.0) for d in drivers) if drivers else float(op.cw_fleet_gross_earnings or 0.0)
    cw_trips = sum(int(d.cw_trips or 0) for d in drivers) if drivers else int(op.cw_fleet_trips or 0)
    total_veh = len(vehicles) if vehicles else max(len(drivers), (op.total_vehicles or 0))
    active_veh = len([v for v in vehicles if v.status == "active"]) if vehicles else max(len([d for d in drivers if d.is_active]), (op.active_vehicles or 0))

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
        idle_vehicles=op.idle_vehicles or 0,
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
        vehicles=vehicles
    )

@router.get("/{operator_id}/fleet")
def get_operator_fleet(operator_id: Union[int, str], db: Session = Depends(get_db)):
    op = resolve_operator(str(operator_id), db)
    target_op_id = op.app_operator_id if op else (int(operator_id) if str(operator_id).isdigit() else operator_id)
    hisaabs = db.query(AppHisaabs).filter(AppHisaabs.app_operator_id == target_op_id).all()
    return {"operator_id": target_op_id, "fleet_count": len(hisaabs), "hisaabs": hisaabs}

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
        
        if drivers:
            cw_to_pay = sum(float(d.cw_to_pay or 0.0) for d in drivers)
            cw_to_collect = sum(float(d.cw_to_collect or 0.0) for d in drivers)
            total_vehicles = max(len(drivers), total_vehicles)
            active_vehicles = max(len([d for d in drivers if d.is_active]), active_vehicles)
            total_drivers = max(len(drivers), total_drivers)

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
        idle_vehicles=op.idle_vehicles or 0,
        total_drivers=total_drivers,
        deposit_total_req=float(op.deposit_total_req or 0.0),
        deposit_paid=float(op.deposit_paid or 0.0),
        deposit_pending=float(op.deposit_pending or 0.0),
        referral_code=op.referral_code or "",
        referral_reward_amt=float(op.referral_reward_amt or 2000.0),
        upi_id=op.upi_id or "",
        bank_account_last4=op.bank_account_last4 or "",
        cw_fleet_trips=op.cw_fleet_trips or 0,
        cw_fleet_gross_earnings=float(op.cw_fleet_gross_earnings or 0.0),
        cw_to_collect=cw_to_collect,
        cw_to_pay=cw_to_pay,
        lw_fleet_trips=op.lw_fleet_trips or 0,
        lw_fleet_gross_earnings=float(op.lw_fleet_gross_earnings or 0.0),
        lw_status=op.lw_status or "unpaid"
    )
