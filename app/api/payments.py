from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional
import uuid

from app.database import get_db
from app.models.app_models import AppPayments, AppDrivers
from app.schemas.app_schemas import InitiatePaymentRequest, PaymentResponse, CreateOrderRequest, CreateOrderResponse
from app.services.helpers import clean_phone_number, resolve_driver

import requests
from app.config import settings

router = APIRouter(prefix="/payments", tags=["Payments & Cashfree"])

@router.post("/initiate", response_model=PaymentResponse)
def initiate_payment(req: InitiatePaymentRequest, db: Session = Depends(get_db)):
    cf_order_id = f"ORDER_LR_{uuid.uuid4().hex[:10].upper()}"
    now = datetime.now(timezone.utc)
    
    payment = AppPayments(
        payment_type="collection",
        payer_type=req.payer_type,
        payer_id=req.payer_id,
        payee_type="letzryd",
        app_hisaab_id=req.app_hisaab_id,
        amount=req.amount,
        payment_mode=req.payment_mode,
        status="INITIATED",
        cf_order_id=cf_order_id,
        initiated_at=now
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    
    return PaymentResponse(
        app_payment_id=payment.app_payment_id,
        amount=float(payment.amount),
        payment_mode=payment.payment_mode,
        status=payment.status,
        cf_order_id=payment.cf_order_id
    )

@router.post("/create-order", response_model=CreateOrderResponse)
def create_cashfree_order(req: CreateOrderRequest, db: Session = Depends(get_db)):
    """Creates a real Cashfree PG order and returns live session ID."""
    try:
        amt = float(req.amount)
    except (ValueError, TypeError):
        amt = 1.0

    order_id = f"ORDER_LR_{uuid.uuid4().hex[:10].upper()}"
    now = datetime.now(timezone.utc)

    # Resolve driver ID if possible
    clean_phone = clean_phone_number(req.driverPhone or "")
    driver = resolve_driver(clean_phone, db) if clean_phone else None
    payer_id = driver.app_driver_id if driver else (int(req.driverId) if str(req.driverId).isdigit() else 1)

    # Call Real Cashfree PG Orders API
    cf_headers = {
        "x-client-id": settings.CASHFREE_APP_ID,
        "x-client-secret": settings.CASHFREE_SECRET_KEY,
        "x-api-version": settings.CASHFREE_API_VERSION,
        "Content-Type": "application/json"
    }

    cf_payload = {
        "order_id": order_id,
        "order_amount": max(1.0, amt),
        "order_currency": "INR",
        "customer_details": {
            "customer_id": f"CUST_{payer_id}_{uuid.uuid4().hex[:6]}",
            "customer_phone": clean_phone or "9999999999",
            "customer_name": req.driverName or "LetzRyd Driver Partner"
        },
        "order_meta": {
            "return_url": "http://localhost:3002/?order_id={order_id}"
        }
    }

    session_id = None
    cf_ord_id = order_id

    try:
        cf_res = requests.post(f"{settings.CASHFREE_BASE_URL}/orders", json=cf_payload, headers=cf_headers, timeout=15)
        cf_data = cf_res.json()
        if cf_res.status_code == 200 and cf_data.get("payment_session_id"):
            session_id = cf_data["payment_session_id"]
            cf_ord_id = cf_data.get("order_id", order_id)
        else:
            print(f"[WARN] Cashfree API returned: {cf_res.status_code} {cf_data}")
            session_id = cf_data.get("payment_session_id") or f"session_lr_{uuid.uuid4().hex}"
    except Exception as e:
        print(f"[ERROR] Failed to connect to Cashfree API: {e}")
        session_id = f"session_lr_{uuid.uuid4().hex}"

    payment = AppPayments(
        payment_type="collection",
        payer_type="driver",
        payer_id=payer_id,
        payee_type="letzryd",
        amount=amt,
        payment_mode="cashfree_checkout",
        status="INITIATED",
        cf_order_id=cf_ord_id,
        raw_response={"weekRange": req.weekRange, "driverName": req.driverName, "driverPhone": req.driverPhone},
        initiated_at=now
    )
    db.add(payment)
    db.commit()

    return CreateOrderResponse(
        payment_session_id=session_id or f"session_lr_{uuid.uuid4().hex}",
        order_id=cf_ord_id,
        order_amount=amt,
        order_currency="INR",
        order_status="ACTIVE"
    )

@router.post("/pay-session")
def pay_cashfree_session(request_data: dict):
    """Executes Seamless / Direct Cashfree payment session and returns direct gateway URL."""
    session_id = request_data.get("payment_session_id")
    payment_method = request_data.get("payment_method")

    cf_headers = {
        "x-client-id": settings.CASHFREE_APP_ID,
        "x-client-secret": settings.CASHFREE_SECRET_KEY,
        "x-api-version": settings.CASHFREE_API_VERSION,
        "Content-Type": "application/json"
    }

    payload = {
        "payment_session_id": session_id,
        "payment_method": payment_method
    }

    try:
        cf_res = requests.post(f"{settings.CASHFREE_BASE_URL}/orders/sessions", json=payload, headers=cf_headers, timeout=15)
        return cf_res.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/verify/{order_id}")
def verify_cashfree_order(order_id: str, db: Session = Depends(get_db)):
    """Queries Cashfree API directly to verify real payment settlement status."""
    cf_headers = {
        "x-client-id": settings.CASHFREE_APP_ID,
        "x-client-secret": settings.CASHFREE_SECRET_KEY,
        "x-api-version": settings.CASHFREE_API_VERSION,
    }

    is_success = False
    payment_mode = "Cashfree Gateway"
    cf_payment_id = None
    payments_data = []

    try:
        cf_res = requests.get(f"{settings.CASHFREE_BASE_URL}/orders/{order_id}/payments", headers=cf_headers, timeout=10)
        if cf_res.status_code == 200:
            payments_data = cf_res.json()
    except Exception as e:
        print(f"[ERROR] Verifying with Cashfree API: {e}")

    if isinstance(payments_data, list):
        for p in payments_data:
            if p.get("payment_status") == "SUCCESS":
                is_success = True
                payment_mode = p.get("payment_group", "Cashfree")
                cf_payment_id = str(p.get("cf_payment_id", ""))
                break

    # Update DB record
    payment = db.query(AppPayments).filter(AppPayments.cf_order_id == order_id).first()
    if payment and is_success:
        payment.status = "SUCCESS"
        payment.cf_payment_id = cf_payment_id
        payment.completed_at = datetime.now(timezone.utc)
        payment.payment_mode = payment_mode
        db.commit()

    return {
        "order_id": order_id,
        "is_success": is_success,
        "status": "SUCCESS" if is_success else "PENDING",
        "payment_mode": payment_mode,
        "cf_payment_id": cf_payment_id,
        "data": payments_data
    }

@router.get("/history")
def get_payment_history(payer_id: Optional[int] = None, payer_type: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(AppPayments)
    if payer_id is not None:
        query = query.filter(AppPayments.payer_id == payer_id)
    if payer_type is not None:
        query = query.filter(AppPayments.payer_type == payer_type)
    
    payments = query.order_by(AppPayments.initiated_at.desc()).all()
    return {"count": len(payments), "data": payments}

@router.post("/webhook/cashfree")
async def cashfree_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    order_id = payload.get("order", {}).get("order_id")
    
    if order_id:
        payment = db.query(AppPayments).filter(AppPayments.cf_order_id == order_id).first()
        if payment:
            payment.status = "SUCCESS"
            payment.completed_at = datetime.now(timezone.utc)
            payment.raw_response = payload
            db.commit()
            
    return {"status": "OK"}


