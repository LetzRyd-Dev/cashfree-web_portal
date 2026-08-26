"""
helpers.py — Shared normalization, alias resolution, and lookups
"""
import re
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.models.app_models import AppDrivers, AppOperators

DRIVER_PHONE_ALIASES = {
    "9876543210": "9901484683",  # Demo Driver 1 (Vivek)
    "9876543211": "9140631755",  # Demo Driver 2 (Sushant)
    "9876543212": "9930420065",  # Demo Driver 3 (Aayush)
}

OPERATOR_PHONE_ALIASES = {
    "9876543222": "9691938866",  # Demo Operator 1 (Anurag & RK Fleet)
    "9876543223": "9848012345",  # Demo Operator 2 (Saleem Fleet)
}

def clean_phone_number(raw_phone: str) -> str:
    """Strip country codes, spaces, dashes and non-numeric chars."""
    if not raw_phone:
        return ""
    cleaned = re.sub(r"[^\d]", "", str(raw_phone))
    if cleaned.startswith("91") and len(cleaned) == 12:
        cleaned = cleaned[2:]
    elif cleaned.startswith("0") and len(cleaned) == 11:
        cleaned = cleaned[1:]
    return cleaned

def resolve_driver(phone_or_id: str, db: Session) -> Optional[AppDrivers]:
    """Find AppDrivers by clean phone, alias phone, or ID."""
    clean = clean_phone_number(phone_or_id)
    
    # 1. Direct phone match
    if clean:
        driver = db.query(AppDrivers).filter(AppDrivers.phone == clean).first()
        if driver:
            return driver
            
        # 2. Alias phone match
        if clean in DRIVER_PHONE_ALIASES:
            aliased_phone = DRIVER_PHONE_ALIASES[clean]
            driver = db.query(AppDrivers).filter(AppDrivers.phone == aliased_phone).first()
            if driver:
                return driver

    # 3. Numeric ID match (app_driver_id or driver_id)
    if str(phone_or_id).isdigit():
        num_id = int(phone_or_id)
        driver = db.query(AppDrivers).filter(
            (AppDrivers.app_driver_id == num_id) | (AppDrivers.driver_id == num_id)
        ).first()
        if driver:
            return driver

    return None

def resolve_operator(phone_or_id: str, db: Session) -> Optional[AppOperators]:
    """Find AppOperators by clean phone, alias phone, or ID."""
    clean = clean_phone_number(phone_or_id)

    # 1. Direct phone match
    if clean:
        op = db.query(AppOperators).filter(AppOperators.phone == clean).first()
        if op:
            return op

        # 2. Alias phone match
        if clean in OPERATOR_PHONE_ALIASES:
            aliased_phone = OPERATOR_PHONE_ALIASES[clean]
            op = db.query(AppOperators).filter(AppOperators.phone == aliased_phone).first()
            if op:
                return op

    # 3. Numeric ID match (app_operator_id or operator_id)
    if str(phone_or_id).isdigit():
        num_id = int(phone_or_id)
        op = db.query(AppOperators).filter(
            (AppOperators.app_operator_id == num_id) | (AppOperators.operator_id == num_id)
        ).first()
        if op:
            return op

    return None
