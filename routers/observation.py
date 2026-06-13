from fastapi import APIRouter, Depends, HTTPException
from schemas import ObservationCreate, ObservationResponse
from models import Observation, Patient, User
from database import get_db
from sqlalchemy.orm import Session
from typing import List
from auth import get_current_user, require_role

router = APIRouter(prefix="/fhir/Observation", tags=["Observation"])


@router.post("", response_model=ObservationResponse, status_code=201)
def create_observation(
    observation: ObservationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["doctor", "admin"]))
):
    new_observation = Observation(**observation.model_dump())
    db.add(new_observation)
    db.commit()
    db.refresh(new_observation)
    return new_observation


@router.get("", response_model=List[ObservationResponse], status_code=200)
def get_all_observations(
    patient_id: str | None = None,
    code: str | None = None,
    status: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Observation)
    
    if current_user.role == "patient":
        query = query.join(Patient).filter(Patient.user_id == current_user.id)
    
    if patient_id:
        query = query.filter(Observation.patient_id == patient_id)
    if code:
        query = query.filter(Observation.code == code)
    if status:
        query = query.filter(Observation.status == status)
    
    return query.order_by(Observation.id).offset(skip).limit(limit).all()


@router.get("/{observation_id}", response_model=ObservationResponse, status_code=200)
def get_observation(
    observation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    requested_observation = db.query(Observation).filter(Observation.id == observation_id).first()
    if requested_observation is None:
        raise HTTPException(status_code=404, detail=f"No observation recorded with given id {observation_id}")
    
    if current_user.role == "patient":
        patient = db.query(Patient).filter(Patient.id == requested_observation.patient_id).first()
        if patient.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="You can only access your own records")
    
    return requested_observation


@router.put("/{observation_id}", response_model=ObservationResponse, status_code=200)
def update_observation(
    observation_id: str,
    observation: ObservationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["doctor", "admin"]))
):
    observation_to_update = db.query(Observation).filter(Observation.id == observation_id).first()
    if observation_to_update is None:
        raise HTTPException(status_code=404, detail=f"No observation exists with given id: {observation_id}")
    
    update_data = observation.model_dump()
    for field, value in update_data.items():
        setattr(observation_to_update, field, value)
    
    db.commit()
    db.refresh(observation_to_update)
    return observation_to_update


@router.delete("/{observation_id}", status_code=204)
def delete_observation(
    observation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    observation_to_delete = db.query(Observation).filter(Observation.id == observation_id).first()
    if observation_to_delete is None:
        raise HTTPException(status_code=404, detail=f"No observation exists with given id: {observation_id}")
    db.delete(observation_to_delete)
    db.commit()