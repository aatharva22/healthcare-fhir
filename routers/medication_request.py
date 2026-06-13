from fastapi import APIRouter, Depends, HTTPException
from schemas import MedicationRequest_Create, MedicationRequest_Response
from models import MedicationRequest, Patient, User
from sqlalchemy.orm import Session
from database import get_db
from typing import List
from auth import get_current_user, require_role

router = APIRouter(prefix="/fhir/MedicationRequest", tags=["MedicationRequest"])


@router.post("", response_model=MedicationRequest_Response, status_code=201)
def create_medicationRequest(
    medicationRquest: MedicationRequest_Create,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["doctor", "admin"]))
):
    new_medicationRequest = MedicationRequest(**medicationRquest.model_dump())
    db.add(new_medicationRequest)
    db.commit()
    db.refresh(new_medicationRequest)
    return new_medicationRequest


@router.get("", response_model=List[MedicationRequest_Response], status_code=200)
def get_all_medicationRequests(
    patient_id: str | None = None,
    status: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(MedicationRequest)
    
    if current_user.role == "patient":
        query = query.join(Patient).filter(Patient.user_id == current_user.id)
    
    if patient_id:
        query = query.filter(MedicationRequest.patient_id == patient_id)
    if status:
        query = query.filter(MedicationRequest.status == status)
    
    return query.order_by(MedicationRequest.id).offset(skip).limit(limit).all()


@router.get("/{id}", response_model=MedicationRequest_Response, status_code=200)
def get_medicationRequest(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    requested_medicationRequest = db.query(MedicationRequest).filter(MedicationRequest.id == id).first()
    if requested_medicationRequest is None:
        raise HTTPException(status_code=404, detail=f"No medication request recorded with given id {id}")
    
    if current_user.role == "patient":
        patient = db.query(Patient).filter(Patient.id == requested_medicationRequest.patient_id).first()
        if patient.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="You can only access your own records")
    
    return requested_medicationRequest


@router.put("/{id}", response_model=MedicationRequest_Response, status_code=200)
def update_medicationRequest(
    id: str,
    medicationRequest: MedicationRequest_Create,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["doctor", "admin"]))
):
    medicationRequest_to_update = db.query(MedicationRequest).filter(MedicationRequest.id == id).first()
    if medicationRequest_to_update is None:
        raise HTTPException(status_code=404, detail=f"No medication request recorded with given id {id}")
    
    update_data = medicationRequest.model_dump()
    for field, value in update_data.items():
        setattr(medicationRequest_to_update, field, value)
    
    db.commit()
    db.refresh(medicationRequest_to_update)
    return medicationRequest_to_update


@router.delete("/{id}", status_code=204)
def delete_medicationRequest(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    medicationRequest_to_delete = db.query(MedicationRequest).filter(MedicationRequest.id == id).first()
    if medicationRequest_to_delete is None:
        raise HTTPException(status_code=404, detail=f"No medication request recorded with given id: {id}")
    db.delete(medicationRequest_to_delete)
    db.commit()