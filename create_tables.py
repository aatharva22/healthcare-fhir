from database import Base, engine
from models import Patient, Observation, MedicationRequest, Condition

Base.metadata.create_all(bind = engine)
