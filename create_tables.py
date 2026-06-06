from database import Base, engine
from models import Patient

Base.metadata.create_all(bind = engine)
