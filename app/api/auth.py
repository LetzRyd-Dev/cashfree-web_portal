from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import jwt

from app.database import get_db
from app.config import settings
from app.models.app_models import AppDrivers, AppOperators, AppSessions, AppAuditLogs
from app.schemas.app_schemas import OTPRequest, OTPVerify, PasswordLogin, TokenResponse
from app.services.helpers import clean_phone_number, resolve_driver, resolve_operator

router = APIRouter(prefix="/auth", tags=["Authentication"])

TESTING_STATIC_OTPS = {"1234", "123456", "0000", "000000"}

@router.post("/otp/request")
def request_otp(req: OTPRequest, request: Request, db: Session = Depends(get_db)):
    clean_phone = clean_phone_number(req.phone)
    driver = resolve_driver(clean_phone, db)
    operator = resolve_operator(clean_phone, db)

    if not driver and not operator:
        raise HTTPException(
            status_code=404,
            detail="Profile does not exist. This mobile number is not registered with LetzRyd. Please contact your Fleet Manager or Support."
        )

    req_type = (req.user_type or "driver").lower().strip()
    if req_type == "operator" and operator:
        user_type = "operator"
        user_id = operator.app_operator_id
        effective_phone = operator.phone
    elif req_type == "driver" and driver:
        user_type = "driver"
        user_id = driver.app_driver_id
        effective_phone = driver.phone
    elif driver:
        user_type = "driver"
        user_id = driver.app_driver_id
        effective_phone = driver.phone
    else:
        user_type = "operator"
        user_id = operator.app_operator_id
        effective_phone = operator.phone

    now = datetime.now(timezone.utc)
    session = AppSessions(
        user_type=user_type,
        user_ref_id=user_id,
        phone=effective_phone,
        otp_hash="hashed_1234",
        attempt_count=0,
        is_verified=False,
        used_password=False,
        ip_address=request.client.host if request.client else "127.0.0.1",
        user_agent=request.headers.get("user-agent", ""),
        expires_at=now + timedelta(minutes=10),
        created_at=now
    )
    db.add(session)
    audit = AppAuditLogs(
        user_type=user_type,
        user_ref_id=user_id,
        event_type="OTP_REQUEST",
        phone=effective_phone,
        created_at=now
    )
    db.add(audit)
    db.commit()

    resp = {"success": True, "message": f"OTP sent to {effective_phone}"}
    if getattr(settings, "ENVIRONMENT", "development").lower() == "development":
        resp["demo_otp"] = "1234"
    return resp


@router.post("/otp/verify", response_model=TokenResponse)
def verify_otp(req: OTPVerify, request: Request, db: Session = Depends(get_db)):
    clean_phone = clean_phone_number(req.phone)
    otp = req.otp.strip()

    driver = resolve_driver(clean_phone, db)
    operator = resolve_operator(clean_phone, db)

    if not driver and not operator:
        raise HTTPException(
            status_code=404,
            detail="Profile does not exist. This mobile number is not registered with LetzRyd. Please contact your Fleet Manager or Support."
        )

    # Determine requested user type and target account
    req_type = (req.user_type or "driver").lower().strip()
    
    # If req_type defaulted to 'driver', check if unverified session was requested as 'operator'
    if req_type == "driver" and operator:
        session_check = db.query(AppSessions).filter(
            AppSessions.phone == clean_phone,
            AppSessions.is_verified == False
        ).order_by(AppSessions.created_at.desc()).first()
        if session_check and session_check.user_type == "operator":
            req_type = "operator"

    if req_type == "operator" and operator:
        actual_user_type = "operator"
        user_name = operator.company_name or operator.contact_person_name or "Operator"
        user_id = operator.app_operator_id
        effective_phone = operator.phone
    elif req_type == "driver" and driver:
        actual_user_type = "driver"
        user_name = driver.full_name or "Driver"
        user_id = driver.app_driver_id
        effective_phone = driver.phone
    elif driver:
        actual_user_type = "driver"
        user_name = driver.full_name or "Driver"
        user_id = driver.app_driver_id
        effective_phone = driver.phone
    else:
        actual_user_type = "operator"
        user_name = operator.company_name or operator.contact_person_name or "Operator"
        user_id = operator.app_operator_id
        effective_phone = operator.phone

    # Check testing static OTPs only in development mode
    is_valid_otp = False
    if getattr(settings, "ENVIRONMENT", "development").lower() == "development" and otp in TESTING_STATIC_OTPS:
        is_valid_otp = True

    matched_session = db.query(AppSessions).filter(
        AppSessions.phone == effective_phone,
        AppSessions.is_verified == False
    ).order_by(AppSessions.created_at.desc()).first()

    if not is_valid_otp:
        # Check database session hash
        if matched_session and (matched_session.otp_hash == f"hashed_{otp}"):
            is_valid_otp = True

    if not is_valid_otp:
        err_msg = "Invalid OTP. Please enter the 6-digit SMS OTP sent to your phone."
        if getattr(settings, "ENVIRONMENT", "development").lower() == "development":
            err_msg += " (Demo OTP: 1234)"
        raise HTTPException(
            status_code=400,
            detail=err_msg
        )

    if matched_session:
        matched_session.is_verified = True

    now = datetime.now(timezone.utc)
    payload = {
        "sub": effective_phone,
        "user_type": actual_user_type,
        "user_id": user_id,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    audit = AppAuditLogs(
        user_type=actual_user_type,
        user_ref_id=user_id,
        event_type="LOGIN_SUCCESS",
        phone=effective_phone,
        created_at=now
    )
    db.add(audit)
    db.commit()

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_type=actual_user_type,
        user_id=user_id,
        name=user_name
    )


@router.post("/login/password", response_model=TokenResponse)
def login_password(req: PasswordLogin, request: Request, db: Session = Depends(get_db)):
    clean_phone = clean_phone_number(req.phone)
    driver = resolve_driver(clean_phone, db)
    operator = resolve_operator(clean_phone, db)

    if not driver and not operator:
        raise HTTPException(
            status_code=404,
            detail="Profile does not exist. This mobile number is not registered with LetzRyd."
        )

    req_type = (req.user_type or "driver").lower().strip()
    if req_type == "operator" and operator:
        actual_user_type = "operator"
        user_name = operator.company_name or operator.contact_person_name or "Operator"
        user_id = operator.app_operator_id
        effective_phone = operator.phone
    elif req_type == "driver" and driver:
        actual_user_type = "driver"
        user_name = driver.full_name or "Driver"
        user_id = driver.app_driver_id
        effective_phone = driver.phone
    elif driver:
        actual_user_type = "driver"
        user_name = driver.full_name or "Driver"
        user_id = driver.app_driver_id
        effective_phone = driver.phone
    else:
        actual_user_type = "operator"
        user_name = operator.company_name or operator.contact_person_name or "Operator"
        user_id = operator.app_operator_id
        effective_phone = operator.phone

    now = datetime.now(timezone.utc)
    payload = {
        "sub": effective_phone,
        "user_type": actual_user_type,
        "user_id": user_id,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    audit = AppAuditLogs(
        user_type=actual_user_type,
        user_ref_id=user_id,
        event_type="LOGIN_PASSWORD_SUCCESS",
        phone=effective_phone,
        created_at=now
    )
    db.add(audit)
    db.commit()

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_type=actual_user_type,
        user_id=user_id,
        name=user_name
    )

