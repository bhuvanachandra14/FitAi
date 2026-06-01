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
    # Handle Render's postgres:// schema (SQLAlchemy requires postgresql:// or postgresql+psycopg2://)
    import time

    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1).replace("postgresql://", "postgresql+psycopg2://", 1)
    
    print(f"DEBUG: Attempting to connect to DB: {DATABASE_URL.split('@')[-1]}") # Log host only

    MAX_RETRIES = 5
    for attempt in range(MAX_RETRIES):
        try:
            engine = create_engine(DATABASE_URL)
            # Test connection
            with engine.connect() as connection:
                print("DEBUG: Database Connection Successful!")
                break
        except Exception as e:
            print(f"ERROR: Database Connection Failed (Attempt {attempt + 1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(2) # Wait 2 seconds before retrying
            else:
                print("WARNING: All connection attempts failed. Falling back to temporary SQLite database (Data will not persist)")
                DATABASE_URL = "sqlite:///./temp_faces.db"
                engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

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
