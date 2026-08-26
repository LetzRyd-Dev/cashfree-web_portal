from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.app_models import AppDrivers
from app.schemas.app_schemas import DriverProfileResponse
from app.services.helpers import clean_phone_number, resolve_driver

router = APIRouter(prefix="/drivers", tags=["Drivers"])

@router.get("/by-phone/{phone}", response_model=DriverProfileResponse)
@router.get("/phone/{phone}", response_model=DriverProfileResponse)
def get_driver_by_phone(phone: str, db: Session = Depends(get_db)):
    clean = clean_phone_number(phone)
    driver = resolve_driver(clean, db)
    if not driver:
        raise HTTPException(status_code=404, detail=f"No driver found with phone {phone}")
    return _map_driver(driver)

@router.get("/me", response_model=DriverProfileResponse)
def get_current_driver(phone: str = "9876543210", db: Session = Depends(get_db)):
    clean = clean_phone_number(phone)
    driver = resolve_driver(clean, db)
    if not driver:
        driver = db.query(AppDrivers).first()
        if not driver:
            raise HTTPException(status_code=404, detail="Driver profile not found")
    return _map_driver(driver)

@router.get("/fleet/{operator_id}")
@router.get("/operator/{operator_id}")
def get_drivers_by_operator(operator_id: int, db: Session = Depends(get_db)):
    drivers = db.query(AppDrivers).filter(AppDrivers.operator_id == operator_id).all()
    return {"operator_id": operator_id, "count": len(drivers), "data": [_map_driver(d) for d in drivers]}

@router.get("/{driver_id}", response_model=DriverProfileResponse)
def get_driver_by_id(driver_id: int, db: Session = Depends(get_db)):
    driver = db.query(AppDrivers).filter(
        (AppDrivers.app_driver_id == driver_id) | (AppDrivers.driver_id == driver_id)
    ).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return _map_driver(driver)

def _map_driver(driver: AppDrivers) -> DriverProfileResponse:
    return DriverProfileResponse(
        app_driver_id=driver.app_driver_id,
        driver_code=driver.driver_code or "",
        phone=driver.phone or "",
        full_name=driver.full_name or "Driver",
        initials=driver.initials or (driver.full_name[:2].upper() if driver.full_name else "D"),
        operator_id=driver.operator_id or 0,
        vehicle_reg_number=driver.vehicle_reg_number,
        vehicle_make=driver.vehicle_make,
        vehicle_model=driver.vehicle_model,
        vehicle_variant=driver.vehicle_variant,
        vehicle_year=driver.vehicle_year,
        vehicle_color=driver.vehicle_color,
        vehicle_fuel_type=driver.vehicle_fuel_type,
        vehicle_daily_rate=float(driver.vehicle_daily_rate or 1000.0),
        vehicle_allocated_from=str(driver.vehicle_allocated_from) if driver.vehicle_allocated_from else None,
        aadhar_number=driver.aadhar_number,
        blood_group=driver.blood_group,
        dob=str(driver.dob) if driver.dob else None,
        address=driver.address,
        joined_date=str(driver.joined_date) if driver.joined_date else None,
        emergency_name=driver.emergency_name,
        emergency_relation=driver.emergency_relation,
        emergency_phone=driver.emergency_phone,
        dl_number=driver.dl_number,
        dl_expiry=str(driver.dl_expiry) if driver.dl_expiry else None,
        rc_number=driver.rc_number,
        rc_expiry=str(driver.rc_expiry) if driver.rc_expiry else None,
        insurance_number=driver.insurance_number,
        insurance_expiry=str(driver.insurance_expiry) if driver.insurance_expiry else None,
        permit_type=driver.permit_type,
        permit_number=driver.permit_number,
        permit_expiry=str(driver.permit_expiry) if driver.permit_expiry else None,
        fitness_number=driver.fitness_number,
        fitness_expiry=str(driver.fitness_expiry) if driver.fitness_expiry else None,
        puc_expiry=str(driver.puc_expiry) if driver.puc_expiry else None,
        assigned_manager_name=driver.assigned_manager_name,
        assigned_manager_phone=driver.assigned_manager_phone,
        deposit_total_req=float(driver.deposit_total_req or 0.0),
        deposit_paid=float(driver.deposit_paid or 0.0),
        deposit_pending=float(driver.deposit_pending or 0.0),
        referral_code=driver.referral_code,
        referral_reward_amt=float(driver.referral_reward_amt or 1000.0),
        incentive_trips_target=driver.incentive_trips_target or 260,
        incentive_reward_amt=float(driver.incentive_reward_amt or 1500.0),
        cw_trips=driver.cw_trips or 0,
        cw_gross_earnings=float(driver.cw_gross_earnings or 0.0),
        cw_total_km=float(driver.cw_total_km or 0.0),
        cw_os=float(driver.cw_os or 0.0),
        cw_to_pay=float(driver.cw_to_pay or 0.0),
        cw_to_collect=float(driver.cw_to_collect or 0.0),
        cw_active_days=driver.cw_active_days or 0,
        cw_incentive_trips_done=driver.cw_incentive_trips_done or 0,
        lw_trips=driver.lw_trips or 0,
        lw_gross_earnings=float(driver.lw_gross_earnings or 0.0),
        lw_os=float(driver.lw_os or 0.0),
        lw_week_number=driver.lw_week_number or 0,
        lw_hisaab_number=driver.lw_hisaab_number or "",
        lw_status=driver.lw_status or "unpaid",
        growth_pct=float(driver.growth_pct or 0.0),
        vehicle_odometer_km=driver.vehicle_odometer_km or 0,
        doc_last_updated=str(driver.doc_last_updated) if driver.doc_last_updated else None,
        deposit_next_due=str(driver.deposit_next_due) if driver.deposit_next_due else None,
        upi_id=driver.upi_id,
        bank_account_last4=driver.bank_account_last4
    )

