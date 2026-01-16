"""
Tests for new API endpoints
--------------------------
Validates batch analysis, analytics, and export endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_batch_analysis_single_case():
    """Batch endpoint should handle single case."""
    payload = {
        "cases": [
            {
                "jurisdiction": "California",
                "county": "Riverside",
                "facts": "Buyer failed to pay after taking possession of horse.",
                "evidence": [{"label": "Receipt", "description": "Payment proof"}],
                "requested_output": "json"
            }
        ]
    }
    
    res = client.post("/legal-support/batch", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "completed"
    assert body["total_cases"] == 1
    assert body["successful"] >= 1
    assert "results" in body
    assert len(body["results"]) == 1


def test_batch_analysis_multiple_cases():
    """Batch endpoint should handle multiple cases."""
    payload = {
        "cases": [
            {
                "jurisdiction": "California",
                "county": "Riverside",
                "facts": "First case with sufficient facts for analysis.",
                "requested_output": "json"
            },
            {
                "jurisdiction": "California",
                "county": "Los Angeles",
                "facts": "Second case with different jurisdiction and facts.",
                "requested_output": "json"
            }
        ]
    }
    
    res = client.post("/legal-support/batch", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "completed"
    assert body["total_cases"] == 2
    assert len(body["results"]) == 2
    assert "processing_time_seconds" in body


def test_batch_analysis_max_limit():
    """Batch endpoint should enforce max 10 cases limit."""
    # Create 11 cases (exceeds limit)
    cases = [
        {
            "jurisdiction": "California",
            "county": "Riverside",
            "facts": f"Case {i} with sufficient facts for analysis purposes.",
            "requested_output": "json"
        }
        for i in range(11)
    ]
    
    payload = {"cases": cases}
    
    res = client.post("/legal-support/batch", json=payload)
    # Should return validation error
    assert res.status_code == 422


def test_analytics_endpoint():
    """Analytics endpoint should return system metrics."""
    res = client.get("/analytics")
    assert res.status_code == 200
    body = res.json()
    assert "cache_stats" in body
    assert "total_requests" in body
    assert "uptime_seconds" in body


def test_clear_cache_endpoint():
    """Cache clear endpoint should work."""
    res = client.delete("/cache")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "success"


def test_jurisdictions_endpoint():
    """Jurisdictions endpoint should return supported jurisdictions."""
    res = client.get("/jurisdictions")
    assert res.status_code == 200
    body = res.json()
    assert "jurisdictions" in body
    assert len(body["jurisdictions"]) > 0
    
    # Check California is listed
    ca_jurisdiction = next((j for j in body["jurisdictions"] if j["name"] == "California"), None)
    assert ca_jurisdiction is not None
    assert ca_jurisdiction["supported"] is True
    assert "counties" in ca_jurisdiction


def test_legal_support_html_export():
    """Legal support endpoint should support HTML export."""
    payload = {
        "jurisdiction": "California",
        "county": "Riverside",
        "facts": "Buyer failed to pay after taking possession of horse.",
        "requested_output": "html"
    }
    
    res = client.post("/legal-support", json=payload)
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert "<!DOCTYPE html>" in res.text


def test_legal_support_markdown_export():
    """Legal support endpoint should support Markdown export."""
    payload = {
        "jurisdiction": "California",
        "county": "Riverside",
        "facts": "Buyer failed to pay after taking possession of horse.",
        "requested_output": "markdown"
    }
    
    res = client.post("/legal-support", json=payload)
    assert res.status_code == 200
    assert "# Legal Support Analysis Report" in res.text


def test_legal_support_text_export():
    """Legal support endpoint should support plain text export."""
    payload = {
        "jurisdiction": "California",
        "county": "Riverside",
        "facts": "Buyer failed to pay after taking possession of horse.",
        "requested_output": "text"
    }
    
    res = client.post("/legal-support", json=payload)
    assert res.status_code == 200
    assert "LEGAL SUPPORT ANALYSIS REPORT" in res.text


def test_api_info_updated():
    """API info should reflect new supported formats."""
    res = client.get("/api")
    assert res.status_code == 200
    body = res.json()
    assert "supported_outputs" in body
    assert "html" in body["supported_outputs"]
    assert "markdown" in body["supported_outputs"]
    assert "text" in body["supported_outputs"]


def test_batch_analysis_includes_timing():
    """Batch analysis should include processing time."""
    payload = {
        "cases": [
            {
                "jurisdiction": "California",
                "county": "Riverside",
                "facts": "Test case with sufficient facts for proper analysis.",
                "requested_output": "json"
            }
        ]
    }
    
    res = client.post("/legal-support/batch", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert "processing_time_seconds" in body
    assert body["processing_time_seconds"] >= 0


def test_batch_analysis_error_handling():
    """Batch analysis should handle errors gracefully."""
    # Invalid facts (too short)
    payload = {
        "cases": [
            {
                "jurisdiction": "California",
                "county": "Riverside",
                "facts": "Too short",  # Less than minimum length
                "requested_output": "json"
            }
        ]
    }
    
    res = client.post("/legal-support/batch", json=payload)
    # Should return validation error
    assert res.status_code == 422
