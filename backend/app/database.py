"""
Database Configuration using SQLAlchemy.
Supports SQLite (file-based, persistent) for effortless zero-config local run,
and PostgreSQL via DATABASE_URL environment variable.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'uip_platform.db'))}"
)

# Connect args needed for SQLite thread concurrency
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI Dependency for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Import all models to ensure tables are created
from app.models.case import Case, Document, AgentRun, HumanReview, AuditEvent
from app.models.client import Client, ClientHistory
