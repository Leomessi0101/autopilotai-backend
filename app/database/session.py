from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Use existing DB if env var not set
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///C:/Users/Raidi/autopilotai-backend/autopilotai.db"
)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()
