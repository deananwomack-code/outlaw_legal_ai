# GitHub Copilot Instructions for Outlaw Legal AI

## Project Overview

Outlaw Legal AI is a FastAPI-based automated legal support and analysis engine. It provides legal support analysis, risk assessment, and generates PDF reports for legal cases.

## Technology Stack

- **Framework**: FastAPI (Python web framework)
- **Python Version**: Python 3.x
- **Testing**: pytest with FastAPI TestClient
- **PDF Generation**: ReportLab
- **HTTP Client**: requests library
- **Type Validation**: Pydantic v2
- **Server**: uvicorn
- **Logging**: Python logging module

## Repository Structure

```
/
├── app.py               # FastAPI application entrypoint
├── legal_engine.py      # Core legal analysis logic
├── pdf_generator.py     # PDF report generation
├── tests/               # Test suite
│   ├── test_app.py     # API integration tests
│   └── test_legal_engine.py
├── requirements.txt     # Python dependencies
└── Dockerfile          # Container configuration
```

## Coding Standards

### Python Style

- Follow PEP 8 guidelines for Python code
- Use type hints where appropriate (Pydantic models already use Field annotations)
- Use dataclasses for data structures (see `legal_engine.py`)
- Maintain descriptive docstrings at the module and function level
- Use f-strings for string formatting
- Keep functions focused and single-purpose

### Code Organization

- Keep API endpoints in `app.py`
- Core business logic belongs in `legal_engine.py`
- Utility functions for specific tasks in separate modules (e.g., `pdf_generator.py`)
- Use Pydantic models for request/response validation
- Log important events using the configured logger

### Error Handling

- Use FastAPI's `HTTPException` for API errors
- Include appropriate status codes and error messages
- Log errors for debugging purposes
- Handle external API failures gracefully with fallbacks

## Testing

### Test Framework

- Use `pytest` for all tests
- Use FastAPI's `TestClient` for integration tests
- Tests are located in the `tests/` directory

### Running Tests

```bash
# Install dependencies including test requirements
pip install -r requirements.txt

# Run all tests
pytest

# Run specific test file
pytest tests/test_app.py

# Run with verbose output
pytest -v
```

### Test Patterns

- Test files should be prefixed with `test_`
- Use descriptive test function names: `test_<feature>_<scenario>()`
- Include docstrings explaining what each test validates
- Test both success and error cases
- Mock external API calls in unit tests

## Dependencies

### Adding New Dependencies

- Add to `requirements.txt` with version constraints
- Use semantic versioning ranges (e.g., `>=0.115.0,<0.120.0`)
- Group dependencies logically (core vs development/testing)
- Document why the dependency is needed

### Dependency Management

- Core dependencies should have strict version ranges
- Development dependencies are marked as optional
- Test all functionality after adding/updating dependencies

## API Development

### Endpoints

- Use appropriate HTTP methods (GET, POST, etc.)
- Return proper status codes
- Use Pydantic models for request validation
- Include examples in Field definitions
- Document endpoints with clear docstrings

### CORS Configuration

- Currently configured to allow all origins (`["*"]`)
- Modify in `app.py` if stricter CORS policy is needed

### Response Formats

- Support both JSON and PDF responses where applicable
- Use FastAPI's `FileResponse` for file downloads
- Clean up temporary files after sending responses

## Logging

- Use the configured logger instance: `logger = logging.getLogger("outlaw")`
- Log at appropriate levels (INFO, WARNING, ERROR)
- Include contextual information in log messages
- Log API requests and external service calls

## Docker

- Application is containerized using Docker
- Build command: `docker build -t outlaw-legal-ai .`
- Dockerfile is optimized for production deployment
- See `Dockerfile` for configuration details

## Best Practices

### When Making Changes

1. **Understand the Context**: Review related code before making changes
2. **Maintain Consistency**: Follow existing patterns in the codebase
3. **Test Your Changes**: Write tests for new functionality
4. **Document**: Update docstrings and comments as needed
5. **Keep It Simple**: Prefer clear, readable code over clever solutions

### Security Considerations

- Validate all user inputs using Pydantic models
- Sanitize data before including in PDF reports
- Be cautious with external API calls
- Don't expose sensitive information in logs or error messages
- Use environment variables for configuration

### Performance

- Use async/await patterns where appropriate
- Clean up temporary files promptly
- Consider caching for expensive operations
- Log performance-critical sections

## Common Tasks

### Adding a New Endpoint

1. Define Pydantic models for request/response in `app.py`
2. Implement the endpoint handler function
3. Add business logic to `legal_engine.py` if needed
4. Write integration tests in `tests/test_app.py`
5. Update API documentation

### Modifying Legal Analysis Logic

1. Update dataclasses in `legal_engine.py` if needed
2. Modify the `build_legal_support()` function
3. Update related tests in `tests/test_legal_engine.py`
4. Ensure PDF generation handles new fields

### Adding PDF Features

1. Modify `pdf_generator.py`
2. Update the `generate_pdf_report()` function
3. Test PDF generation with sample data
4. Ensure proper cleanup of temporary files

## Deployment

- Application can be deployed using Docker
- See `README_DEPLOY.md` for deployment instructions
- Configuration via `render.yaml` for Render platform
- Ensure all environment variables are properly set

## Support and Resources

- FastAPI Documentation: https://fastapi.tiangolo.com/
- ReportLab Documentation: https://www.reportlab.com/docs/
- Pydantic Documentation: https://docs.pydantic.dev/
