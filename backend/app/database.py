from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey, JSON, Float, Boolean, Enum as SAEnum
from sqlalchemy.orm import sessionmaker, DeclarativeBase, relationship, Session
from sqlalchemy.sql import func
from fastapi import Depends
from typing import Generator

from app.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=3600,
)

SessionLocal = sessionmaker(engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
