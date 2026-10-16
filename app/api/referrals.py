from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional

from app.database import get_db
from app.models.app_models import AppReferralLeads, AppDrivers, AppOperators
from app.schemas.app_schemas import SubmitReferralRequest, ReferralResponse
from app.services.helpers import resolve_driver, resolve_operator, clean_phone_number

router = APIRouter(prefix="/referrals", tags=["Referrals"])

@router.get("")
def list_referrals(
    driver_id: Optional[int] = None,
    operator_id: Optional[int] = None,
    user_id: Optional[int] = None,
    user_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(AppReferralLeads)

    if driver_id is not None:
        driver = resolve_driver(str(driver_id), db)
        target_id = driver.app_driver_id if driver else driver_id
        query = query.filter(AppReferralLeads.referred_by_driver_id == target_id)
    elif operator_id is not None:
        op = resolve_operator(str(operator_id), db)
        target_id = op.app_operator_id if op else operator_id
        query = query.filter(AppReferralLeads.referred_by_op_id == target_id)
    elif user_id is not None:
        if user_type == "operator":
            op = resolve_operator(str(user_id), db)
            target_id = op.app_operator_id if op else user_id
            query = query.filter(AppReferralLeads.referred_by_op_id == target_id)
        else:
            driver = resolve_driver(str(user_id), db)
            target_id = driver.app_driver_id if driver else user_id
            query = query.filter(AppReferralLeads.referred_by_driver_id == target_id)
    
    referrals = query.order_by(AppReferralLeads.submitted_at.desc()).all()
    mapped = [
        {
            "app_referral_id": r.app_referral_id,
            "referred_by_driver_id": r.referred_by_driver_id,
            "referred_by_op_id": r.referred_by_op_id,
            "referral_code_used": r.referral_code_used,
            "lead_name": r.lead_name,
            "lead_phone": r.lead_phone,
            "lead_city": getattr(r, "lead_city", None),
            "status": r.status or "submitted",
            "reward_amount": float(r.reward_amount or 0.0),
            "reward_credited": r.reward_credited or False,
            "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None
        }
        for r in referrals
    ]
    return {"count": len(mapped), "data": mapped}

@router.post("", response_model=ReferralResponse)
def submit_referral(req: SubmitReferralRequest, db: Session = Depends(get_db)):
    referral_code = req.referral_code_used
    ref_driver_id = None
    ref_op_id = None

    reward_amt = 1000.00
    if req.referred_by_type == 'driver':
        driver = resolve_driver(str(req.referred_by_id), db)
        ref_driver_id = driver.app_driver_id if driver else req.referred_by_id
        if not referral_code and driver:
            referral_code = driver.referral_code
        if driver and driver.referral_reward_amt is not None:
            reward_amt = float(driver.referral_reward_amt)
        else:
            reward_amt = 1000.00
    elif req.referred_by_type == 'operator':
        op = resolve_operator(str(req.referred_by_id), db)
        ref_op_id = op.app_operator_id if op else req.referred_by_id
        if not referral_code and op:
            referral_code = op.referral_code
        if op and op.referral_reward_amt is not None:
            reward_amt = float(op.referral_reward_amt)
        else:
            reward_amt = 2000.00

    clean_lead_name = (req.lead_name or "").strip()
    if not clean_lead_name:
        raise HTTPException(status_code=400, detail="Lead name cannot be empty")
    if len(clean_lead_name) > 150:
        raise HTTPException(status_code=400, detail="Lead name cannot exceed 150 characters")

    clean_lead_phone = clean_phone_number(req.lead_phone)
    if not clean_lead_phone or len(clean_lead_phone) < 10:
        raise HTTPException(status_code=400, detail="A valid 10-digit mobile number is required for referral lead")
    if len(clean_lead_phone) > 15:
        clean_lead_phone = clean_lead_phone[-10:]

    # Idempotency check: if user already referred this phone, return existing record
    if ref_driver_id is not None:
        chk_filter = (AppReferralLeads.referred_by_driver_id == ref_driver_id)
    elif ref_op_id is not None:
        chk_filter = (AppReferralLeads.referred_by_op_id == ref_op_id)
    else:
        raise HTTPException(status_code=400, detail="Invalid referrer: driver or operator not found")

    existing_lead = db.query(AppReferralLeads).filter(
        AppReferralLeads.lead_phone == clean_lead_phone,
        chk_filter
    ).first()
    if existing_lead:
        return ReferralResponse(
            app_referral_id=existing_lead.app_referral_id,
            lead_name=existing_lead.lead_name,
            lead_phone=existing_lead.lead_phone,
            status=existing_lead.status,
            reward_amount=float(existing_lead.reward_amount or 0.0),
            reward_credited=existing_lead.reward_credited or False
        )

    now = datetime.now(timezone.utc)
    lead = AppReferralLeads(
        referred_by_type=req.referred_by_type,
        referred_by_driver_id=ref_driver_id,
        referred_by_op_id=ref_op_id,
        lead_name=clean_lead_name,
        lead_phone=clean_lead_phone,
        referral_code_used=referral_code,
        status="submitted",
        rides_completed=0,
        reward_amount=reward_amt,
        reward_credited=False,
        submitted_at=now,
        created_at=now,
        updated_at=now
    )
    try:
        db.add(lead)
        db.commit()
        db.refresh(lead)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to record referral: {e}")

    return ReferralResponse(
        app_referral_id=lead.app_referral_id,
        lead_name=lead.lead_name,
        lead_phone=lead.lead_phone,
        status=lead.status,
        reward_amount=float(lead.reward_amount or 0.0),
        reward_credited=lead.reward_credited or False
    )

