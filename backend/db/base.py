"""Database base and session management for Virasat."""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .models import Base

# Database URL - will be overridden by environment variable
SQLALCHEMY_DATABASE_URL = os.getenv("VIRASAT_DATABASE_URL", "sqlite:///./virasat_demo.db")
if SQLALCHEMY_DATABASE_URL.startswith('postgres://'):
    SQLALCHEMY_DATABASE_URL = 'postgresql+psycopg://' + SQLALCHEMY_DATABASE_URL[len('postgres://'):]
elif SQLALCHEMY_DATABASE_URL.startswith('postgresql://'):
    SQLALCHEMY_DATABASE_URL = 'postgresql+psycopg://' + SQLALCHEMY_DATABASE_URL[len('postgresql://'):]

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Provide a request-scoped database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
