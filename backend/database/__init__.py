from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator

from ..config import settings

# Configure connection pooling for production workloads
# pool_size: Number of connections to keep open (default 5)
# max_overflow: Additional connections allowed beyond pool_size (default 10)
# pool_recycle: Recycle connections after this many seconds (prevents stale connections)
# pool_pre_ping: Test connections before using (adds overhead but prevents stale connections)
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,  # Increased from default 5 for 100+ concurrent users
    max_overflow=30,  # Allow 30 extra connections during spikes
    pool_recycle=3600,  # Recycle connections every hour
    pool_pre_ping=True,  # Check connection health before using
    echo=False,  # Set to True for SQL query logging (debug only)
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator:
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
