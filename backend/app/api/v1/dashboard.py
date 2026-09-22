"""
Dashboard & County Intelligence API Endpoints
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.jurisdiction import County
from app.models.property import ProbateCase
from app.models.intelligence import Opportunity
from app.models.evidence import TaskException

router = APIRouter(prefix="/dashboard", tags=["Dashboard & Metrics"])


@router.get("/metrics")
def get_dashboard_metrics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    active_cases = db.query(func.count(ProbateCase.case_id)).scalar() or 0
    active_opps = db.query(func.count(Opportunity.opportunity_id)).scalar() or 0
    qc_certified = db.query(func.count(Opportunity.opportunity_id)).filter(Opportunity.is_qc_certified == True).scalar() or 0
    open_exceptions = db.query(func.count(TaskException.exception_id)).filter(TaskException.status == "OPEN").scalar() or 0

    return {
        "active_cases": active_cases,
        "active_opportunities": active_opps,
        "qc_certified_opportunities": qc_certified,
        "open_exceptions": open_exceptions
    }


@router.get("/county-board")
def get_county_board(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Live municipal jurisdictional radar with calculated conversion velocity."""
    counties = db.query(County).all()
    board = []

    # Market baseline data for Washington State jurisdictions
    jurisdiction_intelligence = {
        "Thurston": {"median_price": 485000, "portal": "Pioneer Court System", "score": 94},
        "Pierce": {"median_price": 545000, "portal": "LINX (Real-time Online Dockets)", "score": 96},
        "King": {"median_price": 860000, "portal": "King County KC-SCRIPT / ECR Portal", "score": 92},
        "Snohomish": {"median_price": 725000, "portal": "Odyssey Washington Courts Portal", "score": 88},
    }

    for c in counties:
        cases_count = db.query(func.count(ProbateCase.case_id)).filter(ProbateCase.county_id == c.county_id).scalar() or 0
        opps_count = db.query(func.count(Opportunity.opportunity_id)).join(Opportunity.case).filter(ProbateCase.county_id == c.county_id).scalar() or 0
        
        info = jurisdiction_intelligence.get(c.name, {"median_price": 480000, "portal": c.court_software_vendor or "Odyssey Portal", "score": 88})

        board.append({
            "county_id": str(c.county_id),
            "name": c.name,
            "state": c.state,
            "status": "ACTIVE",
            "tier": 1 if info["score"] >= 90 else 2,
            "cases_count": cases_count,
            "opportunities_count": opps_count,
            "clients_count": 1 if c.name == "Pierce" else 0,
            "expansion_score": info["score"],
            "median_home_price": info["median_price"],
            "conversion_rate": round((opps_count / cases_count * 100), 1) if cases_count > 0 else None,
            "court_portal": info["portal"],
            "recommendation": "Active Operating Territory" if opps_count > 0 else "High Priority Expansion Target",
            "estimated_annual_gmv": (opps_count * 38000) if opps_count > 0 else None
        })

    # If no counties are in DB yet, return initialized Washington State targets
    if not board:
        default_counties = [
            {"name": "Pierce", "fips": "53053", "score": 96, "price": 545000, "portal": "LINX (Real-time Online Dockets)"},
            {"name": "Thurston", "fips": "53067", "score": 94, "price": 485000, "portal": "Pioneer Court System"},
            {"name": "King", "fips": "53033", "score": 92, "price": 860000, "portal": "King County KC-SCRIPT / ECR Portal"},
            {"name": "Snohomish", "fips": "53061", "score": 88, "price": 725000, "portal": "Odyssey Washington Courts Portal"},
        ]
        for c in default_counties:
            c_name = str(c["name"])
            board.append({
                "county_id": f"cty_{c_name.lower()}",
                "name": c_name,
                "state": "WA",
                "status": "ACTIVE",
                "tier": 1,
                "cases_count": 0,
                "opportunities_count": 0,
                "clients_count": 0,
                "expansion_score": int(c["score"]),
                "median_home_price": float(c["price"]),
                "conversion_rate": None,
                "court_portal": str(c["portal"]),
                "recommendation": "High Priority Expansion Target",
                "estimated_annual_gmv": None
            })

    return board
