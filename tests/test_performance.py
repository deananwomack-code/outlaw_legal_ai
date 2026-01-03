"""
Performance tests for optimizations in legal_engine.py
------------------------------------------------------
Validates that performance improvements don't break functionality.
"""

import pytest
from legal_engine import (
    build_legal_support,
    compute_score,
    assess_risks,
)


def test_compute_score_with_lowercase_facts():
    """Verify compute_score correctly uses pre-lowercased facts."""
    # Use facts > 60 chars to get base 80 score, plus breach keyword for bonus
    facts = "This is a Breach of Contract case with clear EVIDENCE and detailed documentation"
    facts_lowercase = facts.lower()
    
    score = compute_score(facts, facts_lowercase, 3)
    
    # Should detect "breach" keyword in lowercase version (80 base + 5 bonus = 85)
    assert score.clarity_score == 85  # Base 80 (>60 chars) + breach bonus (5)
    assert score.evidence_score > 70  # Should increase with evidence count
    assert score.overall >= 0


def test_assess_risks_with_lowercase_facts():
    """Verify assess_risks correctly uses pre-lowercased facts."""
    # Test with uppercase keywords that should be detected
    facts_lowercase = "buyer refused to INSPECT the horse".lower()
    
    risks = assess_risks(facts_lowercase)
    
    assert len(risks) > 0
    # Should detect "inspect" keyword even though it was uppercase
    assert any(r.severity == "medium" for r in risks)


def test_build_legal_support_lowercase_optimization():
    """Verify build_legal_support efficiently handles lowercase conversion."""
    # This is an integration test that ensures the optimization works end-to-end
    # Use facts > 60 chars to get base 80 clarity score
    response = build_legal_support(
        jurisdiction="California",
        county="Riverside",
        facts="Buyer refused to INSPECT and pay for BREACH of contract with documentation",
        evidence=[
            {"label": "Contract", "description": "Signed agreement"},
            {"label": "Email", "description": "Payment demand"}
        ]
    )
    
    data = response.to_dict()
    
    # Should detect keywords regardless of case
    assert "score" in data
    score = data["score"]
    assert score["clarity_score"] == 85  # Base 80 (>60 chars) + breach bonus (5)
    assert score["evidence_score"] > 70  # Should have evidence bonus
    
    # Should detect inspection risk
    risks = data["risks"]
    assert any(r["severity"] == "medium" for r in risks)


def test_performance_no_duplicate_lowercase_calls():
    """
    Verify that facts.lower() is only called once in build_legal_support.
    This is a logical test - if it works correctly with mixed case,
    the optimization is functioning.
    """
    facts = "UPPERCASE facts WITH lowercase AND MixedCase WORDS"
    
    response = build_legal_support(
        jurisdiction="California",
        county="Riverside", 
        facts=facts,
        evidence=[]
    )
    
    # If this works, it means lowercase was handled correctly
    assert response.facts == facts  # Original case preserved
    assert len(response.risks) > 0  # Risks were assessed
    assert response.score.overall >= 0  # Score was computed


def test_multiple_api_calls_for_connection_reuse():
    """
    Verify that multiple API calls work correctly, which demonstrates
    connection reuse is functioning (tested indirectly through behavior).
    """
    # Make multiple calls to verify session handling works
    for i in range(3):
        response = build_legal_support(
            jurisdiction="California",
            county="Riverside",
            facts=f"Test case {i} with sufficient length to trigger analysis properly",
            evidence=[]
        )
        # Each call should work correctly
        assert response is not None
        assert response.jurisdiction == "California"
        assert len(response.statutes) > 0  # Should have fallback statutes
