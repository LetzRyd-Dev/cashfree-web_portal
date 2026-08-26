from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional, List
import uuid

from app.database import get_db
from app.models.app_models import AppSupportTickets, AppDrivers
from app.schemas.app_schemas import CreateTicketRequest, TicketResponse
from app.services.helpers import resolve_driver

router = APIRouter(prefix="/tickets", tags=["Support Tickets"])

@router.get("")
def list_tickets(
    creator_id: Optional[int] = None,
    creator_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(AppSupportTickets)
    if creator_id is not None:
        driver = resolve_driver(str(creator_id), db)
        target_id = driver.app_driver_id if driver else creator_id
        query = query.filter(AppSupportTickets.creator_id == target_id)
    if creator_type is not None:
        query = query.filter(AppSupportTickets.creator_type == creator_type)
    
    tickets = query.order_by(AppSupportTickets.created_at.desc()).all()
    return {"creator_id": creator_id, "count": len(tickets), "data": [_map_ticket(t) for t in tickets]}

@router.post("", response_model=TicketResponse)
def create_ticket(req: CreateTicketRequest, db: Session = Depends(get_db)):
    driver = resolve_driver(str(req.creator_id), db)
    target_id = driver.app_driver_id if (driver and req.creator_type == 'driver') else req.creator_id

    now = datetime.now(timezone.utc)
    ticket_no = f"TKT-2026-{now.strftime('%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
    ticket = AppSupportTickets(
        ticket_number=ticket_no,
        creator_type=req.creator_type,
        creator_id=target_id,
        category=req.category,
        subject=req.subject,
        description=req.description,
        priority=req.priority or "medium",
        status="open",
        created_at=now
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return _map_ticket(ticket)

def _map_ticket(t: AppSupportTickets) -> TicketResponse:
    return TicketResponse(
        app_ticket_id=t.app_ticket_id,
        ticket_number=t.ticket_number or "",
        category=t.category or "",
        subject=t.subject or "",
        description=t.description,
        status=t.status or "open",
        priority=t.priority or "medium",
        created_at=t.created_at,
        resolved_at=t.resolved_at,
        resolution_note=t.resolution_note
    )

