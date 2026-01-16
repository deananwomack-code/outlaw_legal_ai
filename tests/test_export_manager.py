"""
Tests for export_manager.py
--------------------------
Validates multi-format export functionality.
"""

import pytest
from export_manager import (
    export_to_html,
    export_to_markdown,
    export_to_text,
    export_analysis,
)


# Sample test data
SAMPLE_DATA = {
    "jurisdiction": "California",
    "county": "Riverside",
    "facts": "Buyer failed to pay $5,000 after taking possession of the horse.",
    "statutes": [
        {
            "citation": "Cal. Civ. Code §1550",
            "title": "Essential Elements of a Contract",
            "summary": "A valid contract requires capacity, consent, lawful object, and consideration.",
            "elements": [
                {"name": "Capacity", "description": "Parties must be legally capable."},
                {"name": "Consent", "description": "Mutual assent must exist."}
            ]
        }
    ],
    "procedures": [
        {"name": "Venue", "description": "File in Riverside County"},
        {"name": "Service", "description": "Serve defendant ≥15 days before hearing"}
    ],
    "risks": [
        {"severity": "medium", "description": "Possible issue", "mitigation": "Provide evidence"}
    ],
    "score": {
        "overall": 75,
        "element_score": 90,
        "evidence_score": 80,
        "clarity_score": 85,
        "risk_penalty": 10
    }
}


def test_export_to_html():
    """HTML export should generate valid HTML with all sections."""
    html = export_to_html(SAMPLE_DATA)
    
    assert "<!DOCTYPE html>" in html
    assert "<html" in html
    assert SAMPLE_DATA["jurisdiction"] in html
    assert SAMPLE_DATA["county"] in html
    assert SAMPLE_DATA["facts"] in html
    assert "Cal. Civ. Code §1550" in html
    assert "Venue" in html
    assert "Possible issue" in html
    assert "75" in html  # Overall score


def test_export_to_markdown():
    """Markdown export should generate valid markdown with all sections."""
    md = export_to_markdown(SAMPLE_DATA)
    
    assert "# Legal Support Analysis Report" in md
    assert f"**Jurisdiction:** {SAMPLE_DATA['jurisdiction']}" in md
    assert f"**County:** {SAMPLE_DATA['county']}" in md
    assert SAMPLE_DATA["facts"] in md
    assert "Cal. Civ. Code §1550" in md
    assert "## Procedural Rules" in md
    assert "## Risk Assessment" in md
    assert "## Case Strength Score" in md


def test_export_to_text():
    """Text export should generate plain text with all sections."""
    text = export_to_text(SAMPLE_DATA)
    
    assert "LEGAL SUPPORT ANALYSIS REPORT" in text
    assert f"Jurisdiction: {SAMPLE_DATA['jurisdiction']}" in text
    assert f"County: {SAMPLE_DATA['county']}" in text
    assert SAMPLE_DATA["facts"] in text
    assert "Cal. Civ. Code §1550" in text
    assert "PROCEDURAL RULES" in text
    assert "RISK ASSESSMENT" in text
    assert "CASE STRENGTH SCORE" in text


def test_export_analysis_html():
    """export_analysis should route to HTML export correctly."""
    result = export_analysis(SAMPLE_DATA, "html")
    assert "<!DOCTYPE html>" in result


def test_export_analysis_markdown():
    """export_analysis should route to Markdown export correctly."""
    result = export_analysis(SAMPLE_DATA, "markdown")
    assert "# Legal Support Analysis Report" in result


def test_export_analysis_text():
    """export_analysis should route to Text export correctly."""
    result = export_analysis(SAMPLE_DATA, "text")
    assert "LEGAL SUPPORT ANALYSIS REPORT" in result


def test_export_analysis_case_insensitive():
    """export_analysis should handle format names case-insensitively."""
    html = export_analysis(SAMPLE_DATA, "HTML")
    assert "<!DOCTYPE html>" in html
    
    md = export_analysis(SAMPLE_DATA, "MARKDOWN")
    assert "# Legal Support Analysis Report" in md


def test_export_analysis_aliases():
    """export_analysis should support format aliases."""
    # HTML aliases
    html1 = export_analysis(SAMPLE_DATA, "html")
    html2 = export_analysis(SAMPLE_DATA, "htm")
    assert html1 == html2
    
    # Markdown aliases
    md1 = export_analysis(SAMPLE_DATA, "markdown")
    md2 = export_analysis(SAMPLE_DATA, "md")
    assert md1 == md2
    
    # Text aliases
    txt1 = export_analysis(SAMPLE_DATA, "text")
    txt2 = export_analysis(SAMPLE_DATA, "txt")
    assert txt1 == txt2


def test_export_analysis_invalid_format():
    """export_analysis should raise ValueError for invalid formats."""
    with pytest.raises(ValueError, match="Unsupported export format"):
        export_analysis(SAMPLE_DATA, "invalid_format")


def test_html_export_handles_missing_data():
    """HTML export should handle missing data gracefully."""
    minimal_data = {
        "jurisdiction": "California",
        "county": "Test",
        "facts": "Test facts"
    }
    
    html = export_to_html(minimal_data)
    assert "<!DOCTYPE html>" in html
    assert "California" in html


def test_markdown_export_with_elements():
    """Markdown export should properly format statute elements."""
    md = export_to_markdown(SAMPLE_DATA)
    assert "**Elements:**" in md
    assert "- **Capacity:" in md
    assert "- **Consent:" in md


def test_text_export_formatting():
    """Text export should use proper separators and formatting."""
    text = export_to_text(SAMPLE_DATA)
    assert "=" * 70 in text  # Header separator
    assert "-" * 70 in text  # Section separator
