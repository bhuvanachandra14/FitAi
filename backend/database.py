from sqlalchemy import create_engine, Column, Integer, String, LargeBinary, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

import os

# Render provides DATABASE_URL, local uses sqlite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./faces.db")

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # Handle Render's postgres:// schema (SQLAlchemy requires postgresql://)
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Face(Base):
    __tablename__ = "faces"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    age = Column(Integer)
    height = Column(String) # Storing as string to allow units like "180cm" or just number
    weight = Column(String)
    encoding = Column(LargeBinary) # Storing numpy array as bytes

    messages = relationship("Message", back_populates="owner")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    face_id = Column(Integer, ForeignKey("faces.id"))
    role = Column(String) # 'user' or 'ai'
    content = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

    owner = relationship("Face", back_populates="messages")
