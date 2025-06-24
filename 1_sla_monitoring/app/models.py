from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base

class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(String, primary_key=True, index=True)
    priority = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    status = Column(String, nullable=False)
    customer_tier = Column(String, nullable=False)
    escalation_level = Column(Integer, default=0)
    history = relationship("TicketHistory", back_populates="ticket")
    alerts = relationship("Alert", back_populates="ticket")

class TicketHistory(Base):
    __tablename__ = "ticket_history"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ticket_id = Column(String, ForeignKey('tickets.id'), nullable=False)
    old_status = Column(String, nullable=False)
    new_status = Column(String, nullable=False)
    changed_at = Column(DateTime, nullable=False)
    ticket = relationship("Ticket", back_populates="history")

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ticket_id = Column(String, ForeignKey('tickets.id'), nullable=False)
    event = Column(String, nullable=False)  # 'alert' or 'breach'
    sla = Column(String, nullable=True)
    remaining = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False)
    ticket = relationship("Ticket", back_populates="alerts")