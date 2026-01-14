# Outlaw Legal AI

## Overview
This is a FastAPI-based legal support and analysis engine. It provides automated legal-support and analysis for mobile/web clients.

## Project Architecture

### Technology Stack
- **Backend**: Python 3.11 with FastAPI
- **PDF Generation**: ReportLab
- **API Framework**: FastAPI with Pydantic for validation
- **Server**: Uvicorn ASGI server

### Directory Structure
- `app.py` - Main FastAPI entrypoint with API routes
- `legal_engine.py` - Core legal analysis logic
- `pdf_generator.py` - PDF report generation
- `tests/` - Test suite (pytest)
- `assets/` - Static assets

### API Endpoints
- `GET /` - Welcome message
- `GET /health` - Health check
- `POST /legal-support` - Generate legal analysis (JSON or PDF output)

## Development
The application runs on port 5000 with uvicorn in development mode:
```bash
uvicorn app:app --host 0.0.0.0 --port 5000 --reload
```

## Dependencies
Core dependencies are defined in `requirements.txt`:
- fastapi
- uvicorn[standard]
- requests
- pydantic
- reportlab
- python-multipart

## Recent Changes
- January 14, 2026: Initial Replit environment setup
