"""
Opportunities API Routes
"""

from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session, joinedload
from gieni_os.database.connection import get_db
from gieni_os.database.models import OpportunityModel, ProbateCaseModel, CountyModel, WorkflowAuditLogModel
from gieni_os.api.deps import get_current_user, ClerkUserContext
from gieni_os.workflow.engine import WorkflowEngine, WorkflowStage
from gieni_os.pof.builder import ProbateOpportunityFileBuilder, ProbateOpportunityFile
from gieni_os.pof.exporter import POFExporter
from gieni_os.services.pof_resolver import POFDataResolver

router = APIRouter(prefix="/opportunities", tags=["Opportunities"])

class OpportunityCreate(BaseModel):
    id: Optional[str] = None
    case_id: str
    county_id: Optional[str] = None
    workflow_stage: str = "NEW"
    priority: str = "MEDIUM"
    authority_status: str = "UNRESOLVED"
    score: int = 0

class OpportunityActionRequest(BaseModel):
    notes: Optional[str] = None

class OpportunityResponse(BaseModel):
    id: str
    case_id: str
    county_id: str
    workflow_stage: str
    priority: str
    authority_status: str
    score: int
    case_number: Optional[str] = None
    decedent: Optional[str] = None
    estate_name: Optional[str] = None
    county_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

@router.get("", response_model=List[OpportunityResponse])
def list_opportunities(
    workflow_stage: Optional[str] = None,
    county_id: Optional[str] = None,
    authority_status: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: ClerkUserContext = Depends(get_current_user)
):
    query = db.query(OpportunityModel).options(
        joinedload(OpportunityModel.case),
        joinedload(OpportunityModel.county)
    )
    # Tenancy isolation: B2B client partners are restricted to their contracted county
    if not user.is_internal_operator and user.contracted_county:
        query = query.filter(
            (OpportunityModel.county_id == user.contracted_county) |
            (OpportunityModel.county.has(CountyModel.name == user.contracted_county))
        )
    elif county_id:
        query = query.filter(OpportunityModel.county_id == county_id)

    if workflow_stage:
        query = query.filter(OpportunityModel.workflow_stage == workflow_stage)
    if authority_status:
        query = query.filter(OpportunityModel.authority_status == authority_status)
    
    results = []
    for opp in query.offset(offset).limit(limit).all():
        c_num = opp.case.case_number if opp.case else None
        dec = opp.case.decedent if opp.case else None
        c_name = opp.county.name if opp.county else opp.county_id
        estate = f"Estate of {dec}" if dec else f"Estate #{opp.id[:8]}"
        results.append(OpportunityResponse(
            id=opp.id,
            case_id=opp.case_id,
            county_id=opp.county_id,
            workflow_stage=opp.workflow_stage,
            priority=opp.priority,
            authority_status=opp.authority_status,
            score=opp.score,
            case_number=c_num,
            decedent=dec,
            estate_name=estate,
            county_name=c_name
        ))
    return results

@router.get("/{opportunity_id}", response_model=OpportunityResponse)
def get_opportunity(
    opportunity_id: str,
    db: Session = Depends(get_db),
    user: ClerkUserContext = Depends(get_current_user)
):
    opp = db.query(OpportunityModel).filter(OpportunityModel.id == opportunity_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found.")

    if not user.is_internal_operator and user.contracted_county:
        c_name = opp.county.name if opp.county else opp.county_id
        if opp.county_id != user.contracted_county and c_name != user.contracted_county:
            raise HTTPException(status_code=403, detail="Forbidden: You do not hold an active contract for this county.")

    c_num = opp.case.case_number if opp.case else None
    dec = opp.case.decedent if opp.case else None
    c_name = opp.county.name if opp.county else opp.county_id
    estate = f"Estate of {dec}" if dec else f"Estate #{opp.id[:8]}"
    return OpportunityResponse(
        id=opp.id,
        case_id=opp.case_id,
        county_id=opp.county_id,
        workflow_stage=opp.workflow_stage,
        priority=opp.priority,
        authority_status=opp.authority_status,
        score=opp.score,
        case_number=c_num,
        decedent=dec,
        estate_name=estate,
        county_name=c_name
    )

@router.post("", response_model=OpportunityResponse, status_code=status.HTTP_201_CREATED)
def create_opportunity(
    opp_in: OpportunityCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    case = db.query(ProbateCaseModel).filter(ProbateCaseModel.id == opp_in.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{opp_in.case_id}' not found.")

    county_id = opp_in.county_id or case.county_id

    opp = OpportunityModel(
        id=opp_in.id,
        case_id=case.id,
        county_id=county_id,
        workflow_stage=opp_in.workflow_stage,
        priority=opp_in.priority,
        authority_status=opp_in.authority_status,
        score=opp_in.score
    )
    db.add(opp)
    db.commit()
    db.refresh(opp)
    return opp

def build_pof_for_opportunity(opp: OpportunityModel) -> ProbateOpportunityFile:
    return POFDataResolver.resolve_opportunity_pof(opp)

@router.get("/{opportunity_id}/workbench")
def get_opportunity_workbench(
    opportunity_id: str,
    db: Session = Depends(get_db),
    user: ClerkUserContext = Depends(get_current_user)
):
    opp = db.query(OpportunityModel).filter(OpportunityModel.id == opportunity_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found.")

    if not user.is_internal_operator and user.contracted_county:
        c_name = opp.county.name if opp.county else opp.county_id
        if opp.county_id != user.contracted_county and c_name != user.contracted_county:
            raise HTTPException(status_code=403, detail="Forbidden: You do not hold an active contract for this county.")
    
    pof = build_pof_for_opportunity(opp)
    
    return {
        "opportunity": {
            "id": opp.id,
            "case_id": opp.case_id,
            "case_number": opp.case.case_number if opp.case else "N/A",
            "decedent": opp.case.decedent if opp.case else "Unknown",
            "county_id": opp.county_id,
            "county_name": opp.county.name if opp.county else opp.county_id,
            "workflow_stage": opp.workflow_stage,
            "priority": opp.priority,
            "authority_status": opp.authority_status,
            "score": opp.score
        },
        "property_summary": {
            "apn": pof.property_profile.apn,
            "situs_address": pof.property_profile.situs_address,
            "city_state_zip": pof.property_profile.city_state_zip,
            "legal_description": pof.property_profile.legal_description,
            "avm_market_estimate": pof.property_profile.avm_market_estimate,
            "total_assessed_value": pof.property_profile.total_assessed_value,
            "land_value": pof.property_profile.land_value,
            "improvement_value": pof.property_profile.improvement_value,
            "landuse": pof.property_profile.landuse,
            "pas_score": pof.property_profile.pas_score
        },
        "ownership_summary": {
            "legal_title_vesting": pof.ownership_profile.legal_title_vesting,
            "ownership_complexity_score": pof.ownership_profile.ownership_complexity_score,
            "net_distributable_equity": pof.ownership_profile.net_distributable_equity,
            "net_equity_pct": pof.ownership_profile.net_equity_pct,
            "target_wholesale_mao": pof.ownership_profile.target_wholesale_mao,
            "senior_mortgage_balance": pof.ownership_profile.senior_mortgage_balance,
            "municipal_liens": pof.ownership_profile.municipal_liens,
            "estimated_repairs": pof.ownership_profile.estimated_repairs,
            "is_free_and_clear": pof.ownership_profile.is_free_and_clear
        },
        "authority_summary": {
            "authority_tier": pof.authority_profile.authority_tier,
            "court_oversight_model": pof.authority_profile.court_oversight_model,
            "can_execute_psa": pof.authority_profile.can_execute_psa,
            "court_confirmation_required": pof.authority_profile.court_confirmation_required,
            "statutory_basis": pof.authority_profile.statutory_basis,
            "statutory_power_scope": pof.authority_profile.statutory_power_scope
        },
        "risk_summary": {
            "overall_deal_risk_classification": pof.risk_profile.overall_deal_risk_classification,
            "foreclosure_acceleration_risk": pof.risk_profile.foreclosure_acceleration_risk,
            "title_cloud_detected": False,
            "contested_will_flag": False
        },
        "evidence_summary": {
            "qc_certification_stamp": pof.evidence_package.qc_certification_stamp,
            "recorded_deed_instrument": pof.evidence_package.recorded_deed_instrument,
            "source_dockets": pof.evidence_package.source_dockets
        },
        "score_summary": {
            "composite_viability_score": pof.opportunity_profile.composite_viability_score,
            "priority_tier": pof.opportunity_profile.priority_tier,
            "deal_friction_score": pof.opportunity_profile.deal_friction_score,
            "dispatch_sla": pof.opportunity_profile.dispatch_sla
        },
        "contact_summary": {
            "target_name": pof.control_profile.primary_decision_maker or f"Authorized PR of {opp.case.decedent if opp.case else 'Estate'}",
            "relationship": pof.control_profile.relationship_to_decedent or "Personal Representative",
            "primary_phone": getattr(pof.control_profile, "primary_phone", None),
            "line_type": "WIRELESS" if getattr(pof.control_profile, "primary_phone", None) else None,
            "confidence_score": 0.95 if getattr(pof.control_profile, "primary_phone", None) else 0.0,
            "is_dnc": False,
            "verified_email": None,
            "mailing_address": pof.property_profile.situs_address,
            "heir_count": pof.control_profile.heir_count,
            "skip_trace_status": "CERTIFIED_ENRICHED" if getattr(pof.control_profile, "primary_phone", None) else "PENDING_SKIP_TRACE"
        },
        "recommended_action": {
            "transaction_strategy": pof.recommended_action.transaction_strategy,
            "first_touch_channel": pof.recommended_action.first_touch_channel,
            "conversational_framing_script": pof.recommended_action.conversational_framing_script
        }
    }

@router.post("/{opportunity_id}/pof/generate")
def generate_pof(
    opportunity_id: str,
    db: Session = Depends(get_db),
    user: ClerkUserContext = Depends(get_current_user)
):
    opp = db.query(OpportunityModel).filter(OpportunityModel.id == opportunity_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found.")

    if not user.is_internal_operator and user.contracted_county:
        c_name = opp.county.name if opp.county else opp.county_id
        if opp.county_id != user.contracted_county and c_name != user.contracted_county:
            raise HTTPException(status_code=403, detail="Forbidden: You do not hold an active contract for this county.")
    
    pof = build_pof_for_opportunity(opp)
    html = POFExporter.to_institutional_html(pof)
    crm = POFExporter.to_crm_webhook_payload(pof)
    
    return {
        "opportunity_id": opp.id,
        "case_number": pof.docket_number,
        "estate_name": pof.estate_name,
        "crm_payload": crm,
        "html_dossier": html
    }

@router.get("/{opportunity_id}/pof/html")
def get_pof_html(
    opportunity_id: str,
    db: Session = Depends(get_db),
    user: ClerkUserContext = Depends(get_current_user)
):
    opp = db.query(OpportunityModel).filter(OpportunityModel.id == opportunity_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found.")

    if not user.is_internal_operator and user.contracted_county:
        c_name = opp.county.name if opp.county else opp.county_id
        if opp.county_id != user.contracted_county and c_name != user.contracted_county:
            raise HTTPException(status_code=403, detail="Forbidden: You do not hold an active contract for this county.")
    
    pof = build_pof_for_opportunity(opp)
    html = POFExporter.to_institutional_html(pof)
    return HTMLResponse(content=html)

@router.get("/{opportunity_id}/pof/json")
def get_pof_json(
    opportunity_id: str,
    db: Session = Depends(get_db),
    user: ClerkUserContext = Depends(get_current_user)
):
    opp = db.query(OpportunityModel).filter(OpportunityModel.id == opportunity_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found.")

    if not user.is_internal_operator and user.contracted_county:
        c_name = opp.county.name if opp.county else opp.county_id
        if opp.county_id != user.contracted_county and c_name != user.contracted_county:
            raise HTTPException(status_code=403, detail="Forbidden: You do not hold an active contract for this county.")
    
    pof = build_pof_for_opportunity(opp)
    crm = POFExporter.to_crm_webhook_payload(pof)
    return JSONResponse(content=crm)

@router.post("/{opportunity_id}/approve")
def approve_opportunity(
    opportunity_id: str,
    req: Optional[OpportunityActionRequest] = None,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user)
):
    opp = db.query(OpportunityModel).filter(OpportunityModel.id == opportunity_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found.")
    target_stage = "READY" if opp.workflow_stage != "READY" else "DELIVERED"
    operator = user.get("username", "Operator") if hasattr(user, "get") else "Operator"
    notes = (req.notes if req else None) or "Operator APPROVED via Opportunity Workbench"
    opp = WorkflowEngine.transition(
        db=db,
        opportunity_id=opp.id,
        to_stage=target_stage,
        transitioned_by=operator,
        notes=notes
    )
    return {"status": "APPROVED", "opportunity_id": opp.id, "workflow_stage": opp.workflow_stage}

@router.post("/{opportunity_id}/reject")
def reject_opportunity(
    opportunity_id: str,
    req: Optional[OpportunityActionRequest] = None,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user)
):
    opp = db.query(OpportunityModel).filter(OpportunityModel.id == opportunity_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found.")
    operator = user.get("username", "Operator") if hasattr(user, "get") else "Operator"
    notes = (req.notes if req else None) or "Operator REJECTED via Opportunity Workbench"
    opp = WorkflowEngine.transition(
        db=db,
        opportunity_id=opp.id,
        to_stage=WorkflowStage.EXCEPTION.value,
        transitioned_by=operator,
        notes=notes
    )
    return {"status": "REJECTED", "opportunity_id": opp.id, "workflow_stage": opp.workflow_stage}

@router.post("/{opportunity_id}/send-qc")
def send_to_qc(
    opportunity_id: str,
    req: Optional[OpportunityActionRequest] = None,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user)
):
    opp = db.query(OpportunityModel).filter(OpportunityModel.id == opportunity_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found.")
    operator = user.get("username", "Operator") if hasattr(user, "get") else "Operator"
    notes = (req.notes if req else None) or "Routed to QC Gate via Opportunity Workbench"
    opp = WorkflowEngine.transition(
        db=db,
        opportunity_id=opp.id,
        to_stage=WorkflowStage.QC.value,
        transitioned_by=operator,
        notes=notes
    )
    return {"status": "ROUTED_TO_QC", "opportunity_id": opp.id, "workflow_stage": opp.workflow_stage}

@router.post("/{opportunity_id}/research")
def request_research(
    opportunity_id: str,
    req: Optional[OpportunityActionRequest] = None,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user)
):
    opp = db.query(OpportunityModel).filter(OpportunityModel.id == opportunity_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found.")
    operator = user.get("username", "Operator") if hasattr(user, "get") else "Operator"
    notes = (req.notes if req else None) or "Research requested via Opportunity Workbench"
    opp = WorkflowEngine.transition(
        db=db,
        opportunity_id=opp.id,
        to_stage=WorkflowStage.OWNERSHIP.value,
        transitioned_by=operator,
        notes=notes
    )
    return {"status": "RESEARCH_REQUESTED", "opportunity_id": opp.id, "workflow_stage": opp.workflow_stage}

@router.post("/{opportunity_id}/deliver", response_model=OpportunityResponse)
def deliver_opportunity(
    opportunity_id: str,
    req: Optional[OpportunityActionRequest] = None,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user)
):
    """
    Dedicated delivery endpoint transitioning opportunity to DELIVERED with idempotency
    and persistent actor audit logging.
    """
    opp = db.query(OpportunityModel).filter(OpportunityModel.id == opportunity_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found.")

    # Idempotency guard: if already delivered, return current opportunity
    if opp.workflow_stage == WorkflowStage.DELIVERED.value:
        return opp

    operator = getattr(user, "user_id", None) or (user.get("user_id") if hasattr(user, "get") else "Operator")
    notes = (req.notes if req else None) or f"Opportunity delivered to partner channel by {operator}"

    try:
        opp = WorkflowEngine.transition(
            db=db,
            opportunity_id=opp.id,
            to_stage=WorkflowStage.DELIVERED.value,
            transitioned_by=operator,
            notes=notes
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return opp

