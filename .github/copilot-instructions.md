# Copilot Instructions for Outlaw Legal AI

## Project Overview

Outlaw Legal AI is a FastAPI-based Python application that provides automated legal-support and analysis. The API generates legal analysis reports in JSON or PDF format based on jurisdiction, county, facts, and evidence provided by the user.

## Repository Structure

- `app.py` - FastAPI entrypoint with API routes (`/`, `/health`, `/legal-support`)
- `legal_engine.py` - Core logic for legal analysis, statute lookup, risk assessment, and scoring
- `pdf_generator.py` - PDF report generation using ReportLab
- `tests/` - Pytest test files using FastAPI TestClient
- `requirements.txt` - Python dependencies
- `assets/` - Static assets including logo for PDF branding
- `Dockerfile` - Container configuration for deployment
- `render.yaml` - Render deployment configuration

## Development Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the development server:
   ```bash
   uvicorn app:app --reload
   ```

## Testing

Run tests with pytest:
```bash
pytest tests/ -v
```

Tests use FastAPI's `TestClient` for API integration testing. When adding new endpoints or modifying existing ones, ensure corresponding tests are added or updated in the `tests/` directory.

## Code Style and Conventions

- Use Python type hints for function parameters and return values
- Follow PEP 8 style guidelines
- Use descriptive docstrings for modules, classes, and functions
- Use `dataclass` for structured data (see `legal_engine.py` for examples)
- Use Pydantic `BaseModel` for API request/response validation
- Prefer logging over print statements (use `logging` module)
- Use meaningful variable names that reflect their purpose

## API Design Guidelines

- All endpoints should have appropriate tags for OpenAPI documentation
- Use Pydantic models for request validation with `Field` for examples and validation
- Return consistent response structures (e.g., `{"status": "success", "data": {...}}`)
- Use appropriate HTTP status codes and `HTTPException` for errors
- Include proper CORS middleware configuration for cross-origin requests

## Key Data Classes

The `legal_engine.py` module defines these core data classes:
- `LegalElement` - Individual legal elements (name, description)
- `Statute` - Legal statute references (citation, title, jurisdiction, summary, elements)
- `ProceduralRule` - Procedural guidelines (name, description)
- `RiskItem` - Risk assessment items (severity, description, mitigation)
- `WinningFactor` - Case strength scoring (element_score, evidence_score, clarity_score, risk_penalty)
- `LegalSupportResponse` - Complete API response structure

## PDF Generation

The `pdf_generator.py` uses ReportLab to create branded PDF reports. When modifying:
- Follow the existing section-based structure
- Use the `BRANDING` configuration for consistent styling
- Handle page breaks appropriately using the `_draw_paragraph` helper
- Test PDF output manually to verify layout

## Dependencies

- FastAPI and Uvicorn for the web framework
- Pydantic for data validation
- ReportLab for PDF generation
- Requests for external API calls
- Pytest and HTTPX for testing

When adding new dependencies:
1. Add them to `requirements.txt` with version constraints
2. Ensure they are compatible with the existing Python version requirements
3. Update the Dockerfile if needed

## Error Handling

- Wrap external API calls in try/except blocks with appropriate fallbacks
- Log errors using the `logging` module before raising exceptions
- Return meaningful error messages in HTTP responses
- Use the `HTTPException` class for API errors with appropriate status codes

## Security Considerations

- Do not commit sensitive data or API keys
- Validate and sanitize all user inputs through Pydantic models
- Be cautious with file operations (use `tempfile` for temporary files)
- Review any changes to CORS settings carefully
