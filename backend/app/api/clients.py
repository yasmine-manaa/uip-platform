"""
Clients API endpoints for managing recurring customers.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

from app.database import get_db
from app.models.client import Client, ClientHistory
from app.models.case import Case

router = APIRouter(tags=["clients"])


# Pydantic models
class ClientCreate(BaseModel):
    full_name: str
    birth_date: Optional[str] = None
    driver_age: Optional[int] = None
    licence_number: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None


class ClientUpdate(BaseModel):
    full_name: Optional[str] = None
    birth_date: Optional[str] = None
    driver_age: Optional[int] = None
    licence_number: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None


class ClientHistoryCreate(BaseModel):
    event_type: str
    details: Optional[str] = None
    previous_bonus_malus: Optional[float] = None
    new_bonus_malus: Optional[float] = None


# Endpoints
@router.post("/clients", response_model=dict)
def create_client(client_data: ClientCreate, db: Session = Depends(get_db)):
    """Create a new client"""
    # Generate client reference
    year = datetime.utcnow().year
    count = db.query(Client).count() + 1
    client_reference = f"CLI-{year}-{count:04d}"

    client = Client(
        id=str(uuid.uuid4()),
        client_reference=client_reference,
        full_name=client_data.full_name,
        birth_date=datetime.fromisoformat(client_data.birth_date) if client_data.birth_date else None,
        driver_age=client_data.driver_age,
        licence_number=client_data.licence_number,
        email=client_data.email,
        phone=client_data.phone,
        address=client_data.address,
        postal_code=client_data.postal_code,
        city=client_data.city,
    )

    db.add(client)
    db.commit()
    db.refresh(client)

    return client.to_dict()


@router.get("/clients", response_model=List[dict])
def list_clients(db: Session = Depends(get_db)):
    """List all clients"""
    clients = db.query(Client).all()
    return [c.to_dict() for c in clients]


@router.get("/clients/{client_id}", response_model=dict)
def get_client(client_id: str, db: Session = Depends(get_db)):
    """Get a specific client"""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client.to_dict()


@router.put("/clients/{client_id}", response_model=dict)
def update_client(client_id: str, client_data: ClientUpdate, db: Session = Depends(get_db)):
    """Update a client"""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Update fields
    update_data = client_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == 'birth_date' and value:
            setattr(client, field, datetime.fromisoformat(value))
        else:
            setattr(client, field, value)

    client.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(client)

    return client.to_dict()


@router.delete("/clients/{client_id}")
def delete_client(client_id: str, db: Session = Depends(get_db)):
    """Delete a client"""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    db.delete(client)
    db.commit()
    return {"message": "Client deleted successfully"}


@router.get("/clients/{client_id}/cases", response_model=List[dict])
def get_client_cases(client_id: str, db: Session = Depends(get_db)):
    """Get all cases for a client"""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    cases = db.query(Case).filter(Case.client_id == client_id).all()
    return [c.to_dict() for c in cases]


@router.get("/clients/{client_id}/history", response_model=List[dict])
def get_client_history(client_id: str, db: Session = Depends(get_db)):
    """Get client history"""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    history = db.query(ClientHistory).filter(ClientHistory.client_id == client_id).all()
    return [h.to_dict() for h in history]


@router.post("/clients/{client_id}/history", response_model=dict)
def add_client_history(client_id: str, history_data: ClientHistoryCreate, db: Session = Depends(get_db)):
    """Add client history event"""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    history = ClientHistory(
        id=str(uuid.uuid4()),
        client_id=client_id,
        event_type=history_data.event_type,
        details=history_data.details,
        previous_bonus_malus=history_data.previous_bonus_malus,
        new_bonus_malus=history_data.new_bonus_malus,
    )

    db.add(history)
    db.commit()
    db.refresh(history)

    return history.to_dict()


@router.post("/clients/{client_id}/renew", response_model=dict)
def renew_client_policy(client_id: str, db: Session = Depends(get_db)):
    """Create a renewal case for an existing client"""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Get the most recent case for this client
    latest_case = db.query(Case).filter(Case.client_id == client_id).order_by(Case.created_at.desc()).first()
    if not latest_case:
        raise HTTPException(status_code=404, detail="No previous case found for this client")

    # Create a new case based on the latest one
    new_case_id = f"CAS-{datetime.utcnow().year}-{uuid.uuid4().hex[:8].upper()}"
    
    # Copy data from latest case
    import json
    raw_input = json.loads(latest_case.raw_input_json) if latest_case.raw_input_json else {}
    
    # Update some fields for renewal
    raw_input['case_id'] = new_case_id
    raw_input['renewal'] = True
    raw_input['previous_case_id'] = latest_case.id

    new_case = Case(
        id=new_case_id,
        applicant_name=client.full_name,
        status="DRAFT",
        coverage_requested=latest_case.coverage_requested or "Tous Risques",
        raw_input_json=json.dumps(raw_input),
        client_id=client_id,
    )

    db.add(new_case)
    db.commit()
    db.refresh(new_case)

    # Add history event
    history = ClientHistory(
        id=str(uuid.uuid4()),
        client_id=client_id,
        event_type="POLICY_RENEWAL",
        details=f"Renewal from case {latest_case.id}",
    )
    db.add(history)
    db.commit()

    return new_case.to_dict()
