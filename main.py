"""
Handwritten Notes Processing Agents - Main Application
"""

import os
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from models.database import Base, get_db
from api.notes import router as notes_router
from services.ocr_service import OCRService
from services.ai_service import AIService
from services.storage_service import StorageService

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Handwritten Notes Processing Agents",
    description="AI-powered system for processing handwritten notes",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
engine = create_engine(os.getenv("DATABASE_URL", "sqlite:///./notes.db"))
Base.metadata.create_all(bind=engine)

# Initialize services
ocr_service = OCRService()
ai_service = AIService()
storage_service = StorageService()

# Include API routers
app.include_router(notes_router, prefix="/api", tags=["notes"])

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main web interface (original URL)"""
    with open("static/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return Response(
        content=html_content,
        media_type="text/html",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.get("/v2", response_class=HTMLResponse)
async def read_root_v2():
    """
    Serve the web interface on a versioned path.
    This helps bypass any upstream caching on the root URL.
    """
    return FileResponse("static/index.html")

@app.get("/email", response_class=HTMLResponse)
async def read_root_email():
    """
    Serve the web interface with Outlook email feature enabled.
    This is a testing URL for the email functionality.
    """
    with open("static/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return Response(
        content=html_content,
        media_type="text/html",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
            "ETag": str(hash(html_content)),  # Force revalidation
            "Last-Modified": "Thu, 01 Jan 1970 00:00:00 GMT"  # Always considered stale
        }
    )

@app.get("/email-fresh-v3", response_class=HTMLResponse)
async def read_root_email_fresh_v3():
    """FRESH VERSION - No cache, completely new path to bypass all Azure caching"""
    with open("static/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return Response(
        content=html_content,
        media_type="text/html",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Handwritten Notes Processing Agents is running"}

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("🚀 Starting Handwritten Notes Processing Agents...")
    print("📝 OCR Service initialized")
    print("🤖 AI Service initialized")
    print("💾 Storage Service initialized")
    print("🌐 Web interface available at http://localhost:8000")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "True").lower() == "true"
    )


