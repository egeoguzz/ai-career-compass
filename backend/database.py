from sqlmodel import create_engine, SQLModel, Session
import logging

from config import settings

# --- Database Configuration ---
DATABASE_URL = settings.DATABASE_URL

# --- Database Engine Creation ---
engine = create_engine(DATABASE_URL, echo=True)

# --- Dependency: Database Session Provider ---
def get_session():
    """
    FastAPI Dependency that provides a database session for each API request.
    """
    with Session(engine) as session:
        yield session

# --- Table Initialization Function ---
def create_db_and_tables():
    """
    Initializes the database by creating all necessary tables.
    """
    try:
        logging.info("Creating database and tables if they don't exist...")
        SQLModel.metadata.create_all(engine)
        logging.info("Database and tables are ready.")
    except Exception as e:
        logging.critical(f"FATAL: Could not create database or tables. Error: {e}")