# Handwritten Notes Processing Agents

A comprehensive system for processing handwritten notes using OCR, AI agents, and modern web technologies.

## Features

- **OCR Processing**: Extract text from handwritten PDFs and images using Tesseract with advanced preprocessing
- **AI Agents**: Multiple specialized agents for different tasks:
  - **Text Extraction Agent**: Advanced OCR with confidence scoring and word-level analysis
  - **Content Analysis Agent**: Categorization, sentiment analysis, and key point extraction
  - **Title Generation Agent**: Automatic title creation from note content
  - **Tagging Agent**: Intelligent tag generation for better organization
  - **Summary Agent**: Concise summary generation
- **Web Interface**: Modern, responsive UI for uploading and managing notes
- **Search & Storage**: Full-text search and organized note storage with semantic search capabilities
- **Export Options**: Multiple export formats (TXT, JSON) for processed notes
- **Statistics Dashboard**: Comprehensive analytics and insights

## Quick Start

### Option 1: Automated Setup (Recommended)
```bash
# Run the setup script
python start.py

# Start the application
python main.py
```

### Option 2: Manual Setup

1. Install Tesseract OCR:
```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp env.example .env
# Edit .env with your OpenAI API key (optional but recommended)
```

4. Test the system:
```bash
python test_system.py
```

5. Run the application:
```bash
python main.py
```

6. Open your browser to `http://localhost:8000`

## Project Structure

```
├── main.py                 # FastAPI application entry point
├── models/                 # Database models
├── services/               # Core business logic
│   ├── ocr_service.py     # OCR processing
│   ├── ai_service.py      # AI analysis
│   └── storage_service.py # Note storage
├── api/                   # API endpoints
├── static/                # Web interface files
├── uploads/               # Uploaded images
└── processed/             # Processed notes
```

## API Endpoints

- `POST /upload` - Upload handwritten note PDFs or images
- `GET /notes` - Retrieve all processed notes
- `GET /notes/{id}` - Get specific note details
- `POST /search` - Search through notes
- `GET /export/{id}` - Export note in various formats

## Technologies Used

- **Backend**: FastAPI, SQLAlchemy
- **OCR**: Tesseract, OpenCV
- **AI**: OpenAI GPT, Sentence Transformers
- **Frontend**: HTML5, CSS3, JavaScript
- **Database**: SQLite (easily upgradeable to PostgreSQL)
