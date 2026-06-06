import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Date
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv() #loads the env vaiables, reads them
database_url = os.getenv("DATABASE_URL")

engine = create_engine(database_url)

Base = declarative_base()

session_local = sessionmaker(bind = engine)

