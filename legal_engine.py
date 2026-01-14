"""
legal_engine.py  –  Core logic for Outlaw Legal AI
--------------------------------------------------
Fetches statutes/procedures from a public API when possible,
falls back to built-in Riverside/SoCal templates, and builds
a structured legal-support analysis.
"""

from __future__ import annotations
import requests
import logging
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional

from cache_manager import cached, generate_cache_key, get_cached, set_cached

logger = logging.getLogger(__name__)

# ============================================================
# HTTP SESSION FOR CONNECTION REUSE
# ============================================================

# Reuse HTTP session for better performance with connection pooling
_http_session = requests.Session()
_http_session.headers.update({"User-Agent": "Outlaw-Legal-AI/1.0"})

# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class LegalElement:
    name: str
    description: str


@dataclass
class Statute:
    citation: str
    title: str
    jurisdiction: str
    summary: str
    elements: List[LegalElement] = field(default_factory=list)


@dataclass
class ProceduralRule:
    name: str
    description: str


@dataclass
class RiskItem:
    severity: str
    description: str
    mitigation: str


@dataclass
class WinningFactor:
    element_score: int
    evidence_score: int
    clarity_score: int
    risk_penalty: int

    @property
    def overall(self) -> int:
        """Calculate composite winning score."""
        return max(0, (self.element_score + self.evidence_score + self.clarity_score)//3 - self.risk_penalty)

    def to_dict(self) -> Dict[str, int]:
        """Convert to dict including the computed overall property."""
        return {
            "element_score": self.element_score,
            "evidence_score": self.evidence_score,
            "clarity_score": self.clarity_score,
            "risk_penalty": self.risk_penalty,
            "overall": self.overall,
        }


@dataclass
class LegalSupportResponse:
    jurisdiction: str
    county: str
    facts: str
    statutes: List[Statute]
    procedures: List[ProceduralRule]
    risks: List[RiskItem]
    score: WinningFactor

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        # Replace score dict with one that includes the computed 'overall' property
        result["score"] = self.score.to_dict()
        return result


# ============================================================
# PUBLIC API LOOKUP
# ============================================================

# Reduced timeout for faster fallback to local data when API is unreachable
API_TIMEOUT_SECONDS = 3

def fetch_statutes_from_api(jurisdiction: str, query: str) -> List[Statute]:
    """
    Try to get a few statute summaries from a public source (govinfo.gov).
    Fallback to local data if the API is unavailable.
    Results are cached to reduce API calls.
    """
    # Check cache first
    cache_key = generate_cache_key("statutes", jurisdiction, query)
    cached_result = get_cached(cache_key)
    if cached_result is not None:
        logger.info(f"Using cached statutes for {jurisdiction}")
        return cached_result
    
    url = f"https://api.govinfo.gov/collections/{jurisdiction.lower()}code/2022-01-01"
    try:
        api_response = _http_session.get(url, timeout=API_TIMEOUT_SECONDS)
        api_response.raise_for_status()
        data = api_response.json()
        results = []
        for item in data.get("packages", [])[:3]:
            title = item.get("title", "")
            results.append(Statute(
                citation=item.get("packageId", ""),
                title=title[:90],
                jurisdiction=jurisdiction,
                summary=f"Reference from public collection: {title}"
            ))
        logger.info(f"Fetched {len(results)} statutes from API for {jurisdiction}.")
        
        # Cache the results
        set_cached(cache_key, results, ttl=3600)
        
        return results
    except requests.exceptions.RequestException as e:
        logger.warning(f"Statute API fetch failed for {jurisdiction}: {e}")
        return []


# ============================================================
# LOCAL FALLBACK DATA
# ============================================================

def fallback_statutes() -> List[Statute]:
    """Simplified Riverside/SoCal fallback statutes."""
    return [
        Statute(
            citation="Cal. Civ. Code §1550",
            title="Essential Elements of a Contract",
            jurisdiction="California",
            summary="A valid contract requires capacity, consent, lawful object, and consideration.",
            elements=[
                LegalElement("Capacity", "Parties must be legally capable of contracting."),
                LegalElement("Consent", "Mutual assent must exist."),
                LegalElement("Consideration", "Each side gives something of value.")
            ]
        ),
        Statute(
            citation="Cal. Civ. Code §3300",
            title="Damages for Breach of Contract",
            jurisdiction="California",
            summary="Damages equal to detriment caused by breach."
        )
    ]


def fallback_procedures() -> List[ProceduralRule]:
    """Default local procedural guidance for Riverside County."""
    return [
        ProceduralRule("Venue", "File in Riverside County where contract was made or defendant resides."),
        ProceduralRule("Service", "Serve defendant ≥15 days before hearing if in county; ≥20 if out of county."),
        ProceduralRule("Forms", "SC-100 (Claim) and SC-104 (Proof of Service).")
    ]


# ============================================================
# RISK + SCORING
# ============================================================

def assess_risks(facts_lowercase: str) -> List[RiskItem]:
    """Simple keyword-based risk assessment.
    
    Args:
        facts_lowercase: Pre-lowercased facts string for efficient keyword matching
    
    Note:
        Accepts pre-lowercased string to avoid redundant .lower() calls.
        The caller (build_legal_support) converts facts to lowercase once and
        passes it to multiple functions for efficiency.
    """
    risks = []
    if "inspect" in facts_lowercase or "eye" in facts_lowercase:
        risks.append(RiskItem("medium", "Possible nondisclosure claim", "Show refusal to inspect."))
    elif "oral" in facts_lowercase:
        risks.append(RiskItem("medium", "Potential enforceability issue (oral contract).", "Provide corroborating evidence."))
    else:
        risks.append(RiskItem("low", "Minor procedural risk", "Ensure timely filing."))
    return risks


def compute_score(facts: str, facts_lowercase: str, evidence_count: int) -> WinningFactor:
    """Compute a simple case-strength score based on facts length and evidence.
    
    Args:
        facts: Original facts string (for length calculation)
        facts_lowercase: Pre-lowercased facts string for efficient keyword matching
        evidence_count: Number of evidence items provided
    
    Note:
        Accepts both facts and facts_lowercase to avoid redundant .lower() calls.
        The caller (build_legal_support) converts facts to lowercase once and
        passes it to multiple functions for efficiency.
    """
    base_clarity_score = 80 if len(facts) > 60 else 60
    if "breach" in facts_lowercase:
        base_clarity_score += 5
    return WinningFactor(
        element_score=90,
        evidence_score=min(100, 70 + evidence_count * 5),
        clarity_score=min(100, base_clarity_score),
        risk_penalty=10 if "eye" in facts_lowercase else 0
    )


# ============================================================
# MASTER BUILDER
# ============================================================

def build_legal_support(
    jurisdiction: str,
    county: str,
    facts: str,
    evidence: Optional[List[Dict[str, str]]] = None
) -> LegalSupportResponse:
    """Master entry point used by app.py"""
    evidence = evidence or []
    # Convert facts to lowercase once for efficiency across multiple function calls
    facts_lowercase = facts.lower()
    
    statutes = fetch_statutes_from_api(jurisdiction, "contract") or fallback_statutes()
    procedures = fallback_procedures()
    risks = assess_risks(facts_lowercase)
    score = compute_score(facts, facts_lowercase, len(evidence))

    response = LegalSupportResponse(
        jurisdiction=jurisdiction,
        county=county,
        facts=facts,
        statutes=statutes,
        procedures=procedures,
        risks=risks,
        score=score
    )

    logger.info(f"Built legal support response for {jurisdiction}, {county}.")
    return response
