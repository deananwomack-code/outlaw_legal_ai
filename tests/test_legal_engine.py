"""
Unit tests for legal_engine.py
------------------------------
Verifies that core logic works independently of the API layer.
"""

import pytest
from legal_engine import (
    build_legal_support,
    compute_score,
    assess_risks,
    fallback_statutes,
    fallback_procedures,
)


def test_compute_score_increases_with_evidence():
    """Higher evidence count should increase evidence_score."""
    facts = "simple contract"
    facts_lowercase = facts.lower()
    low = compute_score(facts, facts_lowercase, 0)
    high = compute_score(facts, facts_lowercase, 4)
    assert high.evidence_score > low.evidence_score
    assert 0 <= high.overall <= 100


def test_assess_risks_detects_inspection_issue():
    """Should detect 'inspect' keyword and mark risk as medium."""
    facts = "The buyer refused to inspect the item."
    facts_lowercase = facts.lower()
    risks = assess_risks(facts_lowercase)
    assert any(r.severity == "medium" for r in risks)


def test_fallback_statutes_return_defaults():
    """Fallback statutes should contain California Civil Code references."""
    statutes = fallback_statutes()
    assert any("Cal. Civ. Code" in s.citation for s in statutes)
    assert len(statutes) >= 2


def test_fallback_procedures_have_expected_fields():
    """Procedural rules should contain name and description."""
    procs = fallback_procedures()
    assert all(hasattr(p, "name") and hasattr(p, "description") for p in procs)


def test_build_legal_support_structure():
    """Master builder should return valid LegalSupportResponse."""
    response = build_legal_support(
        jurisdiction="California",
        county="Riverside",
        facts="Buyer claims seller refused inspection.",
        evidence=[{"label": "Contract", "description": "Signed contract copy"}],
    )
    data = response.to_dict()

    assert data["jurisdiction"] == "California"
    assert "statutes" in data
    assert "procedures" in data
    assert "score" in data
    assert isinstance(data["score"]["overall"], int)
