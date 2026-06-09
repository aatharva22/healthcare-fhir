from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class PatientCreate(BaseModel):
    family_name:str
    given_name:str
    gender:Optional[str] = None
    birth_date:Optional[date] = None
    active:bool = True


class PatientResponse(BaseModel):
    id:str
    family_name:str
    given_name:str
    gender:Optional[str] = None
    birth_date:Optional[date] = None
    active:bool = True



    class Config:
        from_attributes = True

class ObservationCreate(BaseModel):
    patient_id:str 
    code :str
    value :str
    unit :Optional[str] = None
    effective_date:Optional[datetime] = None
    status :str = "final"

class ObservationResponse(BaseModel):
    id :str
    patient_id:str 
    code :str
    value :str
    unit :Optional[str] = None
    effective_date:Optional[datetime] = None
    status :str = "final"

    class Config:
        from_attributes = True