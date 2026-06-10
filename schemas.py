from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from typing import List

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



class MedicationRequest_Create(BaseModel):
    
    patient_id:str
    medication_name:str
    dosage:str
    frequency:str
    status:str = "active"
    prescribed_date:datetime
    notes:str

class MedicationRequest_Response(BaseModel):
    id:str
    patient_id:str
    medication_name:str
    dosage:str
    frequency:str
    status:str = "active"
    prescribed_date:datetime
    notes:str

    class Config:
        from_attributes = True


class Condition_Create(BaseModel):
    
    patient_id:str
    code:str
    description:str
    clinical_status:str = "active"
    onset_date:datetime
    notes:str

class Condition_Create_Response(BaseModel):
    id:str
    patient_id:str
    code:str
    description:str
    clinical_status:str = "active"
    onset_date:datetime
    notes:str

    class Config:
        from_attributes = True

class PatientEverything(BaseModel):
    resourceType: str = "Bundle"
    type: str = "searchset"
    patient: PatientResponse
    observations: List[ObservationResponse]
    medications: List[MedicationRequest_Response]
    conditions: List[Condition_Create_Response]

class ClinicalNoteInput(BaseModel):
    note: str
    patient_id: str