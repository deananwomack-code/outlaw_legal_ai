"""
Integration tests for the FastAPI app (app.py)
"""
import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_root_endpoint():
    res = client.get("/")
    assert res.status_code == 200
    assert "Welcome" in res.json()["message"]

def test_legal_support_json_response():
    payload = {
        "jurisdiction": "California",
        "county": "Riverside",
        "facts": "Buyer failed to pay after taking possession of goods.",
        "evidence": [{"label": "Payment record", "description": "Bank transfer screenshot"}],
        "requested_output": "json"
    }
    res = client.post("/legal-support", json=payload)
    assert res.status_code == 200
    assert res.json()["status"] == "success"
    data = res.json()["data"]
    assert data["jurisdiction"] == "California"
    assert "score" in data
