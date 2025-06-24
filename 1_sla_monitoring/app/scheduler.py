from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from app.db import SessionLocal
from app.models import Ticket, TicketHistory, Alert
from app.config import config
from app.slack import send_alert

scheduler = AsyncIOScheduler()

async def check_sla():
    db = SessionLocal()
    now = datetime.utcnow()
    tickets = db.query(Ticket).filter(Ticket.status=='open').all()
    for ticket in tickets:
        sla_items = config.get(ticket.priority, ticket.customer_tier)
        for sla_name, sla_seconds in sla_items.items():
            deadline = ticket.created_at + timedelta(seconds=sla_seconds)
            remaining = (deadline - now).total_seconds()
            # Breach
            if remaining <= 0 and ticket.status != 'breached':
                # record history
                db.add(TicketHistory(
                    ticket_id=ticket.id,
                    old_status=ticket.status,
                    new_status='breached',
                    changed_at=now
                ))
                # record alert
                db.add(Alert(
                    ticket_id=ticket.id,
                    event='breach',
                    sla=sla_name,
                    remaining=int(remaining),
                    created_at=now
                ))
                ticket.escalation_level += 1
                ticket.status = 'breached'
                await send_alert({"id": ticket.id, "event": "breach", "sla": sla_name})
            # Alert threshold
            elif remaining / sla_seconds <= 0.15:
                # record alert
                db.add(Alert(
                    ticket_id=ticket.id,
                    event='alert',
                    sla=sla_name,
                    remaining=int(remaining),
                    created_at=now
                ))
                await send_alert({"id": ticket.id, "event": "alert", "sla": sla_name, "remaining": remaining})
    db.commit()
    db.close()


def start_scheduler():
    scheduler.add_job(check_sla, 'interval', seconds=60)
    scheduler.start()