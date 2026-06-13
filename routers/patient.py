from fastapi import APIRouter, Depends, HTTPException
from schemas import PatientResponse, PatientCreate, PatientEverything
from database import get_db
from sqlalchemy.orm import Session
from typing import List
from models import Patient, MedicationRequest, Condition, Observation, User
from auth import get_current_user

router = APIRouter( prefix = "/fhir/Patient",
                tags = ["Patient"])

@router.post("", response_model = PatientResponse, status_code = 201)
def create_patient(patient: PatientCreate, db: Session = Depends(get_db), current_user:User = Depends(get_current_user)):
    new_patient = Patient( ** patient.model_dump())
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)
    return new_patient

@router.get("", response_model = List[PatientResponse], status_code = 200)
def get_all_patients(skip:int = 0, limit:int = 100,db: Session = Depends(get_db), current_user:User = Depends(get_current_user)):
    
    return db.query(Patient).order_by(Patient.id).offset(skip).limit(limit).all()

@router.get("/{patient_id}", response_model = PatientResponse, status_code = 200)
def get_patient(patient_id : str, db : Session = Depends(get_db)):


    patient_found = db.query(Patient).filter(Patient.id == patient_id).first()
    if patient_found is None:
        raise HTTPException(status_code = 404, detail = f"No patient found with patient id:{patient_id}")
        
    return patient_found
    
@router.put("/{patient_id}", response_model = PatientResponse, status_code = 200)
def update_patient(patient_id : str, patient:PatientCreate, db : Session = Depends(get_db), current_user:User = Depends(get_current_user)):
    patient_to_update = db.query(Patient).filter(patient_id == Patient.id).first()
    if patient_to_update is None:
        raise HTTPException(status_code = 404, detail = f"No patient found with this id, please enter correct patient id")
    update_data = patient.model_dump(exclude_unset = True) # this will only include the fields the user actually sent
 
    for key,value in update_data.items():
        setattr(patient_to_update, key, value)

    db.commit()
    db.refresh(patient_to_update)
    return patient_to_update

@router.delete("/{patient_id}", status_code = 204)
def delete_patient(patient_id : str, db:Session = Depends(get_db), current_user:User = Depends(get_current_user)):
    patient_to_delete = db.query(Patient).filter(Patient.id == patient_id).first()
    if patient_to_delete is None:
        raise HTTPException(status_code = 404, detail = f"No patient found with patient id:  {patient_id}")
    db.delete(patient_to_delete)
    db.commit()

@router.get("/{patient_id}/$everything", response_model = PatientEverything)
def return_Everything(patient_id:str, db:Session = Depends(get_db), current_user:User = Depends(get_current_user)):
    patient = db.query(Patient).filter(patient_id == Patient.id).first()
    if not patient:
        raise HTTPException(status_code = 404, detail = f"No patient found with id:{patient_id}")
    medications = db.query(MedicationRequest).filter(patient_id == MedicationRequest.patient_id).all()
    conditions = db.query(Condition).filter(patient_id == Condition.patient_id).all()
    observations = db.query(Observation).filter(patient_id == Observation.patient_id).all()
    return PatientEverything(patient = patient, medications = medications, observations = observations, conditions = conditions)

    