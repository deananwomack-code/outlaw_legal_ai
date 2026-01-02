# Copilot Instructions for Outlaw Legal AI

## Project Overview

Outlaw Legal AI is a FastAPI-based legal support and analysis engine designed to generate structured legal analyses and branded PDF reports, primarily focused on California and Southern California jurisdictions. The application provides automated legal support by analyzing facts, evidence, and jurisdiction-specific statutes.

## Technology Stack

- **Framework**: FastAPI (0.115.x)
- **Python Version**: 3.12
- **Web Server**: Uvicorn
- **PDF Generation**: ReportLab (4.1.x)
- **HTTP Requests**: requests library
- **Data Validation**: Pydantic 2.6+
- **Testing**: pytest with FastAPI TestClient

## Project Structure

```
/
├── app.py                 # FastAPI entrypoint, API routes and endpoints
├── legal_engine.py        # Core legal analysis logic and data structures
├── pdf_generator.py       # PDF report generation using ReportLab
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container configuration
├── tests/
│   ├── test_app.py       # Integration tests for API endpoints
│   └── test_legal_engine.py  # Unit tests for legal engine
└── assets/               # Static assets (logos, etc.)
```

## Development Setup

### Prerequisites
- Python 3.12+
- pip and venv

### Installation and Running

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Run development server with auto-reload
uvicorn app:app --reload

# Server runs on http://localhost:8000
```

## Build and Test Commands

### Running Tests
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_app.py
pytest tests/test_legal_engine.py
```

### Docker Build
```bash
# Build Docker image
docker build -t outlaw-legal-ai .

# Run container
docker run -p 8000:8000 outlaw-legal-ai
```

## API Endpoints

### System Endpoints
- `GET /` - Welcome message and usage information
- `GET /health` - Health check endpoint

### Legal Analysis Endpoint
- `POST /legal-support` - Generate legal analysis
  - Input: JSON with jurisdiction, county, facts, evidence, requested_output
  - Output: JSON analysis or PDF file

## Code Style and Conventions

### General Guidelines
- Use Python 3.12+ features and type hints
- Follow dataclass patterns for structured data (see `legal_engine.py`)
- Use Pydantic models for request/response validation
- Keep API route handlers in `app.py`, business logic in separate modules
- Use descriptive docstrings with clear section headers (see existing files)

### Documentation Style
- Module-level docstrings use ASCII art separators for sections
- Example:
  ```python
  """
  module_name.py — Brief description
  ----------------------------------
  Longer description here.
  """
  ```
- Section comments use ASCII separators:
  ```python
  # ============================================================
  # SECTION NAME
  # ============================================================
  ```

### Code Organization Patterns
- **Data Classes**: Use `@dataclass` for structured data with `to_dict()` methods
- **Logging**: Configure module-level loggers: `logger = logging.getLogger(__name__)`
- **Error Handling**: Use FastAPI's `HTTPException` with appropriate status codes
- **Type Hints**: Always include type hints for function parameters and returns
- **Constants**: Define configuration constants at module level (see `BRANDING` in `pdf_generator.py`)

### Naming Conventions
- **Variables/Functions**: snake_case (e.g., `build_legal_support`, `api_response`)
- **Classes**: PascalCase (e.g., `LegalSupportRequest`, `WinningFactor`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `API_TIMEOUT_SECONDS`, `BRANDING`)
- **Private Functions**: Prefix with underscore (e.g., `_draw_header`)

## Testing Approach

### Test Structure
- Use `pytest` as the testing framework
- Integration tests in `tests/test_app.py` using FastAPI's `TestClient`
- Unit tests for business logic in `tests/test_legal_engine.py`
- Test functions follow pattern: `test_<functionality>_<scenario>`

### Test Guidelines
- Each test should have a clear docstring describing what it validates
- Use `TestClient` for API endpoint testing
- Validate both status codes and response structure
- Test both success and error scenarios
- Use fixtures and temporary paths where needed (e.g., `tmp_path` for PDF tests)

### Example Test Pattern
```python
def test_endpoint_success_case():
    """Clear description of what this tests."""
    payload = {...}
    res = client.post("/endpoint", json=payload)
    assert res.status_code == 200
    assert "expected_field" in res.json()
```

## Deployment

### Docker Deployment
- Application is containerized using Python 3.12-slim base image
- Exposes port 8000
- Includes ReportLab system dependencies (libfreetype6-dev, libjpeg-dev, libpng-dev)
- Uses Uvicorn as ASGI server

### Environment
- No environment variables currently required
- API calls external govinfo.gov API with 3-second timeout, falls back to local data

## Key Features and Logic

### Legal Analysis Engine (`legal_engine.py`)
- Fetches statutes from public API (govinfo.gov) when available
- Falls back to built-in California/Riverside templates
- Builds structured analysis with:
  - Statutes and legal elements
  - Procedural rules
  - Risk assessment
  - Winning score calculation

### PDF Generation (`pdf_generator.py`)
- Creates branded PDF reports with ReportLab
- Includes header, sections, and formatted content
- Caches logo path at module level for efficiency
- Uses color schemes and branding configuration

### Request Validation
- All API requests validated using Pydantic models
- Required fields enforced (jurisdiction, county, facts)
- Minimum length validation on facts field (20 characters)
- Output format: "json" (default) or "pdf"

## Important Notes

- **API Timeouts**: External API calls have 3-second timeout for fast fallback
- **PDF Cleanup**: Temporary PDF files are cleaned up using background tasks
- **CORS**: API allows all origins (configured for development/testing)
- **Logging**: Uses Python standard logging with INFO level
- **Error Handling**: All exceptions logged and converted to HTTP 500 with detail messages

## Contributing Guidelines

When making changes:
1. Maintain existing code style and documentation patterns
2. Add tests for new functionality
3. Update type hints and docstrings
4. Ensure Docker build succeeds
5. Run tests before committing: `pytest -v`
6. Keep changes minimal and focused
