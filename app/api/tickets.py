from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional, List
import uuid

from app.database import get_db
from app.models.app_models import AppSupportTickets, AppDrivers, AppOperators
from app.schemas.app_schemas import CreateTicketRequest, TicketResponse, UpdateTicketRequest
from app.services.helpers import resolve_driver, resolve_operator

router = APIRouter(prefix="/tickets", tags=["Support Tickets"])

@router.get("")
def list_tickets(
    creator_id: Optional[int] = None,
    creator_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(AppSupportTickets)
    if creator_id is not None:
        if creator_type == 'operator':
            op = resolve_operator(str(creator_id), db)
            target_id = op.app_operator_id if op else creator_id
        elif creator_type == 'driver':
            driver = resolve_driver(str(creator_id), db)
            target_id = driver.app_driver_id if driver else creator_id
        else:
            driver = resolve_driver(str(creator_id), db)
            if driver:
                target_id = driver.app_driver_id
            else:
                op = resolve_operator(str(creator_id), db)
                target_id = op.app_operator_id if op else creator_id
        query = query.filter(AppSupportTickets.creator_id == target_id)
    if creator_type is not None:
        query = query.filter(AppSupportTickets.creator_type == creator_type)
    
    tickets = query.order_by(AppSupportTickets.created_at.desc()).all()
    mapped = [_map_ticket(t) for t in tickets]
    return {"creator_id": creator_id, "count": len(mapped), "data": mapped}

@router.post("", response_model=TicketResponse)
def create_ticket(req: CreateTicketRequest, db: Session = Depends(get_db)):
    if req.creator_type == 'operator':
        op = resolve_operator(str(req.creator_id), db)
        target_id = op.app_operator_id if op else req.creator_id
    else:
        driver = resolve_driver(str(req.creator_id), db)
        target_id = driver.app_driver_id if driver else req.creator_id

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

@router.patch("/{ticket_id}/status", response_model=TicketResponse)
@router.put("/{ticket_id}/status", response_model=TicketResponse)
@router.patch("/{ticket_id}", response_model=TicketResponse)
@router.put("/{ticket_id}", response_model=TicketResponse)
def update_ticket_status(ticket_id: int, req: UpdateTicketRequest, db: Session = Depends(get_db)):
    ticket = db.query(AppSupportTickets).filter(
        (AppSupportTickets.app_ticket_id == ticket_id)
    ).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if req.status is not None:
        valid_statuses = ["open", "in_progress", "resolved", "closed"]
        normalized_status = req.status.strip().lower()
        if normalized_status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status '{req.status}'. Must be one of {valid_statuses}"
            )
        ticket.status = normalized_status
        if normalized_status in ["resolved", "closed"]:
            ticket.resolved_at = datetime.now(timezone.utc)
        else:
            ticket.resolved_at = None

    if req.resolution_note is not None:
        ticket.resolution_note = req.resolution_note

    if req.priority is not None:
        ticket.priority = req.priority.strip().lower()

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


