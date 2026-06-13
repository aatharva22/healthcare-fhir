from fastapi import APIRouter, Depends, HTTPException
from schemas import Condition_Create, Condition_Create_Response
from models import Condition, User
from sqlalchemy.orm import Session
from database import get_db
from typing import List
from auth import get_current_user

router = APIRouter(prefix = "/fhir/Condition", tags = ["Condition"])

@router.post("", response_model = Condition_Create_Response, status_code = 201 )
def create_Condition(condition:Condition_Create, db : Session = Depends(get_db), current_user:User = Depends(get_current_user)):
    new_condition = Condition( ** condition.model_dump())
    db.add(new_condition)
    db.commit()
    db.refresh(new_condition)
    return new_condition

@router.get("/{id}", response_model = Condition_Create_Response, status_code = 200 )
def get_Condition(id:str, db: Session = Depends(get_db), current_user:User = Depends(get_current_user)):
    requested_condition = db.query(Condition).filter(Condition.id == id).first()
    if requested_condition is None:
        raise HTTPException(status_code = 404, detail = f"No condition recorded with given id {id}")
    return requested_condition

@router.get("", response_model = List[Condition_Create_Response], status_code = 200)
def get_all_conditions(patient_id:str | None = None,code:str | None = None, status:str | None = None, skip:int = 0, limit:int = 100, db : Session = Depends(get_db),current_user:User = Depends(get_current_user)):
    query = db.query(Condition)
    if patient_id:
        query = query.filter(Condition.patient_id == patient_id)
    if code:
        query = query.filter(Condition.code == code)
    if status:
        query = query.filter(Condition.status == status)
    return query.order_by(Condition.id).offset(skip).limit(limit).all()

@router.put("/{id}", response_model = Condition_Create_Response, status_code = 200)
def update_Condition(id:str, condition:Condition_Create, db:Session = Depends(get_db),current_user:User = Depends(get_current_user)):
    condition_to_update = db.query(Condition).filter(Condition.id == id).first()
    if condition_to_update is None:
        raise HTTPException(status_code = 404, detail = f"No condition recorded with given id: {id}")
    update_data = condition.model_dump()
    for field, value in update_data.items():
        setattr(condition_to_update, field, value)
    db.commit()
    db.refresh(condition_to_update)
    return condition_to_update

@router.delete("/{id}", status_code = 204)
def delete_Condition(id:str, db:Session = Depends(get_db),current_user:User = Depends(get_current_user)):
    condition_to_delete = db.query(Condition).filter(Condition.id == id).first()
    if condition_to_delete is None:
        raise HTTPException(status_code = 404, detail = f"No condition recorded with given id: {id}")
    db.delete(condition_to_delete)
    db.commit()