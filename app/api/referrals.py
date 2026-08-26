from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional

from app.database import get_db
from app.models.app_models import AppReferralLeads, AppDrivers, AppOperators
from app.schemas.app_schemas import SubmitReferralRequest, ReferralResponse
from app.services.helpers import resolve_driver, resolve_operator

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
    return {"count": len(referrals), "data": referrals}

@router.post("", response_model=ReferralResponse)
def submit_referral(req: SubmitReferralRequest, db: Session = Depends(get_db)):
    referral_code = req.referral_code_used
    ref_driver_id = None
    ref_op_id = None

    if req.referred_by_type == 'driver':
        driver = resolve_driver(str(req.referred_by_id), db)
        ref_driver_id = driver.app_driver_id if driver else req.referred_by_id
        if not referral_code and driver:
            referral_code = driver.referral_code
    elif req.referred_by_type == 'operator':
        op = resolve_operator(str(req.referred_by_id), db)
        ref_op_id = op.app_operator_id if op else req.referred_by_id
        if not referral_code and op:
            referral_code = op.referral_code

    now = datetime.now(timezone.utc)
    lead = AppReferralLeads(
        referred_by_type=req.referred_by_type,
        referred_by_driver_id=ref_driver_id,
        referred_by_op_id=ref_op_id,
        lead_name=req.lead_name,
        lead_phone=req.lead_phone,
        referral_code_used=referral_code,
        status="submitted",
        rides_completed=0,
        reward_amount=1000.00,
        reward_credited=False,
        submitted_at=now,
        created_at=now,
        updated_at=now
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return ReferralResponse(
        app_referral_id=lead.app_referral_id,
        lead_name=lead.lead_name,
        lead_phone=lead.lead_phone,
        status=lead.status,
        reward_amount=float(lead.reward_amount),
        reward_credited=lead.reward_credited
    )

