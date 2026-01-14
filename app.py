"""
app.py — FastAPI entrypoint for Outlaw Legal AI
-----------------------------------------------
Starts the API service that mobile/web clients will call.

Endpoints:
  POST /legal-support   →  JSON or PDF report
  GET  /                →  Web interface
  GET  /api             →  API info (for mobile clients)
  GET  /health          →  Health check
  GET  /docs            →  OpenAPI documentation
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Optional
import tempfile
import os
import logging
from pathlib import Path

from legal_engine import build_legal_support
from pdf_generator import generate_pdf_report

# ============================================================
# App Setup
# ============================================================

app = FastAPI(
    title="Outlaw Legal AI",
    description="""
## Automated Legal Support & Analysis Engine

This API provides AI-powered legal analysis for civil cases, focusing on:
- Contract disputes
- Small claims procedures
- Evidence evaluation
- Risk assessment

### For Android/Mobile Integration
Use the `/legal-support` endpoint with JSON requests. The API returns structured data perfect for mobile apps.

### Authentication
Currently open for development. Production deployments should implement API key authentication.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

# Mount static files
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("outlaw")


# ============================================================
# Pydantic Models for Request Validation
# ============================================================

class EvidenceItem(BaseModel):
    label: str = Field(..., json_schema_extra={"example": "Payment proof"})
    description: str = Field(..., json_schema_extra={"example": "Bank transfer receipt"})


class LegalSupportRequest(BaseModel):
    jurisdiction: str = Field(..., json_schema_extra={"example": "California"})
    county: str = Field(..., json_schema_extra={"example": "Riverside"})
    facts: str = Field(..., min_length=20, json_schema_extra={"example": "Buyer failed to pay $5,000 after taking possession of the horse on January 15, 2025."})
    evidence: Optional[List[EvidenceItem]] = Field(default_factory=list)
    requested_output: str = Field("json", description="Output format: 'json' or 'pdf'", json_schema_extra={"example": "json"})

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "jurisdiction": "California",
                    "county": "Riverside",
                    "facts": "Buyer failed to pay $5,000 after taking possession of the horse on January 15, 2025. Multiple payment reminders were sent via email but ignored.",
                    "evidence": [
                        {"label": "Sales Contract", "description": "Signed agreement dated January 10, 2025"},
                        {"label": "Payment Reminders", "description": "Email chain showing 3 payment requests"}
                    ],
                    "requested_output": "json"
                }
            ]
        }
    }


class AnalysisResponse(BaseModel):
    status: str
    data: dict


# ============================================================
# Routes
# ============================================================

@app.get("/", tags=["System"], summary="Welcome")
async def root():
    """Welcome endpoint with API usage information."""
    return {
        "message": "Welcome to Outlaw Legal AI API",
        "usage": "POST /legal-support with JSON body",
        "web_interface": "/ui",
        "documentation": "/docs"
    }


@app.get("/ui", response_class=HTMLResponse, tags=["Web Interface"], include_in_schema=False)
async def web_interface():
    """Serve the web interface."""
    template_path = Path(__file__).parent / "templates" / "index.html"
    if template_path.exists():
        return HTMLResponse(content=template_path.read_text(), status_code=200)
    return HTMLResponse(content="""
        <html>
        <head><title>Outlaw Legal AI</title></head>
        <body style="font-family: sans-serif; text-align: center; padding: 50px;">
            <h1>Outlaw Legal AI</h1>
            <p>API is running. Visit <a href="/docs">/docs</a> for API documentation.</p>
        </body>
        </html>
    """, status_code=200)


@app.get("/api", tags=["System"], summary="API Information")
async def api_info():
    """Get API information for mobile clients."""
    return {
        "name": "Outlaw Legal AI",
        "version": "1.0.0",
        "description": "Automated legal-support and analysis engine",
        "endpoints": {
            "legal_analysis": "POST /legal-support",
            "health": "GET /health",
            "documentation": "GET /docs"
        },
        "supported_outputs": ["json", "pdf"],
        "min_facts_length": 20
    }


@app.get("/health", tags=["System"], summary="Health Check")
async def health_check():
    """Check if the API is running and healthy."""
    return {"status": "ok", "service": "outlaw-legal-ai"}


@app.post("/legal-support", tags=["Legal Analysis"], summary="Generate Legal Support Analysis", response_model=AnalysisResponse, responses={
    200: {"description": "Successful analysis"},
    400: {"description": "Invalid request"},
    500: {"description": "Server error"}
})
async def create_analysis(request: LegalSupportRequest, background_tasks: BackgroundTasks):
    """
    Generate a comprehensive legal support analysis.
    
    This endpoint analyzes the provided case facts and returns:
    - Applicable statutes and legal elements
    - Procedural rules for the jurisdiction
    - Risk assessment with mitigation strategies
    - Case strength scoring
    
    **For Android/Mobile Apps:**
    - Use `requested_output: "json"` for structured data
    - Use `requested_output: "pdf"` to download a formatted report
    """
    try:
        logger.info(f"Processing legal analysis for {request.county}, {request.jurisdiction}")

        evidence_list = [item.model_dump() for item in request.evidence] if request.evidence else []
        
        response_obj = build_legal_support(
            jurisdiction=request.jurisdiction,
            county=request.county,
            facts=request.facts,
            evidence=evidence_list
        )
        data = response_obj.to_dict()

        if request.requested_output.lower() == "pdf":
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                pdf_path = temp_file.name
            generate_pdf_report(data, pdf_path)
            filename = f"OutlawLegalAI_{request.county}_Report.pdf"
            background_tasks.add_task(os.remove, pdf_path)
            return FileResponse(
                pdf_path, 
                media_type="application/pdf", 
                filename=filename,
                headers={"Content-Disposition": f'attachment; filename="{filename}"'}
            )

        return {"status": "success", "data": data}

    except ValueError as ve:
        logger.warning(f"Validation error: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as error:
        logger.exception("Error generating legal analysis:")
        raise HTTPException(status_code=500, detail=f"Server Error: {error}")
