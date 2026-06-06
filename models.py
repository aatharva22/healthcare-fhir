import uuid

from sqlalchemy import Column, String, Boolean, Date
from database import Base

class Patient(Base):
    __tablename__ = "patients"
    id = Column(String, primary_key = True, default = lambda: str(uuid.uuid4()))
    family_name= Column(String, nullable = False)
    given_name = Column(String,nullable = False)
    gender= Column(String)
    birth_date = Column(Date)
    active = Column(Boolean, nullable = False, default = True)

