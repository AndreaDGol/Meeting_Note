"""
API endpoints for note management
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Form, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, Response
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import logging

from models.database import get_db, Note
from services.ocr_service import OCRService
from services.ai_service import AIService
from services.storage_service import StorageService
from services.microsoft_auth_service import MicrosoftAuthService
from services.microsoft_graph_service import MicrosoftGraphService

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services (non-auth services)
ocr_service = OCRService()
ai_service = AIService()
storage_service = StorageService()
microsoft_graph_service = MicrosoftGraphService()

# Dependency to get MicrosoftAuthService with DB session
def get_microsoft_auth_service(db: Session = Depends(get_db)) -> MicrosoftAuthService:
    return MicrosoftAuthService(db)

@router.post("/upload")
async def upload_note(
    file: UploadFile = File(...),
    prompt_template: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload and process a handwritten note PDF using GPT-4o Vision
    
    Args:
        file: PDF file to upload
        prompt_template: Optional custom prompt template for GPT-4o Vision extraction.
                         If not provided, uses default template from environment or built-in default.
    """
    try:
        # Validate file type - ONLY PDFs
        if file.content_type != 'application/pdf':
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Save uploaded file (async method ensures file is fully read)
        file_path = await storage_service.save_uploaded_file(file, file.filename)
        
        # Convert PDF to base64 images (one per page)
        base64_images = ocr_service.convert_pdf_to_base64_images(file_path)
        
        if not base64_images:
            raise HTTPException(status_code=400, detail="Could not convert PDF to images")
        
        # Extract text using GPT-4o Vision API with optional custom prompt
        extraction_result = ai_service.extract_text_from_base64_images(
            base64_images,
            prompt_template=prompt_template
        )
        
        if not extraction_result['text'].strip():
            raise HTTPException(status_code=400, detail="No text could be extracted from the PDF")
        
        # Analyze text using AI
        ai_result = ai_service.analyze_text(extraction_result['text'])
        
        # Prepare note data
        note_data = {
            'title': ai_result['title'],
            'content': extraction_result['text'],
            'original_filename': file.filename,
            'file_path': file_path,
            'confidence_score': extraction_result['confidence'],
            'raw_text': extraction_result['text'],
            'category': ai_result['category'],
            'tags': ai_result['tags'],
            'summary': ai_result['summary'],
            'sentiment': ai_result['sentiment'],
            'key_points': ai_result['key_points'],
            'word_count': extraction_result['word_count'],
            'language': extraction_result['language'],
            'page_count': extraction_result['page_count'],
            'extraction_method': extraction_result['extraction_method']
        }
        
        # Save to database
        note = storage_service.save_processed_note(db, note_data)
        
        return {
            "message": "Note processed successfully",
            "note_id": note.id,
            "title": note.title,
            "confidence": extraction_result['confidence'],
            "category": ai_result['category'],
            "file_type": file.content_type,
            "extraction_method": extraction_result['extraction_method'],
            "page_count": extraction_result['page_count']
        }
        
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing note: {str(e)}")

@router.get("/notes")
async def get_notes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = None,
    tag: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all notes with optional filtering"""
    try:
        if category:
            notes = storage_service.get_notes_by_category(db, category)
        elif tag:
            notes = storage_service.get_notes_by_tag(db, tag)
        else:
            notes = storage_service.get_all_notes(db, skip, limit)
        
        # Convert to response format
        result = []
        for note in notes:
            result.append({
                "id": note.id,
                "title": note.title,
                "category": note.category,
                "summary": note.summary,
                "confidence_score": note.confidence_score,
                "processed_at": note.processed_at,
                "word_count": note.word_count,
                "tags": note.tags,
                "sentiment": note.sentiment
            })
        
        return {"notes": result, "total": len(result)}
        
    except Exception as e:
        logger.error(f"Error getting notes: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving notes")

@router.get("/notes/{note_id}")
async def get_note(note_id: int, db: Session = Depends(get_db)):
    """Get a specific note by ID"""
    try:
        note = storage_service.get_note(db, note_id)
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        
        return {
            "id": note.id,
            "title": note.title,
            "content": note.content,
            "category": note.category,
            "tags": note.tags,
            "summary": note.summary,
            "sentiment": note.sentiment,
            "key_points": note.key_points,
            "confidence_score": note.confidence_score,
            "processed_at": note.processed_at,
            "word_count": note.word_count,
            "language": note.language,
            "original_filename": note.original_filename,
            "file_path": note.file_path
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting note {note_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving note")

@router.post("/search")
async def search_notes(
    query: str,
    db: Session = Depends(get_db)
):
    """Search notes by content"""
    try:
        notes = storage_service.search_notes(db, query)
        
        result = []
        for note in notes:
            result.append({
                "id": note.id,
                "title": note.title,
                "category": note.category,
                "summary": note.summary,
                "confidence_score": note.confidence_score,
                "processed_at": note.processed_at,
                "relevance_score": 1.0  # Simple relevance for now
            })
        
        return {"notes": result, "query": query, "total": len(result)}
        
    except Exception as e:
        logger.error(f"Error searching notes: {str(e)}")
        raise HTTPException(status_code=500, detail="Error searching notes")

@router.put("/notes/{note_id}")
async def update_note(
    note_id: int,
    update_data: dict,
    db: Session = Depends(get_db)
):
    """Update a note"""
    try:
        note = storage_service.update_note(db, note_id, update_data)
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        
        return {
            "message": "Note updated successfully", 
            "note_id": note.id,
            "content": note.content
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating note {note_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating note")

@router.delete("/notes/{note_id}")
async def delete_note(note_id: int, db: Session = Depends(get_db)):
    """Delete a note"""
    try:
        success = storage_service.delete_note(db, note_id)
        if not success:
            raise HTTPException(status_code=404, detail="Note not found")
        
        return {"message": "Note deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting note {note_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting note")

@router.get("/export/{note_id}")
async def export_note(
    note_id: int,
    format: str = Query("txt", regex="^(txt|json)$"),
    db: Session = Depends(get_db)
):
    """Export a note in specified format"""
    try:
        note = storage_service.get_note(db, note_id)
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        
        content = storage_service.export_note(note, format)
        
        return {
            "content": content,
            "format": format,
            "filename": f"{note.title.replace(' ', '_')}.{format}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting note {note_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error exporting note")

@router.get("/statistics")
async def get_statistics(db: Session = Depends(get_db)):
    """Get note statistics"""
    try:
        stats = storage_service.get_note_statistics(db)
        return stats
        
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving statistics")

@router.get("/categories")
async def get_categories(db: Session = Depends(get_db)):
    """Get all available categories"""
    try:
        categories = db.query(Note.category).distinct().all()
        return {"categories": [cat[0] for cat in categories if cat[0]]}
        
    except Exception as e:
        logger.error(f"Error getting categories: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving categories")

@router.get("/files/{note_id}")
async def get_pdf_file(note_id: int, db: Session = Depends(get_db)):
    """Serve the PDF file for a note (inline display, not download)"""
    try:
        note = storage_service.get_note(db, note_id)
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        
        if not note.file_path or not os.path.exists(note.file_path):
            raise HTTPException(status_code=404, detail="PDF file not found")
        
        from fastapi.responses import Response
        
        # Read PDF file and return with proper headers for inline display
        with open(note.file_path, 'rb') as f:
            pdf_content = f.read()
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename=\"{note.original_filename}\"",
                "X-Content-Type-Options": "nosniff"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving PDF file for note {note_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error serving PDF file")

# Microsoft Graph API endpoints for Outlook integration

@router.get("/auth/login")
async def microsoft_auth_login(auth_service: MicrosoftAuthService = Depends(get_microsoft_auth_service)):
    """Redirects to Microsoft login for OAuth2 authentication."""
    auth_url = auth_service.get_auth_url()
    return {"auth_url": auth_url}

@router.get("/auth/callback")
async def microsoft_auth_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
    auth_service: MicrosoftAuthService = Depends(get_microsoft_auth_service)
):
    """Handles the callback from Microsoft after user authentication."""
    logger.info("🔵 /api/auth/callback CALLED!")
    logger.info(f"🔵 Query params - code: {code[:20] if code else None}..., error: {error}")
    
    if error:
        logger.error(f"🔴 Microsoft auth error: {error} - {error_description}")
        return JSONResponse(status_code=400, content={"message": f"Authentication failed: {error_description}"})

    if code:
        try:
            logger.info("🔵 Acquiring token by auth code...")
            token_response = auth_service.acquire_token_by_auth_code(code)
            logger.info(f"🔵 Token response has access_token: {'access_token' in token_response}")
            
            if "access_token" in token_response:
                # Get email from ID token claims (no Graph API call needed!)
                user_email = token_response["id_token_claims"].get("preferred_username")
                if not user_email:
                    user_email = token_response["id_token_claims"].get("upn")
                if not user_email:
                    user_email = token_response["id_token_claims"].get("email")
                
                logger.info(f"🔵 Extracted user email: {user_email}")
                
                if user_email:
                    logger.info(f"🔵 Saving tokens to database for {user_email}...")
                    auth_service._save_tokens(user_email, token_response)
                    logger.info(f"✅ Successfully authenticated user: {user_email}")
                    
                    # Redirect back to the app with success flag
                    return RedirectResponse(url="/email?auth=success")
                else:
                    logger.error("🔴 User email not found in token claims.")
                    raise ValueError("User email not found in token claims.")
            else:
                error_msg = token_response.get('error_description', 'Unknown error')
                logger.error(f"🔴 Failed to acquire token: {error_msg}")
                raise ValueError(f"Failed to acquire token: {error_msg}")
        except Exception as e:
            logger.error(f"🔴 Error during token acquisition: {str(e)}")
            return JSONResponse(status_code=500, content={"message": f"Authentication failed: {str(e)}"})
    
    logger.error("🔴 No authorization code received in callback")
    return JSONResponse(status_code=400, content={"message": "No authorization code received."})

@router.get("/auth/status")
async def microsoft_auth_status(
    user_email: str,
    auth_service: MicrosoftAuthService = Depends(get_microsoft_auth_service)
):
    """Checks if a user is authenticated and their token is valid."""
    logger.info(f"🟡 /api/auth/status called for email: {user_email}")
    
    user_auth = auth_service.get_user_auth(user_email)
    logger.info(f"🟡 Database lookup result: {user_auth is not None}")
    
    if user_auth:
        logger.info(f"🟡 Found user_auth, attempting silent token acquisition...")
        token_result = auth_service.acquire_token_silent(user_email)
        logger.info(f"🟡 Token result has access_token: {token_result and 'access_token' in token_result}")
        
        if token_result and "access_token" in token_result:
            logger.info(f"✅ User {user_email} is authenticated")
            return {"authenticated": True, "user_email": user_email}
    
    logger.info(f"🔴 User {user_email} is NOT authenticated")
    return {"authenticated": False, "user_email": user_email}

@router.post("/create-draft")
async def create_outlook_draft_endpoint(
    subject: str = Form(...),
    html_content: str = Form(...),
    user_email: str = Form(...),
    note_id: int = Form(...),
    db: Session = Depends(get_db),
    auth_service: MicrosoftAuthService = Depends(get_microsoft_auth_service)
):
    """Creates an Outlook draft email using Microsoft Graph API with PDF attachment."""
    try:
        token_result = auth_service.acquire_token_silent(user_email)
        if not token_result or "access_token" not in token_result:
            raise HTTPException(status_code=401, detail="User not authenticated or token expired. Please re-authenticate.")

        access_token = token_result["access_token"]
        
        # Create draft via Graph API
        draft_info = microsoft_graph_service.create_draft_email(
            access_token=access_token,
            subject=subject,
            html_body=html_content
        )
        
        draft_id = draft_info["draft_id"]
        
        # Get note from database to retrieve PDF file
        note = storage_service.get_note(db, note_id)
        if note and note.file_path and os.path.exists(note.file_path):
            try:
                # Read PDF file
                with open(note.file_path, 'rb') as f:
                    pdf_content = f.read()
                
                # Add PDF as attachment to the draft
                microsoft_graph_service.add_attachment_to_draft(
                    access_token=access_token,
                    draft_id=draft_id,
                    file_content=pdf_content,
                    filename=note.original_filename
                )
                logger.info(f"Added PDF attachment '{note.original_filename}' to draft {draft_id}")
            except Exception as attach_error:
                logger.error(f"Failed to attach PDF: {str(attach_error)}")
                # Continue even if attachment fails - draft is still created
        
        # Generate Outlook URLs
        # Desktop Outlook deep link
        outlook_desktop_url = f"outlook:message/{draft_id}"
        
        # Web Outlook URL
        outlook_web_url = f"https://outlook.office.com/mail/deeplink/compose/{draft_id}"
        
        logger.info(f"Successfully created draft for user {user_email}: {draft_id}")
        
        return {
            "status": "success",
            "message": "Draft email created successfully",
            "draft_id": draft_id,
            "outlook_desktop_url": outlook_desktop_url,
            "outlook_web_url": outlook_web_url,
            "web_link": draft_info.get("web_link"),
            "subject": draft_info.get("subject")
        }
        
    except Exception as e:
        logger.error(f"Error creating draft: {str(e)}")
        
        # Check if it's an authentication error
        if "not authenticated" in str(e).lower() or "token" in str(e).lower():
            raise HTTPException(
                status_code=401, 
                detail="Authentication required. Please login with Microsoft first."
            )
        
        raise HTTPException(status_code=500, detail=f"Failed to create draft: {str(e)}")

@router.get("/drafts/list")
async def list_user_drafts(
    user_email: str = Query(...),
    top: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List user's draft emails from Outlook
    
    Args:
        user_email: User's email address
        top: Number of drafts to retrieve (1-100)
        
    Returns:
        List of user's draft emails
    """
    try:
        access_token = microsoft_auth_service.get_valid_token(db, user_email)
        drafts = microsoft_graph_service.list_drafts(access_token, top=top)
        
        return {
            "status": "success",
            "count": len(drafts),
            "drafts": drafts
        }
        
    except Exception as e:
        logger.error(f"Error listing drafts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list drafts: {str(e)}")


