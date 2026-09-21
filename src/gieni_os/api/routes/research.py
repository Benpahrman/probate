"""
Gieni OS Research API Routes
Exposes endpoints for multi-area research across Contacts, Title & Liens, Authority, and Valuation.
Accessible across Workbench, Ops Center, and AI Investigator.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from gieni_os.database.connection import get_db
from gieni_os.database.models import OpportunityModel
from gieni_os.api.deps import get_current_user, ClerkUserContext, require_internal_operator
from gieni_os.research.models import (
    ResearchArea,
    ResearchRequest,
    ResearchDossier,
    ProviderInfo
)
from gieni_os.research.service import ResearchHubService

router = APIRouter(prefix="/research", tags=["Research Hub & Extensible Providers"])

@router.get("/providers", response_model=List[ProviderInfo])
def list_providers() -> List[ProviderInfo]:
    """
    Returns all registered research providers, versions, and supported research domains.
    Extensible: Any new custom data source or vendor adapter appears here automatically.
    """
    return ResearchHubService.list_providers()

@router.post("/execute", response_model=ResearchDossier)
def execute_research(
    req: ResearchRequest,
    db: Session = Depends(get_db),
    user: ClerkUserContext = Depends(require_internal_operator)
) -> ResearchDossier:
    """
    Executes a research sweep across the requested domain:
    - CONTACTS: Skip-trace, phone line types (wireless/landline), DNC scrub, heirs/kin.
    - TITLE: County Auditor deed chain, APN, open mortgages, mechanics/HOA liens, clouds.
    - AUTHORITY: Superior Court probate docket, letters testamentary, RCW 11.68 powers.
    - VALUATION: Assessor value, AVM comps, repair estimates, net equity waterfall.
    - COMPREHENSIVE: Executes 360-degree deep sweep across all 4 domains simultaneously.
    """
    operator_name = getattr(user, "role", "Research Analyst")
    return ResearchHubService.execute_research(req=req, db=db, operator_name=operator_name)

@router.post("/contacts", response_model=ResearchDossier)
def research_contacts(
    req: ResearchRequest,
    db: Session = Depends(get_db),
    user: ClerkUserContext = Depends(require_internal_operator)
) -> ResearchDossier:
    """
    Dedicated endpoint for skip-tracing contacts, fiduciaries, and heirs.
    """
    req.area = ResearchArea.CONTACTS
    operator_name = getattr(user, "role", "Research Analyst")
    return ResearchHubService.execute_research(req=req, db=db, operator_name=operator_name)

@router.post("/title", response_model=ResearchDossier)
def research_title(
    req: ResearchRequest,
    db: Session = Depends(get_db),
    user: ClerkUserContext = Depends(require_internal_operator)
) -> ResearchDossier:
    """
    Dedicated endpoint for deed history, title vesting, and lien encumbrances.
    """
    req.area = ResearchArea.TITLE
    operator_name = getattr(user, "role", "Research Analyst")
    return ResearchHubService.execute_research(req=req, db=db, operator_name=operator_name)

@router.get("/{opportunity_id}/dossier", response_model=ResearchDossier)
def get_opportunity_dossier(
    opportunity_id: str,
    db: Session = Depends(get_db),
    user: ClerkUserContext = Depends(require_internal_operator)
) -> ResearchDossier:
    """
    Retrieves the full comprehensive research dossier for a specific opportunity.
    """
    opp = db.query(OpportunityModel).filter(OpportunityModel.id == opportunity_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found.")
    
    req = ResearchRequest(
        opportunity_id=opp.id,
        area=ResearchArea.COMPREHENSIVE
    )
    return ResearchHubService.execute_research(req=req, db=db, operator_name="Dossier Viewer")
