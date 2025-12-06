"""
app.py — FastAPI entrypoint for Outlaw Legal AI
-----------------------------------------------
Starts the API service that mobile/web clients will call.

Endpoints:
  POST /legal-support   →  JSON or PDF report
  GET  /                →  welcome message
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import tempfile
import os
import logging

from legal_engine import build_legal_support
from pdf_generator import generate_pdf_report

# ============================================================
# App Setup
# ============================================================

app = FastAPI(
    title="Outlaw Legal AI",
    description="Automated legal-support and analysis engine.",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    facts: str = Field(..., min_length=20, json_schema_extra={"example": "Buyer failed to pay after taking possession of horse."})
    evidence: Optional[List[EvidenceItem]] = []
    requested_output: str = Field("json", description="json or pdf", json_schema_extra={"example": "json"})


# ============================================================
# Routes
# ============================================================

@app.get("/", tags=["System"])
async def root():
    return {
        "message": "Welcome to Outlaw Legal AI API",
        "usage": "POST /legal-support with JSON body",
    }


@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok"}


@app.post("/legal-support", tags=["Legal Analysis"], summary="Generate a legal support analysis")
async def create_analysis(request: LegalSupportRequest, background_tasks: BackgroundTasks):
    try:
        logger.info(f"Processing legal analysis for {request.county}, {request.jurisdiction}")

        response_obj = build_legal_support(
            jurisdiction=request.jurisdiction,
            county=request.county,
            facts=request.facts,
            evidence=[evidence_item.model_dump() for evidence_item in request.evidence]
        )
        data = response_obj.to_dict()

        # PDF output
        if request.requested_output.lower() == "pdf":
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                pdf_path = temp_file.name
            generate_pdf_report(data, pdf_path)
            filename = f"OutlawLegalAI_{request.county}_Report.pdf"
            background_tasks.add_task(os.remove, pdf_path)
            return FileResponse(pdf_path, media_type="application/pdf", filename=filename)

        # JSON output
        return {"status": "success", "data": data}

    except Exception as error:
        logger.exception("Error generating legal analysis:")
        raise HTTPException(status_code=500, detail=f"Server Error: {error}")
