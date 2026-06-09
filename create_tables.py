from database import Base, engine
from models import Patient, Observation

Base.metadata.create_all(bind = engine)
