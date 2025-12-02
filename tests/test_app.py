"""
Integration tests for app.py
----------------------------
Uses FastAPI TestClient to simulate API requests and validate responses.
"""

import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_root_endpoint():
    """GET / should return welcome message."""
    res = client.get("/")
    assert res.status_code == 200
    assert "Welcome to Outlaw Legal AI" in res.text


def test_health_check():
    """GET /health should return ok."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_legal_support_json_response():
    """POST /legal-support should return a valid JSON response."""
    payload = {
        "jurisdiction": "California",
        "county": "Riverside",
        "facts": "Buyer failed to pay after taking possession of horse.",
        "evidence": [{"label": "Receipt", "description": "Payment proof"}],
        "requested_output": "json"
    }

    res = client.post("/legal-support", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "success"
    assert "data" in body
    assert "score" in body["data"]


def test_legal_support_pdf_response(tmp_path):
    """POST /legal-support with PDF output should return a PDF file."""
    payload = {
        "jurisdiction": "California",
        "county": "Riverside",
        "facts": "Buyer failed to pay after taking possession of horse.",
        "requested_output": "pdf"
    }

    res = client.post("/legal-support", json=payload)
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
