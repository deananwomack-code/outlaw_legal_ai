"""
Unit tests for legal_engine.py
"""
import pytest
from legal_engine import build_legal_support, assess_risks, compute_score

def test_assess_risks_keywords():
    result = assess_risks("The buyer refused inspection of the item.")
    assert any(r.severity == "medium" for r in result)

def test_compute_score_with_evidence():
    score = compute_score("Breach of contract involving inspection.", evidence_count=3)
    assert score.overall > 50
    assert isinstance(score.overall, int)

def test_build_legal_support_output_structure():
    response = build_legal_support(
        jurisdiction="California",
        county="Riverside",
        facts="Seller failed to disclose inspection issue before sale.",
        evidence=[{"label": "Email", "desc": "Proof of communication"}]
    )
    data = response.to_dict()
    assert "jurisdiction" in data
    assert len(data["statutes"]) >= 1
    assert "score" in data
