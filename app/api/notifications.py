from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.app_models import AppNotifications
from app.schemas.app_schemas import NotificationResponse
from app.services.helpers import resolve_driver, resolve_operator

router = APIRouter(prefix="/notifications", tags=["Push Notifications & Feed"])

@router.get("", response_model=List[NotificationResponse])
def get_notifications(
    target_id: Optional[int] = None,
    target_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(AppNotifications)

    if target_id is not None:
        target_ids = [target_id]
        if target_type == 'operator':
            op = resolve_operator(str(target_id), db)
            if op:
                if op.app_operator_id:
                    target_ids.append(op.app_operator_id)
                if op.operator_id:
                    target_ids.append(op.operator_id)
        elif target_type == 'driver':
            driver = resolve_driver(str(target_id), db)
            if driver:
                if driver.app_driver_id:
                    target_ids.append(driver.app_driver_id)
                if driver.driver_id:
                    target_ids.append(driver.driver_id)
        else:
            driver = resolve_driver(str(target_id), db)
            if driver:
                if driver.app_driver_id:
                    target_ids.append(driver.app_driver_id)
                if driver.driver_id:
                    target_ids.append(driver.driver_id)
            else:
                op = resolve_operator(str(target_id), db)
                if op:
                    if op.app_operator_id:
                        target_ids.append(op.app_operator_id)
                    if op.operator_id:
                        target_ids.append(op.operator_id)

        target_ids = list(set(target_ids))

        if target_type:
            query = query.filter(
                (AppNotifications.target_id.in_(target_ids) & (AppNotifications.target_type == target_type))
                | ((AppNotifications.target_type == target_type) & (AppNotifications.target_id.is_(None)))
                | (AppNotifications.target_type == 'all')
            )
        else:
            query = query.filter(
                AppNotifications.target_id.in_(target_ids)
                | (AppNotifications.target_id.is_(None))
                | (AppNotifications.target_type == 'all')
            )
    elif target_type is not None:
        query = query.filter(
            (AppNotifications.target_type == target_type) | (AppNotifications.target_type == 'all')
        )
    
    notifs = query.order_by(AppNotifications.created_at.desc()).all()
    
    return [
        NotificationResponse(
            app_notif_id=n.app_notif_id,
            title=n.title or "",
            message=n.message or "",
            notif_type=n.notif_type or "hisaab",
            severity=n.severity or "info",
            icon=n.icon,
            is_read=n.is_read or False,
            created_at=n.created_at
        ) for n in notifs
    ]

@router.put("/{notif_id}/read")
@router.patch("/{notif_id}/read")
def mark_read(notif_id: int, db: Session = Depends(get_db)):
    notif = db.query(AppNotifications).filter(AppNotifications.app_notif_id == notif_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    db.commit()
    return {"success": True}


