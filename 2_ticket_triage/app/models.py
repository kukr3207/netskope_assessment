# app/models.py
from sqlalchemy import Column, String, DateTime, Integer, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base

class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(String, primary_key=True, index=True)
    text = Column(String, nullable=False)
    product_area = Column(String)
    urgency = Column(String)
    created_at = Column(DateTime)
    classified_at = Column(DateTime)
    responses = relationship("Response", back_populates="ticket")

class Response(Base):
    __tablename__ = "responses"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ticket_id = Column(String, ForeignKey("tickets.id"), nullable=False)
    answer = Column(String, nullable=False)
    citations = Column(JSON, nullable=False)
    llm_tokens_in = Column(Integer)
    llm_tokens_out = Column(Integer)
    retrieval_latency_ms = Column(Integer)
    created_at = Column(DateTime)
    ticket = relationship("Ticket", back_populates="responses")
