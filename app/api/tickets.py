from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional, List, Union
import uuid

from app.database import get_db
from app.models.app_models import AppSupportTickets, AppDrivers, AppOperators
from app.schemas.app_schemas import CreateTicketRequest, TicketResponse, UpdateTicketRequest
from app.services.helpers import resolve_driver, resolve_operator

router = APIRouter(prefix="/tickets", tags=["Support Tickets"])

@router.get("")
def list_tickets(
    creator_id: Optional[Union[int, str]] = None,
    creator_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(AppSupportTickets)
    if creator_id is not None:
        c_str = str(creator_id)
        if creator_type == 'operator':
            op = resolve_operator(c_str, db)
            target_id = op.app_operator_id if op else (int(c_str) if c_str.isdigit() else creator_id)
        elif creator_type == 'driver':
            driver = resolve_driver(c_str, db)
            target_id = driver.app_driver_id if driver else (int(c_str) if c_str.isdigit() else creator_id)
        else:
            driver = resolve_driver(c_str, db)
            if driver:
                target_id = driver.app_driver_id
            else:
                op = resolve_operator(c_str, db)
        if not isinstance(target_id, int):
            try:
                target_id = int(target_id)
            except (ValueError, TypeError):
                return {"creator_id": creator_id, "count": 0, "data": []}
        query = query.filter(AppSupportTickets.creator_id == target_id)
    if creator_type is not None:
        query = query.filter(AppSupportTickets.creator_type == creator_type)
    
    tickets = query.order_by(AppSupportTickets.created_at.desc()).all()
    mapped = [_map_ticket(t) for t in tickets]
    return {"creator_id": creator_id, "count": len(mapped), "data": mapped}

@router.post("", response_model=TicketResponse)
def create_ticket(req: CreateTicketRequest, db: Session = Depends(get_db)):
    c_str = str(req.creator_id)
    if req.creator_type == 'operator':
        op = resolve_operator(c_str, db)
        target_id = op.app_operator_id if op else (int(c_str) if c_str.isdigit() else req.creator_id)
    else:
        driver = resolve_driver(c_str, db)
        target_id = driver.app_driver_id if driver else (int(c_str) if c_str.isdigit() else req.creator_id)

    if not isinstance(target_id, int):
        try:
            target_id = int(target_id)
        except (ValueError, TypeError):
            target_id = 0

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

@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(ticket_id: str, db: Session = Depends(get_db)):
    tid_str = str(ticket_id).strip()
    ticket = db.query(AppSupportTickets).filter(
        (AppSupportTickets.ticket_number == tid_str) | 
        (AppSupportTickets.ticket_number == f"TKT-{tid_str}")
    ).first()

    if not ticket and tid_str.isdigit():
        ticket = db.query(AppSupportTickets).filter(
            AppSupportTickets.app_ticket_id == int(tid_str)
        ).first()

    if not ticket and tid_str.upper().startswith("TKT-"):
        suffix = tid_str[4:]
        if suffix.isdigit():
            ticket = db.query(AppSupportTickets).filter(
                AppSupportTickets.app_ticket_id == int(suffix)
            ).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return _map_ticket(ticket)

@router.patch("/{ticket_id}/status", response_model=TicketResponse)
@router.put("/{ticket_id}/status", response_model=TicketResponse)
@router.patch("/{ticket_id}", response_model=TicketResponse)
@router.put("/{ticket_id}", response_model=TicketResponse)
def update_ticket_status(ticket_id: str, req: UpdateTicketRequest, db: Session = Depends(get_db)):
    tid_str = str(ticket_id).strip()
    ticket = db.query(AppSupportTickets).filter(
        (AppSupportTickets.ticket_number == tid_str) | 
        (AppSupportTickets.ticket_number == f"TKT-{tid_str}")
    ).first()

    if not ticket and tid_str.isdigit():
        ticket = db.query(AppSupportTickets).filter(
            AppSupportTickets.app_ticket_id == int(tid_str)
        ).first()

    if not ticket and tid_str.upper().startswith("TKT-"):
        suffix = tid_str[4:]
        if suffix.isdigit():
            ticket = db.query(AppSupportTickets).filter(
                AppSupportTickets.app_ticket_id == int(suffix)
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


