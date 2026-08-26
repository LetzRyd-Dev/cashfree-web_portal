from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.app_models import AppOperators, AppDrivers, AppHisaabs
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
def get_operator_fleet_summary(operator_id: int, db: Session = Depends(get_db)):
    op = resolve_operator(str(operator_id), db)
    if not op:
        raise HTTPException(status_code=404, detail="Operator not found")
    
    drivers = db.query(AppDrivers).filter(AppDrivers.operator_id == op.app_operator_id).order_by(AppDrivers.app_driver_id).all()
    if not drivers:
        drivers = db.query(AppDrivers).filter(AppDrivers.operator_id == op.operator_id).order_by(AppDrivers.app_driver_id).all()

    vehicles = []
    for d in drivers:
        hisaabs = db.query(AppHisaabs).filter(AppHisaabs.app_driver_id == d.app_driver_id).order_by(AppHisaabs.week_number.desc()).all()
        cw_os = float(d.cw_os or 0.0)
        vehicles.append(FleetVehicleResponse(
            vehicle_number=d.vehicle_reg_number or "",
            vehicle_make=d.vehicle_make or "",
            vehicle_model=d.vehicle_model or "",
            driver_name=d.full_name or "",
            driver_id=d.app_driver_id,
            driver_phone=d.phone or "",
            daily_rate=float(d.vehicle_daily_rate or 1000.0),
            current_week_os=cw_os,
            status="active" if d.is_active else "idle",
            hisaab_count=len(hisaabs)
        ))

    cw_to_pay = sum(float(d.cw_to_pay or 0.0) for d in drivers) if drivers else float(op.cw_to_pay or 0.0)
    cw_to_collect = sum(float(d.cw_to_collect or 0.0) for d in drivers) if drivers else float(op.cw_to_collect or 0.0)
    cw_gross = sum(float(d.cw_gross_earnings or 0.0) for d in drivers) if drivers else float(op.cw_fleet_gross_earnings or 0.0)
    cw_trips = sum(int(d.cw_trips or 0) for d in drivers) if drivers else int(op.cw_fleet_trips or 0)
    total_veh = len(drivers) if drivers else (op.total_vehicles or 0)
    active_veh = len([d for d in drivers if d.is_active]) if drivers else (op.active_vehicles or 0)

    return OperatorFleetResponse(
        app_operator_id=op.app_operator_id,
        operator_code=op.operator_code or "",
        company_name=op.company_name or "",
        contact_person_name=op.contact_person_name or "",
        phone=op.phone or "",
        initials=op.initials or "OP",
        address=op.address or "",
        assigned_manager_name=op.assigned_manager_name or "",
        assigned_manager_phone=op.assigned_manager_phone or "",
        total_vehicles=total_veh,
        active_vehicles=active_veh,
        idle_vehicles=op.idle_vehicles or 0,
        total_drivers=len(drivers) if drivers else (op.total_drivers or 0),
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
def get_operator_fleet(operator_id: int, db: Session = Depends(get_db)):
    op = resolve_operator(str(operator_id), db)
    target_op_id = op.app_operator_id if op else operator_id
    hisaabs = db.query(AppHisaabs).filter(AppHisaabs.app_operator_id == target_op_id).all()
    return {"operator_id": target_op_id, "fleet_count": len(hisaabs), "hisaabs": hisaabs}

@router.get("/{operator_id}", response_model=OperatorProfileResponse)
def get_operator_by_id(operator_id: int, db: Session = Depends(get_db)):
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
        drivers = db.query(AppDrivers).filter(AppDrivers.operator_id == op.app_operator_id).all()
        if not drivers:
            drivers = db.query(AppDrivers).filter(AppDrivers.operator_id == op.operator_id).all()
        
        if drivers:
            cw_to_pay = sum(float(d.cw_to_pay or 0.0) for d in drivers)
            cw_to_collect = sum(float(d.cw_to_collect or 0.0) for d in drivers)
            total_vehicles = len(drivers)
            active_vehicles = len([d for d in drivers if d.is_active])
            total_drivers = len(drivers)

    return OperatorProfileResponse(
        app_operator_id=op.app_operator_id,
        operator_code=op.operator_code or "",
        company_name=op.company_name or "",
        contact_person_name=op.contact_person_name or "",
        phone=op.phone or "",
        initials=op.initials or "OP",
        address=op.address or "",
        assigned_manager_name=op.assigned_manager_name or "",
        assigned_manager_phone=op.assigned_manager_phone or "",
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

