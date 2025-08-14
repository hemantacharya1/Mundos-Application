import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=5,          # Number of connections to keep in the pool
        max_overflow=2,       # Number of connections to allow beyond the pool size
        pool_recycle=300      # Recycle connections after 5 minutes
        )
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency to get a DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()