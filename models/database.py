"""
Database configuration and models
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./notes.db")

# Create engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class
Base = declarative_base()

class Note(Base):
    """Note model for storing processed handwritten notes"""
    __tablename__ = "notes"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    processed_at = Column(DateTime, default=datetime.utcnow)
    
    # OCR results
    confidence_score = Column(Float, default=0.0)
    raw_text = Column(Text)
    
    # AI analysis results
    category = Column(String(100))
    tags = Column(Text)  # JSON string of tags
    summary = Column(Text)
    sentiment = Column(String(50))
    key_points = Column(Text)  # JSON string of key points
    
    # Metadata
    is_processed = Column(Boolean, default=False)
    word_count = Column(Integer, default=0)
    language = Column(String(10), default="en")
    
    # PDF-specific fields
    page_count = Column(Integer, default=1)
    extraction_method = Column(String(50), default="ocr")  # 'direct_pdf' or 'ocr'

class UserAuth(Base):
    """Store OAuth tokens for Microsoft Graph API authentication"""
    __tablename__ = "user_auth"
    
    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String(255), unique=True, nullable=False, index=True)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=False)
    token_expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


