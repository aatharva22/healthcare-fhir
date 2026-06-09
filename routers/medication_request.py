from fastapi import APIRouter, Depends, HTTPException
from schemas import MedicationRequest_Create, MedicationRequest_Response
from models import MedicationRequest
from sqlalchemy.orm import Session
from database import get_db
from typing import List

router = APIRouter(prefix = "/fhir/MedicationRequest", tags = ["MedicationRequest"])

@router.post("", response_model = MedicationRequest_Response, status_code = 201 )
def create_medicationRequest(medicationRquest:MedicationRequest_Create, db : Session = Depends(get_db)):
    new_medicationRequest = MedicationRequest( ** medicationRquest.model_dump())
    db.add(new_medicationRequest)
    db.commit()
    db.refresh(new_medicationRequest)
    return new_medicationRequest

@router.get("/{id}", response_model = MedicationRequest_Response, status_code = 200 )
def get_medicationRequest(id:str, db: Session = Depends(get_db)):
    requested_medicationRequest = db.query(MedicationRequest).filter(MedicationRequest.id == id).first()
    if requested_medicationRequest is None:
        raise HTTPException(status_code = 404, detail = f"No medication request recorded with given id {id}")
    return requested_medicationRequest

@router.get("", response_model = List[MedicationRequest_Response], status_code = 200)
def get_all_medicationRequests(patient_id:str | None = None, skip:int = 0, limit:int = 100, db : Session = Depends(get_db)):
    query = db.query(MedicationRequest)
    if patient_id:
        query = query.filter(MedicationRequest.patient_id == patient_id)
    return query.order_by(MedicationRequest.id).offset(skip).limit(limit).all()

@router.put("/{id}", response_model = MedicationRequest_Response, status_code = 200)
def update_medicationRequest(id:str, medicationRequest:MedicationRequest_Create, db:Session = Depends(get_db)):
    medicationRequest_to_update = db.query(MedicationRequest).filter(MedicationRequest.id == id).first()
    if medicationRequest_to_update is None:
        raise HTTPException(status_code = 404, detail = f"No medication request recorded with given id {id}")
    update_data = medicationRequest.model_dump()
    for field, value in update_data.items():
        setattr(medicationRequest_to_update, field, value)
    db.commit()
    db.refresh(medicationRequest_to_update)
    return medicationRequest_to_update

@router.delete("/{id}", status_code = 204)
def delete_medicationRequest(id:str, db:Session = Depends(get_db)):
    medicationRequest_to_delete = db.query(MedicationRequest).filter(MedicationRequest.id == id).first()
    if medicationRequest_to_delete is None:
        raise HTTPException(status_code = 404, detail = f"No medication request recorded with given id: {id}")
    db.delete(medicationRequest_to_delete)
    db.commit()