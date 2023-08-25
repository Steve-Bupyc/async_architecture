import enum

from sqlalchemy import MetaData, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from src.config import *

engine = create_engine(f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
metadata = MetaData(schema=DB_SCHEMA)
Base = declarative_base(metadata=metadata)
db = SessionLocal()


class Roles(str, enum.Enum):
    admin = "admin"
    manager = "manager"
    worker = "worker"
    accountant = "accountant"
