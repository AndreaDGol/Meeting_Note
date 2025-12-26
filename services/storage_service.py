"""
Storage Service for managing note data and files
"""

import os
import shutil
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from models.database import Note
import json
import logging

logger = logging.getLogger(__name__)

class StorageService:
    """Service for managing note storage and retrieval"""
    
    def __init__(self):
        self.uploads_dir = "uploads"
        self.processed_dir = "processed"
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure required directories exist"""
        os.makedirs(self.uploads_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)
    
    async def save_uploaded_file(self, file, filename: str) -> str:
        """
        Save uploaded file to uploads directory
        
        Args:
            file: Uploaded file object (FastAPI UploadFile)
            filename: Original filename
            
        Returns:
            Path to saved file
        """
        try:
            # Generate unique filename
            file_extension = os.path.splitext(filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = os.path.join(self.uploads_dir, unique_filename)
            
            # Read file content using async method (ensures we get all data)
            # This handles cases where the file pointer might not be at the beginning
            # Using read() ensures we get the complete file regardless of current pointer position
            content = await file.read()
            
            # Save file content
            with open(file_path, "wb") as buffer:
                buffer.write(content)
            
            logger.info(f"File saved: {file_path} ({len(content)} bytes)")
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving file {filename}: {str(e)}")
            raise
    
    def save_processed_note(self, db: Session, note_data: Dict[str, Any]) -> Note:
        """
        Save processed note to database
        
        Args:
            db: Database session
            note_data: Dictionary containing note data
            
        Returns:
            Created Note object
        """
        try:
            # Create note object
            note = Note(
                title=note_data.get('title', 'Untitled'),
                content=note_data.get('content', ''),
                original_filename=note_data.get('original_filename', ''),
                file_path=note_data.get('file_path', ''),
                confidence_score=note_data.get('confidence_score', 0.0),
                raw_text=note_data.get('raw_text', ''),
                category=note_data.get('category', 'General'),
                tags=json.dumps(note_data.get('tags', [])),
                summary=note_data.get('summary', ''),
                sentiment=note_data.get('sentiment', 'neutral'),
                key_points=json.dumps(note_data.get('key_points', [])),
                is_processed=True,
                word_count=note_data.get('word_count', 0),
                language=note_data.get('language', 'en'),
                page_count=note_data.get('page_count', 1),
                extraction_method=note_data.get('extraction_method', 'ocr')
            )
            
            # Add to database
            db.add(note)
            db.commit()
            db.refresh(note)
            
            logger.info(f"Note saved to database: {note.id}")
            return note
            
        except Exception as e:
            logger.error(f"Error saving note to database: {str(e)}")
            db.rollback()
            raise
    
    def get_note(self, db: Session, note_id: int) -> Optional[Note]:
        """Get note by ID"""
        try:
            return db.query(Note).filter(Note.id == note_id).first()
        except Exception as e:
            logger.error(f"Error getting note {note_id}: {str(e)}")
            return None
    
    def get_all_notes(self, db: Session, skip: int = 0, limit: int = 100) -> List[Note]:
        """Get all notes with pagination"""
        try:
            return db.query(Note).offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting all notes: {str(e)}")
            return []
    
    def search_notes(self, db: Session, query: str) -> List[Note]:
        """Search notes by content"""
        try:
            return db.query(Note).filter(
                Note.content.contains(query) | 
                Note.title.contains(query) |
                Note.summary.contains(query)
            ).all()
        except Exception as e:
            logger.error(f"Error searching notes: {str(e)}")
            return []
    
    def get_notes_by_category(self, db: Session, category: str) -> List[Note]:
        """Get notes by category"""
        try:
            return db.query(Note).filter(Note.category == category).all()
        except Exception as e:
            logger.error(f"Error getting notes by category {category}: {str(e)}")
            return []
    
    def get_notes_by_tag(self, db: Session, tag: str) -> List[Note]:
        """Get notes by tag"""
        try:
            return db.query(Note).filter(Note.tags.contains(tag)).all()
        except Exception as e:
            logger.error(f"Error getting notes by tag {tag}: {str(e)}")
            return []
    
    def update_note(self, db: Session, note_id: int, update_data: Dict[str, Any]) -> Optional[Note]:
        """Update note data"""
        try:
            note = db.query(Note).filter(Note.id == note_id).first()
            if not note:
                return None
            
            # Update fields
            for key, value in update_data.items():
                if hasattr(note, key):
                    if key in ['tags', 'key_points'] and isinstance(value, list):
                        setattr(note, key, json.dumps(value))
                    else:
                        setattr(note, key, value)
            
            db.commit()
            db.refresh(note)
            return note
            
        except Exception as e:
            logger.error(f"Error updating note {note_id}: {str(e)}")
            db.rollback()
            return None
    
    def delete_note(self, db: Session, note_id: int) -> bool:
        """Delete note and associated files"""
        try:
            note = db.query(Note).filter(Note.id == note_id).first()
            if not note:
                return False
            
            # Delete associated files
            if note.file_path and os.path.exists(note.file_path):
                os.remove(note.file_path)
            
            # Delete from database
            db.delete(note)
            db.commit()
            
            logger.info(f"Note {note_id} deleted")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting note {note_id}: {str(e)}")
            db.rollback()
            return False
    
    def get_note_statistics(self, db: Session) -> Dict[str, Any]:
        """Get statistics about stored notes"""
        try:
            total_notes = db.query(Note).count()
            processed_notes = db.query(Note).filter(Note.is_processed == True).count()
            
            # Category distribution
            categories = db.query(Note.category, db.func.count(Note.id)).group_by(Note.category).all()
            category_dist = {cat: count for cat, count in categories}
            
            # Average confidence score
            avg_confidence = db.query(db.func.avg(Note.confidence_score)).scalar() or 0
            
            # Total words
            total_words = db.query(db.func.sum(Note.word_count)).scalar() or 0
            
            return {
                'total_notes': total_notes,
                'processed_notes': processed_notes,
                'category_distribution': category_dist,
                'average_confidence': round(avg_confidence, 2),
                'total_words': total_words
            }
            
        except Exception as e:
            logger.error(f"Error getting note statistics: {str(e)}")
            return {}
    
    def export_note(self, note: Note, format: str = 'txt') -> str:
        """Export note in specified format"""
        try:
            if format == 'txt':
                content = f"Title: {note.title}\n"
                content += f"Category: {note.category}\n"
                content += f"Date: {note.processed_at}\n"
                content += f"Confidence: {note.confidence_score}%\n\n"
                content += f"Content:\n{note.content}\n\n"
                content += f"Summary:\n{note.summary}\n\n"
                content += f"Key Points:\n"
                key_points = json.loads(note.key_points) if note.key_points else []
                for point in key_points:
                    content += f"- {point}\n"
                
                return content
                
            elif format == 'json':
                return json.dumps({
                    'id': note.id,
                    'title': note.title,
                    'content': note.content,
                    'category': note.category,
                    'tags': json.loads(note.tags) if note.tags else [],
                    'summary': note.summary,
                    'sentiment': note.sentiment,
                    'key_points': json.loads(note.key_points) if note.key_points else [],
                    'confidence_score': note.confidence_score,
                    'processed_at': note.processed_at.isoformat(),
                    'word_count': note.word_count
                }, indent=2)
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Error exporting note {note.id}: {str(e)}")
            raise