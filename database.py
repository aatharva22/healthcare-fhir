import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv() #loads the env vaiables, reads them
database_url = os.getenv("DATABASE_URL")

engine = create_engine(database_url)

Base = declarative_base()

SessionLocal = sessionmaker(bind = engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

