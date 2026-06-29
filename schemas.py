from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from typing import List, Literal

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
    status : Literal["final", "preliminary", "amended"]

class ObservationResponse(BaseModel):
    id :str
    patient_id:str 
    code :str
    value :str
    unit :Optional[str] = None
    effective_date:Optional[datetime] = None
    status :Literal["final", "preliminary", "amended"]

    class Config:
        from_attributes = True



class MedicationRequest_Create(BaseModel):
    
    patient_id:str
    medication_name:str
    dosage:str
    frequency:str
    status:Literal["active", "stopped", "completed"]
    prescribed_date:datetime
    notes:str

class MedicationRequest_Response(BaseModel):
    id:str
    patient_id:str
    medication_name:str
    dosage:str
    frequency:str
    status:Literal["active", "stopped", "completed"]
    prescribed_date:datetime
    notes:Optional[str] = None

    class Config:
        from_attributes = True


class Condition_Create(BaseModel):
    
    patient_id:str
    code:str
    description:str
    clinical_status:Literal["active", "inactive", "resolved"]
    onset_date:datetime
    notes:str

class Condition_Create_Response(BaseModel):
    id:str
    patient_id:str
    code:str
    description:str
    clinical_status:Literal["active", "inactive", "resolved"]
    onset_date:datetime
    notes:Optional[str] = None

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

class SummaryResponse(BaseModel):
    patient_id: str
    patient_name: str
    summary: str

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str | None = None
    role: Literal["admin", "doctor", "patient"] = "doctor"

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str | None = None
    role: str
    is_active: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: str | None = None

class AuditLogResponse(BaseModel):
    id: str
    user_email: str | None = None
    user_role: str | None = None
    action: str
    method: str
    path: str
    status_code: int
    ip_address: str | None = None
    timestamp: datetime

    class Config:
        from_attributes = True
