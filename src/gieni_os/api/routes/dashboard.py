"""
Operations Dashboard API Routes
Provides aggregated metrics and dedicated operational queues:
- QC Queue
- Exception Queue
- Authority Queue
- County Board
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from gieni_os.database.connection import get_db
from gieni_os.database.models import (
    CountyModel,
    ClientModel,
    ProbateCaseModel,
    OpportunityModel,
    ExceptionModel
)

router = APIRouter(prefix="/dashboard", tags=["Operations Dashboard"])

@router.get("/metrics")
def get_metrics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    total_cases = db.query(func.count(ProbateCaseModel.id)).scalar() or 0
    total_opportunities = db.query(func.count(OpportunityModel.id)).scalar() or 0
    delivered_opportunities = db.query(func.count(OpportunityModel.id)).filter(OpportunityModel.workflow_stage == "DELIVERED").scalar() or 0
    open_exceptions = db.query(func.count(ExceptionModel.id)).filter(ExceptionModel.status == "OPEN").scalar() or 0
    active_counties = db.query(func.count(CountyModel.id)).filter(CountyModel.status == "ACTIVE").scalar() or 0
    active_clients = db.query(func.count(ClientModel.id)).filter(ClientModel.status == "ACTIVE").scalar() or 0

    # Authority accuracy: resolved authority vs total
    resolved_auth = db.query(func.count(OpportunityModel.id)).filter(OpportunityModel.authority_status != "UNRESOLVED").scalar() or 0
    auth_accuracy = round((resolved_auth / total_opportunities * 100), 1) if total_opportunities > 0 else None

    # QC Pass rate: approved/delivered vs total QC-tested
    qc_count = db.query(func.count(OpportunityModel.id)).filter(OpportunityModel.workflow_stage.in_(["QC", "READY", "DELIVERED"])).scalar() or 0
    qc_pass = db.query(func.count(OpportunityModel.id)).filter(OpportunityModel.workflow_stage.in_(["READY", "DELIVERED"])).scalar() or 0
    qc_pass_rate = round((qc_pass / qc_count * 100), 1) if qc_count > 0 else None

    return {
        "total_cases": total_cases,
        "cases_processed": total_cases,
        "total_opportunities": total_opportunities,
        "authority_accuracy_pct": auth_accuracy,
        "qc_pass_rate_pct": qc_pass_rate,
        "delivered_opportunities": delivered_opportunities,
        "active_counties": active_counties,
        "open_exceptions": open_exceptions,
        "active_clients": active_clients
    }

@router.get("/queues")
def get_queues(db: Session = Depends(get_db)) -> Dict[str, Any]:
    def format_opp(o):
        return {
            "id": o.id,
            "case_id": o.case_id,
            "county_id": o.county_id,
            "workflow_stage": o.workflow_stage,
            "priority": o.priority,
            "authority_status": o.authority_status,
            "score": o.score,
            "created_at": o.created_at.isoformat() if o.created_at else None
        }

    # 1. Property Queue (NEW, PROPERTY_MATCH)
    property_items = db.query(OpportunityModel).filter(OpportunityModel.workflow_stage.in_(["NEW", "PROPERTY_MATCH"])).all()

    # 2. Ownership Queue (OWNERSHIP)
    ownership_items = db.query(OpportunityModel).filter(OpportunityModel.workflow_stage == "OWNERSHIP").all()

    # 3. Authority Queue (AUTHORITY or UNRESOLVED)
    authority_items = db.query(OpportunityModel).filter(
        (OpportunityModel.workflow_stage == "AUTHORITY") | (OpportunityModel.authority_status == "UNRESOLVED")
    ).all()

    # 4. QC Queue (QC)
    qc_items = db.query(OpportunityModel).filter(OpportunityModel.workflow_stage == "QC").all()

    # 5. Exception Queue
    exception_items = db.query(ExceptionModel).filter(ExceptionModel.status == "OPEN").all()

    # 6. Delivery Queue (READY, DELIVERED)
    delivery_items = db.query(OpportunityModel).filter(OpportunityModel.workflow_stage.in_(["READY", "DELIVERED"])).all()

    return {
        "property_queue": [format_opp(o) for o in property_items],
        "ownership_queue": [format_opp(o) for o in ownership_items],
        "authority_queue": [format_opp(o) for o in authority_items],
        "qc_queue": [format_opp(o) for o in qc_items],
        "exception_queue": [
            {
                "id": e.id,
                "opportunity_id": e.opportunity_id,
                "type": e.type,
                "severity": e.severity,
                "status": e.status,
                "assignee": e.assignee,
                "notes": e.notes,
                "created_at": e.created_at.isoformat() if e.created_at else None
            }
            for e in exception_items
        ],
        "delivery_queue": [format_opp(o) for o in delivery_items]
    }

@router.get("/county-board")
def get_county_board(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    counties = db.query(CountyModel).all()
    board = []
    for c in counties:
        cases_count = db.query(func.count(ProbateCaseModel.id)).filter(ProbateCaseModel.county_id == c.id).scalar() or 0
        opps_count = db.query(func.count(OpportunityModel.id)).filter(OpportunityModel.county_id == c.id).scalar() or 0
        clients_count = db.query(func.count(ClientModel.id)).filter(ClientModel.county_id == c.id).scalar() or 0
        # County expansion metrics & intelligence
        median_prices = {
            "King": 860000,
            "Pierce": 545000,
            "Thurston": 495000,
            "Snohomish": 725000,
            "Kitsap": 515000,
            "Clark": 520000,
            "Spokane": 395000
        }
        portal_types = {
            "Pierce": "LINX (Real-time Online Dockets)",
            "Thurston": "Odyssey Portal & County Clerk eFiling",
            "King": "King County KC-SCRIPT / ECR Portal",
            "Snohomish": "Odyssey Washington Courts Portal",
            "Kitsap": "Odyssey Portal"
        }
        med_price = median_prices.get(c.name, 480000)
        portal = portal_types.get(c.name, "Washington Courts Odyssey")
        exp_score = 96 if c.name == "Pierce" else 94 if c.name == "Thurston" else 92 if c.name == "King" else 88
        recommendation = "Exclusive Contract Active" if clients_count > 0 else "High Priority Expansion Target"

        board.append({
            "county_id": c.id,
            "name": c.name,
            "state": c.state,
            "status": c.status,
            "tier": c.tier,
            "cases_count": cases_count,
            "opportunities_count": opps_count,
            "clients_count": clients_count,
            "expansion_score": exp_score,
            "median_home_price": med_price,
            "conversion_rate": round((opps_count / cases_count * 100), 1) if cases_count > 0 else None,
            "court_portal": portal,
            "recommendation": recommendation,
            "estimated_annual_gmv": (opps_count * 38000) if opps_count > 0 else None
        })
    return board
