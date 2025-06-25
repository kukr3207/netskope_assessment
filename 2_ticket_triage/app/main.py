# app/main.py
import os
import time
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.exc import OperationalError, IntegrityError
from sqlalchemy.orm import Session

from app.config import DATA_DIR
from app.db import engine, Base, get_db
from app.models import Ticket, Response
from app.classifier import classify_ticket
from app.rag import ingest_documents_from_data, generate_response

app = FastAPI()

@app.on_event("startup")
def startup():
    # 1) wait for Postgres
    retries = 5
    while retries:
        try:
            engine.connect()
            break
        except OperationalError:
            retries -= 1
            time.sleep(2)
    # 2) create tables
    Base.metadata.create_all(bind=engine)
    # 3) build FAISS index
    ingest_documents_from_data(DATA_DIR)

@app.post("/classify")
def classify(ticket: dict, db: Session = Depends(get_db)):
    try:
        area, urgency = classify_ticket(ticket["text"])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    now = datetime.utcnow()
    db_ticket = Ticket(
        id=ticket["id"],
        text=ticket["text"],
        product_area=area,
        urgency=urgency,
        created_at=now,
        classified_at=now
    )
    db.add(db_ticket)
    db.commit()
    return {"id": ticket["id"], "product_area": area, "urgency": urgency}

@app.post("/respond")
def respond(req: dict, db: Session = Depends(get_db)):
    ticket_id = req.get("ticket_id")
    if not ticket_id:
        raise HTTPException(status_code=400, detail="`ticket_id` is required")
    # 1) Ensure the ticket was already classified & persisted
    existing = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail=f"Ticket '{ticket_id}' not found")

    # 2) Generate the answer
    answer, citations, stats = generate_response(req["query"])
    now = datetime.utcnow()
    resp = Response(
        ticket_id=ticket_id,
        answer=answer,
        citations=citations,
        llm_tokens_in=stats["tokens_in"],
        llm_tokens_out=stats["tokens_out"],
        retrieval_latency_ms=stats["retrieval_ms"],
        created_at=now
    )
    db.add(resp)

    # 3) Commit with IntegrityError handling
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save response: " + str(e))

    return {"answer": answer, "citations": citations}
