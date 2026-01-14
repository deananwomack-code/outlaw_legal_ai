# Outlaw Legal AI

## Overview
Outlaw Legal AI is a FastAPI-based legal support and analysis engine. It provides automated legal analysis for civil cases, focusing on contract disputes, small claims procedures, evidence evaluation, and risk assessment.

## Project Architecture

### Technology Stack
- **Backend**: Python 3.11 with FastAPI
- **PDF Generation**: ReportLab
- **API Framework**: FastAPI with Pydantic for validation
- **Server**: Uvicorn ASGI server
- **Frontend**: Vanilla HTML/CSS/JavaScript (mobile-responsive)

### Directory Structure
```
/
├── app.py              # Main FastAPI entrypoint
├── legal_engine.py     # Core legal analysis logic
├── pdf_generator.py    # PDF report generation
├── templates/          # HTML templates
│   └── index.html      # Web interface
├── static/             # Static assets (CSS, JS)
│   ├── style.css
│   └── app.js
├── assets/             # Brand assets
│   └── outlaw_logo.png
├── tests/              # Test suite (pytest)
└── requirements.txt    # Python dependencies
```

### API Endpoints
- `GET /` - Welcome JSON response with API info
- `GET /ui` - Web interface for testing
- `GET /api` - API information for mobile clients
- `GET /health` - Health check
- `GET /docs` - OpenAPI/Swagger documentation
- `GET /redoc` - ReDoc documentation
- `POST /legal-support` - Generate legal analysis (JSON or PDF)

### For Android/Mobile Integration
The API is designed for easy mobile integration:
1. Use `POST /legal-support` with JSON body
2. Set `Content-Type: application/json` header
3. Response is structured JSON with statutes, procedures, risks, and scores
4. PDF reports can be downloaded by setting `requested_output: "pdf"`

Example request:
```json
{
  "jurisdiction": "California",
  "county": "Riverside",
  "facts": "Description of case facts (min 20 chars)",
  "evidence": [{"label": "Contract", "description": "Signed agreement"}],
  "requested_output": "json"
}
```

## Development
```bash
uvicorn app:app --host 0.0.0.0 --port 5000 --reload
```

## Dependencies
See `requirements.txt`:
- fastapi, uvicorn[standard]
- pydantic, requests
- reportlab, python-multipart
- pytest, httpx, loguru

## Recent Changes
- January 14, 2026: Added web interface with mobile-responsive design
- January 14, 2026: Added OpenAPI documentation at /docs
- January 14, 2026: Optimized API for Android client integration
- January 14, 2026: Initial Replit environment setup
