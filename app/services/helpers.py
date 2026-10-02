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

LEGACY_DRIVER_ID_MAP = {
    157: 1,  # Vivek
    202: 2,  # Sushant
    312: 3,  # Aayush
    41: 4,   # Anurag Driver
    418: 5,  # Mohammed Ali
    501: 6,  # Anil Verma
}

def resolve_driver(phone_or_id: str, db: Session) -> Optional[AppDrivers]:
    """Find AppDrivers by clean phone, alias phone, or ID."""
    clean = clean_phone_number(phone_or_id)
    
    if clean:
        # 1. Alias phone match (e.g. 9876543210 -> Vivek 9901484683)
        if clean in DRIVER_PHONE_ALIASES:
            aliased_phone = DRIVER_PHONE_ALIASES[clean]
            driver = db.query(AppDrivers).filter(AppDrivers.phone == aliased_phone).first()
            if driver:
                return driver
                
        # 2. Direct phone match
        driver = db.query(AppDrivers).filter(AppDrivers.phone == clean).first()
        if driver:
            return driver

    # 3. Numeric ID match: Only if input is numeric and NOT a 10-digit phone number
    if str(phone_or_id).isdigit() and len(clean) != 10:
        num_id = int(phone_or_id)
        if num_id in LEGACY_DRIVER_ID_MAP:
            driver = db.query(AppDrivers).filter(AppDrivers.app_driver_id == LEGACY_DRIVER_ID_MAP[num_id]).first()
            if driver:
                return driver
        if num_id > 0:
            driver = db.query(AppDrivers).filter(AppDrivers.app_driver_id == num_id).first()
            if driver:
                return driver
            driver = db.query(AppDrivers).filter(AppDrivers.driver_id == num_id).first()
            if driver:
                return driver

    return None

def resolve_operator(phone_or_id: str, db: Session) -> Optional[AppOperators]:
    """Find AppOperators by clean phone, alias phone, or ID."""
    clean = clean_phone_number(phone_or_id)

    if clean:
        # 1. Alias phone match (e.g. 9876543222 -> Anurag 9691938866)
        if clean in OPERATOR_PHONE_ALIASES:
            aliased_phone = OPERATOR_PHONE_ALIASES[clean]
            op = db.query(AppOperators).filter(AppOperators.phone == aliased_phone).first()
            if op:
                return op

        # 2. Direct phone match
        op = db.query(AppOperators).filter(AppOperators.phone == clean).first()
        if op:
            return op

    # 3. Numeric ID match: Only if input is numeric and NOT a 10-digit phone number
    if str(phone_or_id).isdigit() and len(clean) != 10:
        num_id = int(phone_or_id)
        if num_id > 0:
            op = db.query(AppOperators).filter(AppOperators.app_operator_id == num_id).first()
            if op:
                return op
            op = db.query(AppOperators).filter(AppOperators.operator_id == num_id).first()
            if op:
                return op

    return None
