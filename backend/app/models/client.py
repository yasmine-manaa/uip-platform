"""
Client and recurring policy models for managing customer history.
"""

from sqlalchemy import Column, String, DateTime, Float, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Client(Base):
    """Client entity for recurring policies."""
    __tablename__ = "clients"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_reference = Column(String(64), unique=True, index=True)  # CLI-YYYY-NNNN
    full_name = Column(String(128), nullable=False)
    birth_date = Column(DateTime, nullable=True)
    driver_age = Column(Integer, nullable=True)
    licence_number = Column(String(64), nullable=True)
    email = Column(String(128), nullable=True)
    phone = Column(String(32), nullable=True)
    address = Column(Text, nullable=True)
    postal_code = Column(String(10), nullable=True)
    city = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    cases = relationship("Case", back_populates="client", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "client_reference": self.client_reference,
            "full_name": self.full_name,
            "birth_date": self.birth_date.isoformat() if self.birth_date else None,
            "driver_age": self.driver_age,
            "licence_number": self.licence_number,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "postal_code": self.postal_code,
            "city": self.city,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ClientHistory(Base):
    """Client history for tracking changes over time."""
    __tablename__ = "client_history"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String(64), ForeignKey("clients.id"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False)  # POLICY_RENEWAL, CLAIM, CANCELLATION, etc.
    event_date = Column(DateTime, default=datetime.utcnow)
    details = Column(Text, nullable=True)  # JSON details
    previous_bonus_malus = Column(Float, nullable=True)
    new_bonus_malus = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Client", backref="history")

    def to_dict(self):
        return {
            "id": self.id,
            "client_id": self.client_id,
            "event_type": self.event_type,
            "event_date": self.event_date.isoformat() if self.event_date else None,
            "details": self.details,
            "previous_bonus_malus": self.previous_bonus_malus,
            "new_bonus_malus": self.new_bonus_malus,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
