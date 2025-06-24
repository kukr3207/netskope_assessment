from fastapi import FastAPI, Depends
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from typing import List
from pydantic import BaseModel
from datetime import datetime
import time

from app.db import get_db, engine, Base
from app.models import Ticket, TicketHistory
from app.scheduler import start_scheduler

app = FastAPI()

@app.on_event("startup")
def on_startup():
    retries = 10
    while retries > 0:
        try:
            engine.connect()
            break
        except OperationalError:
            retries -= 1
            time.sleep(2)
    Base.metadata.create_all(bind=engine)
    start_scheduler()

class TicketIn(BaseModel):
    id: str
    priority: str
    created_at: datetime
    updated_at: datetime
    status: str
    customer_tier: str

@app.post("/tickets")
async def ingest_tickets(tickets: List[TicketIn], db: Session = Depends(get_db)):
    for t in tickets:
        stmt = insert(Ticket).values(
            id=t.id,
            priority=t.priority,
            created_at=t.created_at,
            updated_at=t.updated_at,
            status=t.status,
            customer_tier=t.customer_tier
        ).on_conflict_do_update(
            index_elements=[Ticket.id],
            set_={
                'priority': t.priority,
                'created_at': t.created_at,
                'updated_at': t.updated_at,
                'status': t.status,
                'customer_tier': t.customer_tier
            }
        )
        existing = db.get(Ticket, t.id)
        if existing and existing.status != t.status:
            db.add(TicketHistory(
                ticket_id=t.id,
                old_status=existing.status,
                new_status=t.status,
                changed_at=datetime.utcnow()
            ))
        db.execute(stmt)
    db.commit()
    return {"ingested": len(tickets)}