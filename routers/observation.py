from fastapi import APIRouter, Depends, HTTPException
from schemas import ObservationCreate, ObservationResponse
from models import Observation
from database import get_db
from sqlalchemy.orm import Session
from typing import List


router = APIRouter(prefix = "/fhir/Observation", tags = ["Observation"])

@router.post("", response_model = ObservationResponse, status_code = 201 )
def create_observation(observation:ObservationCreate, db : Session = Depends(get_db)):
    new_observation = Observation( ** observation.model_dump())
    db.add(new_observation)
    db.commit()
    db.refresh(new_observation)
    return new_observation

@router.get("/{observation_id}", response_model = ObservationResponse, status_code = 200 )
def get_observation(observation_id:str, db: Session = Depends(get_db)):
    requested_observation = db.query(Observation).filter(Observation.id == observation_id).first()
    if requested_observation is None:
        raise HTTPException(status_code = 404, detail = f"No observation recorder with given observation id {observation_id}")
    return requested_observation

@router.get("", response_model = List[ObservationResponse], status_code = 200)
def get_all_observations(skip:int = 0, limit:int = 100, db : Session = Depends(get_db)):
    return db.query(Observation).order_by(Observation.id).offset(skip).limit(limit).all()

@router.put("/{observation_id}", response_model = ObservationResponse, status_code = 200)
def update_observation(observation_id:str, observation:ObservationCreate, db:Session = Depends(get_db)):
    observation_to_update = db.query(Observation).filter(Observation.id == observation_id).first()
    if observation_to_update is None:
        raise HTTPException(status_code = 404, detail = f"No observation exists with given observation id: {observation_id}")
    update_data = observation.model_dump()
    for field, value in update_data.items():
        setattr(observation_to_update, field, value)
    db.commit()
    db.refresh(observation_to_update)
    return observation_to_update

@router.delete("/{observation_id}", status_code = 204)
def delete_observation(observation_id:str, db:Session = Depends(get_db)):
    observation_to_delete = db.query(Observation).filter(Observation.id == observation_id).first()
    if observation_to_delete is None:
        raise HTTPException(status_code = 404, detail = f"No observation exists with given observation id: {observation_id}")
    db.delete(observation_to_delete)
    db.commit()
