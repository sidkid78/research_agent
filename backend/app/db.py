# Database connection, session management, and schema definitions 
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base # Import Base from models.py
import os
import logging

logger = logging.getLogger(__name__)

# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./research_agent.db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    logger.info("Getting database session") # TODO: Remove this
    db = SessionLocal()
    try:
        logger.info("Database session yielded") # TODO: Remove this
        yield db
    finally:
        db.close()
        logger.info("Database session closed") # TODO: Remove this

# Function to create database tables
# In a production app with migrations (Alembic), you might not call this directly from the app.
# Alembic would handle table creation and updates.
def create_db_and_tables():
    logger.info("Creating database tables") # TODO: Remove this
    Base.metadata.create_all(bind=engine) 
    logger.info("Database tables created") # TODO: Remove this