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
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import tempfile
import os
import logging
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time

from legal_engine import build_legal_support
from pdf_generator import generate_pdf_report
from cache_manager import get_cache_stats, clear_cache
from export_manager import export_analysis
from rate_limiter import check_rate_limit, get_rate_limit_stats, reset_rate_limit

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

# Add response compression for better performance
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Mount static files
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("outlaw")

# Thread pool for async execution of CPU-bound tasks
executor = ThreadPoolExecutor(max_workers=4)

# Application start time for uptime tracking
APP_START_TIME = time.time()


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
    requested_output: str = Field("json", description="Output format: 'json', 'pdf', 'html', 'markdown', or 'text'", json_schema_extra={"example": "json"})

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


class BatchAnalysisRequest(BaseModel):
    cases: List[LegalSupportRequest] = Field(..., max_length=10, description="List of cases to analyze (max 10)")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "cases": [
                        {
                            "jurisdiction": "California",
                            "county": "Riverside",
                            "facts": "Contract dispute over $5,000 payment.",
                            "evidence": [{"label": "Contract", "description": "Signed agreement"}],
                            "requested_output": "json"
                        }
                    ]
                }
            ]
        }
    }


class BatchAnalysisResponse(BaseModel):
    status: str
    results: List[Dict[str, Any]]
    processing_time_seconds: float
    total_cases: int
    successful: int
    failed: int


class CacheStats(BaseModel):
    cache_size: int
    max_cache_size: int


class AnalyticsResponse(BaseModel):
    total_requests: int
    cache_stats: Dict[str, int]
    uptime_seconds: float


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
        "supported_outputs": ["json", "pdf", "html", "markdown", "text"],
        "min_facts_length": 20
    }


@app.get("/health", tags=["System"], summary="Health Check")
async def health_check():
    """Check if the API is running and healthy."""
    return {"status": "ok", "service": "outlaw-legal-ai"}


@app.post("/legal-support", tags=["Legal Analysis"], summary="Generate Legal Support Analysis", response_model=AnalysisResponse, responses={
    200: {"description": "Successful analysis"},
    400: {"description": "Invalid request"},
    429: {"description": "Rate limit exceeded"},
    500: {"description": "Server error"}
})
async def create_analysis(request_obj: Request, request: LegalSupportRequest, background_tasks: BackgroundTasks):
    """
    Generate a comprehensive legal support analysis.
    
    This endpoint analyzes the provided case facts and returns:
    - Applicable statutes and legal elements
    - Procedural rules for the jurisdiction
    - Risk assessment with mitigation strategies
    - Case strength scoring
    
    **Rate Limiting:**
    - Limited to 100 requests per minute per IP address
    
    **For Android/Mobile Apps:**
    - Use `requested_output: "json"` for structured data
    - Use `requested_output: "pdf"` to download a formatted report
    - Use `requested_output: "html"` for HTML format
    - Use `requested_output: "markdown"` for Markdown format
    - Use `requested_output: "text"` for plain text format
    """
    # Apply rate limiting
    await check_rate_limit(request_obj)
    
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

        output_format = request.requested_output.lower()
        
        # Handle PDF export
        if output_format == "pdf":
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
        
        # Handle HTML export
        elif output_format in ("html", "htm"):
            html_content = export_analysis(data, "html")
            filename = f"OutlawLegalAI_{request.county}_Report.html"
            return HTMLResponse(
                content=html_content,
                headers={"Content-Disposition": f'attachment; filename="{filename}"'}
            )
        
        # Handle Markdown export
        elif output_format in ("markdown", "md"):
            md_content = export_analysis(data, "markdown")
            filename = f"OutlawLegalAI_{request.county}_Report.md"
            return StreamingResponse(
                iter([md_content]),
                media_type="text/markdown",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'}
            )
        
        # Handle Text export
        elif output_format in ("text", "txt"):
            text_content = export_analysis(data, "text")
            filename = f"OutlawLegalAI_{request.county}_Report.txt"
            return StreamingResponse(
                iter([text_content]),
                media_type="text/plain",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'}
            )

        # Default to JSON
        return {"status": "success", "data": data}

    except ValueError as ve:
        logger.warning(f"Validation error: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as error:
        logger.exception("Error generating legal analysis:")
        raise HTTPException(status_code=500, detail=f"Server Error: {error}")


@app.post("/legal-support/batch", tags=["Legal Analysis"], summary="Batch Analysis for Multiple Cases", response_model=BatchAnalysisResponse, responses={
    429: {"description": "Rate limit exceeded"}
})
async def batch_analysis(request_obj: Request, request: BatchAnalysisRequest, background_tasks: BackgroundTasks):
    """
    Analyze multiple cases in a single request (max 10 cases).
    
    This endpoint processes multiple legal cases concurrently for improved efficiency.
    Perfect for batch processing or comparing multiple scenarios.
    
    **Rate Limiting:**
    - Limited to 100 requests per minute per IP address
    
    **Features:**
    - Concurrent processing for faster results
    - Returns individual results for each case
    - Includes processing statistics
    """
    # Apply rate limiting
    await check_rate_limit(request_obj)
    
    start_time = time.time()
    results = []
    successful = 0
    failed = 0
    
    try:
        # Process cases concurrently
        async def process_single_case(case_request: LegalSupportRequest, case_index: int):
            try:
                evidence_list = [item.model_dump() for item in case_request.evidence] if case_request.evidence else []
                
                # Run in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                response_obj = await loop.run_in_executor(
                    executor,
                    build_legal_support,
                    case_request.jurisdiction,
                    case_request.county,
                    case_request.facts,
                    evidence_list
                )
                
                return {
                    "case_index": case_index,
                    "status": "success",
                    "data": response_obj.to_dict()
                }
            except Exception as e:
                logger.error(f"Error processing case {case_index}: {e}")
                return {
                    "case_index": case_index,
                    "status": "error",
                    "error": str(e)
                }
        
        # Process all cases concurrently
        tasks = [process_single_case(case, idx) for idx, case in enumerate(request.cases)]
        results = await asyncio.gather(*tasks)
        
        # Count successes and failures
        successful = sum(1 for r in results if r["status"] == "success")
        failed = len(results) - successful
        
        processing_time = time.time() - start_time
        
        logger.info(f"Batch analysis completed: {successful} successful, {failed} failed, {processing_time:.2f}s")
        
        return {
            "status": "completed",
            "results": results,
            "processing_time_seconds": round(processing_time, 2),
            "total_cases": len(request.cases),
            "successful": successful,
            "failed": failed
        }
        
    except Exception as error:
        logger.exception("Error in batch analysis:")
        raise HTTPException(status_code=500, detail=f"Batch processing error: {error}")


@app.get("/analytics", tags=["System"], summary="System Analytics", response_model=AnalyticsResponse)
async def get_analytics():
    """
    Get system analytics and performance metrics.
    
    Returns:
    - Cache statistics
    - Request counters (approximated from cache usage)
    - System uptime
    """
    cache_stats = get_cache_stats()
    
    # Calculate actual uptime
    uptime = time.time() - APP_START_TIME
    
    return {
        "total_requests": cache_stats.get("size", 0),  # Approximation based on cache usage
        "cache_stats": cache_stats,
        "uptime_seconds": round(uptime, 2)
    }


@app.delete("/cache", tags=["System"], summary="Clear Cache")
async def clear_system_cache():
    """
    Clear all cached data.
    
    Useful for forcing fresh data retrieval or during development.
    Requires appropriate permissions in production.
    """
    try:
        clear_cache()
        logger.info("Cache cleared via API request")
        return {"status": "success", "message": "Cache cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {e}")


@app.get("/rate-limit/stats", tags=["System"], summary="Rate Limit Statistics")
async def get_rate_limit_statistics():
    """
    Get rate limiter statistics.
    
    Returns information about rate limiting configuration and current state.
    """
    try:
        stats = get_rate_limit_stats()
        return {
            "status": "success",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error getting rate limit stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting rate limit stats: {e}")


@app.delete("/rate-limit/reset", tags=["System"], summary="Reset Rate Limits")
async def reset_rate_limits(client_id: Optional[str] = None):
    """
    Reset rate limits for a specific client or all clients.
    
    Args:
        client_id: Optional client ID (IP address) to reset. If not provided, resets all.
    
    Requires appropriate permissions in production.
    """
    try:
        reset_rate_limit(client_id)
        message = f"Rate limit reset for {client_id}" if client_id else "Rate limit reset for all clients"
        return {"status": "success", "message": message}
    except Exception as e:
        logger.error(f"Error resetting rate limit: {e}")
        raise HTTPException(status_code=500, detail=f"Error resetting rate limit: {e}")


@app.get("/jurisdictions", tags=["Legal Analysis"], summary="List Supported Jurisdictions")
async def list_jurisdictions():
    """
    Get list of supported jurisdictions and counties.
    
    Returns information about supported legal jurisdictions and their counties.
    
    Note: This data is currently hardcoded but could be moved to a configuration
    file or database for better maintainability in production deployments.
    """
    return {
        "jurisdictions": [
            {
                "name": "California",
                "counties": ["Riverside", "Los Angeles", "San Diego", "Orange", "San Francisco"],
                "supported": True
            },
            {
                "name": "New York",
                "counties": ["New York", "Kings", "Queens", "Bronx", "Richmond"],
                "supported": False,
                "note": "Coming soon"
            },
            {
                "name": "Texas",
                "counties": ["Harris", "Dallas", "Bexar", "Travis"],
                "supported": False,
                "note": "Coming soon"
            }
        ]
    }
