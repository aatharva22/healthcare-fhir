import uuid
from sqlalchemy import Column, String, Boolean, Date, DateTime, ForeignKey
from database import Base

class Patient(Base):
    __tablename__ = "patients"
    id = Column(String, primary_key = True, default = lambda: str(uuid.uuid4()))
    family_name= Column(String, nullable = False)
    given_name = Column(String,nullable = False)
    gender= Column(String)
    birth_date = Column(Date)
    active = Column(Boolean, nullable = False, default = True)

class Observation(Base):
    __tablename__ = "observations"
    id = Column(String, primary_key = True, default = lambda:str(uuid.uuid4()),nullable = False)
    patient_id = Column(String, ForeignKey("patients.id"),nullable = False)   
    code = Column(String, nullable = False )
    value = Column(String, nullable = False )
    unit = Column(String)
    effective_date = Column(DateTime)
    status = Column(String, default = "final", nullable = False)

class MedicationRequest(Base):
    __tablename__ = "medicationrequests"
    id = Column(String, primary_key = True, default = lambda:str(uuid.uuid4()),nullable = False)
    patient_id = Column(String, ForeignKey("patients.id"),nullable = False)
    medication_name = Column(String, nullable = False)
    dosage = Column(String, nullable = False)
    frequency = Column(String, nullable = False)
    status = Column(String, nullable = False, default = "active")
    prescribed_date = Column(DateTime)
    notes = Column(String)

class Condition(Base):
    __tablename__ = "conditions"
    id = Column(String, primary_key = True, default = lambda:str(uuid.uuid4()),nullable = False)
    patient_id = Column(String, ForeignKey("patients.id"),nullable = False)
    code = Column(String, nullable = False)
    description = Column(String, nullable = False)
    clinical_status = Column(String, nullable = False, default = "active")
    onset_date = Column(DateTime)
    notes = Column(String)

from sqlalchemy.sql import func

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="doctor")
    full_name = Column(String)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())