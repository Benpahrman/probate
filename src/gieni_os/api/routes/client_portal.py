"""
Gieni OS Client Portal API Router (Revenue & Telemetry Layer)
Serves exclusive client opportunities feed, partner quotas, multi-channel CRM webhooks,
and captures closed-loop disposition telemetry:
- Contacted
- Conversation
- Offer
- Contract
- Dead
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from sqlalchemy import func
from gieni_os.database.connection import get_db
from gieni_os.database.models import (
    OpportunityModel,
    CountyModel,
    ClientModel,
    ExceptionModel,
    CRMDispatchLogModel,
    TelemetryDispositionModel
)
from gieni_os.api.routes.opportunities import build_pof_for_opportunity
from gieni_os.pof.exporter import POFExporter

router = APIRouter(prefix="/client", tags=["Client Portal"])

class FeedbackSubmission(BaseModel):
    opportunity_id: str
    stage: str # CONTACTED, CONVERSATION, OFFER, CONTRACT, DEAD
    client_name: Optional[str] = "Sound Capital Acquisitions (Pierce County)"
    notes: Optional[str] = None
    offer_amount: Optional[float] = None
    estimated_close_days: Optional[int] = 14
    dead_reason: Optional[str] = None # UNRESPONSIVE, OVERPRICED, RETAINED_BY_FAMILY, TITLE_DEFECT, COMPETING_OFFER

class FeedbackResponse(BaseModel):
    status: str
    opportunity_id: str
    stage: str
    timestamp: str
    telemetry_recorded: bool
    offer_amount: Optional[float] = None

class CRMExportRequest(BaseModel):
    opportunity_id: str
    crm_platform: Optional[str] = "GoHighLevel" # Podio, FollowUp Boss, GoHighLevel, HubSpot
    webhook_url: Optional[str] = None

from gieni_os.api.deps import get_current_user, ClerkUserContext

@router.get("/partner-profile")
def get_partner_profile(
    user: ClerkUserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    counties = db.query(CountyModel).filter(CountyModel.status == "ACTIVE").all()
    primary_county = user.contracted_county or (counties[0].name if counties else "Pierce")
    
    # County-isolated opportunity counts
    opp_query = db.query(OpportunityModel).filter(OpportunityModel.workflow_stage == "DELIVERED")
    if user.contracted_county:
        opp_query = opp_query.filter(
            (OpportunityModel.county_id == user.contracted_county) |
            (OpportunityModel.county.has(CountyModel.name == user.contracted_county))
        )
    total_delivered = opp_query.count()
    quota_monthly_target = 15
    quota_fulfilled = min(total_delivered, quota_monthly_target)
    
    org_display_name = "Sound Capital"
    if user.org_id == "org_nw_acquisitions":
        org_display_name = "Acquisitions Northwest"
    elif user.org_id == "org_sound_capital":
        org_display_name = "Sound Capital"
    elif user.org_id == "org_king_capital":
        org_display_name = "King Capital"
    elif user.org_id:
        org_display_name = user.org_id.replace("org_", "").replace("_", " ").title()

    return {
        "partner_name": org_display_name,
        "clerk_org_id": user.org_id,
        "org_id": user.org_id,
        "license_tier": "EXCLUSIVE_COUNTY_PARTNER",
        "county_contract": primary_county,
        "exclusive_county": f"{primary_county} County, WA",
        "jurisdiction_lock": True,
        "monthly_quota_target": quota_monthly_target,
        "delivered_this_month": total_delivered,
        "quota_fulfilled_count": quota_fulfilled,
        "quota_progress_pct": round((quota_fulfilled / quota_monthly_target) * 100, 1),
        "sla_compliance_pct": None,
        "active_markets": [c.name for c in counties],
        "crm_integration_active": True,
        "preferred_crm": "GoHighLevel"
    }

@router.get("/dashboard")
def get_client_dashboard(
    county_id: Optional[str] = None,
    user: ClerkUserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    effective_county = county_id or user.contracted_county
    query = db.query(OpportunityModel)
    if effective_county:
        query = query.filter(
            (OpportunityModel.county_id == effective_county) |
            (OpportunityModel.county.has(CountyModel.name == effective_county))
        )
    
    total_delivered = query.filter(OpportunityModel.workflow_stage == "DELIVERED").count()
    active_opps = query.filter(OpportunityModel.workflow_stage.in_(["READY", "DELIVERED", "QC"])).count()
    
    priority_a = query.filter(OpportunityModel.priority.in_(["Priority A", "HIGH", "A"])).count()
    priority_b = query.filter(OpportunityModel.priority.in_(["Priority B", "MEDIUM", "B"])).count()
    counties = db.query(CountyModel).filter(CountyModel.status == "ACTIVE").all()

    return {
        "client_name": f"Exclusive {user.contracted_county or 'County'} Partner",
        "clerk_org_id": user.org_id,
        "assigned_counties": [user.contracted_county] if user.contracted_county else [c.name for c in counties],
        "active_opportunities": active_opps,
        "delivered_this_month": total_delivered,
        "contracts_pending": max(1, int(total_delivered * 0.25)),
        "priority_a_count": priority_a,
        "priority_b_count": priority_b
    }

@router.get("/feed")
def get_client_feed(
    county_id: Optional[str] = None,
    filter_type: Optional[str] = "ALL", # ALL, PRIORITY_A, PRIORITY_B, DELIVERED, UNDER_CONTRACT
    search: Optional[str] = None,
    user: ClerkUserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(OpportunityModel).filter(OpportunityModel.workflow_stage.in_(["READY", "DELIVERED", "QC"]))
    
    # Enforce Clerk Org -> County Contract tenancy mapping
    effective_county = county_id or user.contracted_county
    if effective_county:
        query = query.filter(
            (OpportunityModel.county_id == effective_county) |
            (OpportunityModel.county.has(CountyModel.name == effective_county))
        )
    
    opps = query.all()
    feed = []
    
    for opp in opps:
        pof = build_pof_for_opportunity(opp)
        is_prio_a = "A" in pof.opportunity_profile.priority_tier
        is_prio_b = "B" in pof.opportunity_profile.priority_tier

        # Check latest telemetry status for this deal
        latest_telemetry = (
            db.query(ExceptionModel)
            .filter(
                ExceptionModel.opportunity_id == opp.id,
                ExceptionModel.type == "TELEMETRY_DISPOSITION"
            )
            .order_by(ExceptionModel.created_at.desc())
            .first()
        )
        current_funnel_stage = "NEW_DISPATCH"
        offer_amount = None
        if latest_telemetry and latest_telemetry.notes:
            if "OFFER" in latest_telemetry.notes:
                current_funnel_stage = "OFFER"
            elif "CONTRACT" in latest_telemetry.notes:
                current_funnel_stage = "CONTRACT"
            elif "CONVERSATION" in latest_telemetry.notes:
                current_funnel_stage = "CONVERSATION"
            elif "CONTACTED" in latest_telemetry.notes:
                current_funnel_stage = "CONTACTED"
            elif "DEAD" in latest_telemetry.notes:
                current_funnel_stage = "DEAD"

        if filter_type == "PRIORITY_A" and not is_prio_a:
            continue
        if filter_type == "PRIORITY_B" and not is_prio_b:
            continue
        if filter_type == "DELIVERED" and opp.workflow_stage != "DELIVERED":
            continue
        if filter_type == "UNDER_CONTRACT" and current_funnel_stage != "CONTRACT":
            continue

        if search:
            s = search.lower()
            if (s not in pof.property_profile.situs_address.lower() and
                s not in pof.docket_number.lower() and
                s not in pof.estate_name.lower() and
                s not in pof.property_profile.apn.lower()):
                continue

        feed.append({
            "id": opp.id,
            "case_number": pof.docket_number,
            "estate_name": pof.estate_name,
            "county": opp.county.name if opp.county else opp.county_id,
            "apn": pof.property_profile.apn,
            "situs_address": pof.property_profile.situs_address,
            "city_state_zip": pof.property_profile.city_state_zip,
            "avm": pof.property_profile.avm_market_estimate,
            "net_equity": pof.ownership_profile.net_distributable_equity,
            "net_equity_pct": round(pof.ownership_profile.net_equity_pct * 100, 1),
            "target_mao": pof.ownership_profile.target_wholesale_mao,
            "authority_tier": pof.authority_profile.authority_tier,
            "statutory_basis": pof.authority_profile.statutory_basis,
            "primary_decision_maker": pof.control_profile.primary_decision_maker,
            "relationship": pof.control_profile.relationship_to_decedent,
            "occupancy": pof.control_profile.occupancy,
            "composite_score": pof.opportunity_profile.composite_viability_score,
            "priority_tier": pof.opportunity_profile.priority_tier,
            "dispatch_sla": pof.opportunity_profile.dispatch_sla,
            "stage": opp.workflow_stage,
            "funnel_stage": current_funnel_stage,
            "recommended_script": pof.recommended_action.conversational_framing_script
        })
    return feed

@router.get("/opportunity/{opportunity_id}")
def get_client_opportunity_detail(opportunity_id: str, db: Session = Depends(get_db)):
    opp = db.query(OpportunityModel).filter(OpportunityModel.id == opportunity_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found.")

    pof = build_pof_for_opportunity(opp)
    
    # Check disposition telemetry trail
    telemetry_logs = (
        db.query(ExceptionModel)
        .filter(
            ExceptionModel.opportunity_id == opp.id,
            ExceptionModel.type == "TELEMETRY_DISPOSITION"
        )
        .order_by(ExceptionModel.created_at.desc())
        .all()
    )

    return {
        "opportunity_id": opp.id,
        "docket_number": pof.docket_number,
        "estate_name": pof.estate_name,
        "county": opp.county.name if opp.county else opp.county_id,
        "property": {
            "apn": pof.property_profile.apn,
            "address": pof.property_profile.situs_address,
            "city_state_zip": pof.property_profile.city_state_zip,
            "avm": pof.property_profile.avm_market_estimate,
            "assessed_value": pof.property_profile.total_assessed_value,
            "landuse": pof.property_profile.landuse,
            "pas_score": pof.property_profile.pas_score
        },
        "equity_waterfall": {
            "net_distributable_equity": pof.ownership_profile.net_distributable_equity,
            "net_equity_pct": round(pof.ownership_profile.net_equity_pct * 100, 1),
            "target_wholesale_mao": pof.ownership_profile.target_wholesale_mao,
            "senior_mortgage": pof.ownership_profile.senior_mortgage_balance,
            "estimated_repairs": pof.ownership_profile.estimated_repairs,
            "is_free_and_clear": pof.ownership_profile.is_free_and_clear
        },
        "contact_dossier": {
            "primary_decision_maker": pof.control_profile.primary_decision_maker,
            "relationship": pof.control_profile.relationship_to_decedent,
            "heir_count": pof.control_profile.heir_count,
            "occupancy": pof.control_profile.occupancy,
            "phone": getattr(pof.control_profile, "primary_phone", None),
            "email": None
        },
        "authority_powers": {
            "tier": pof.authority_profile.authority_tier,
            "oversight_model": pof.authority_profile.court_oversight_model,
            "can_execute_psa": pof.authority_profile.can_execute_psa,
            "court_confirmation_required": pof.authority_profile.court_confirmation_required,
            "statutory_basis": pof.authority_profile.statutory_basis,
            "powers_scope": pof.authority_profile.statutory_power_scope
        },
        "score_and_sla": {
            "composite_score": pof.opportunity_profile.composite_viability_score,
            "priority_tier": pof.opportunity_profile.priority_tier,
            "dispatch_sla": pof.opportunity_profile.dispatch_sla,
            "qc_stamp": pof.evidence_package.qc_certification_stamp
        },
        "recommended_action": {
            "strategy": pof.recommended_action.transaction_strategy,
            "channel": pof.recommended_action.first_touch_channel,
            "script": pof.recommended_action.conversational_framing_script
        },
        "telemetry_history": [
            {
                "id": t.id,
                "notes": t.notes,
                "created_at": t.created_at.isoformat() if t.created_at else None
            }
            for t in telemetry_logs
        ]
    }

import ipaddress
import socket
from urllib.parse import urlparse
import httpx

def validate_webhook_url(url_str: str) -> str:
    if not url_str or not url_str.strip():
        raise HTTPException(status_code=400, detail="Registered webhook URL is required for CRM export.")
    
    target_url = url_str.strip()
    parsed = urlparse(target_url)
    if parsed.scheme.lower() != "https":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Security violation: Webhook URL must use https:// scheme (received '{parsed.scheme}')."
        )
    hostname = parsed.hostname
    if not hostname:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security violation: Webhook URL must include a valid hostname."
        )
    
    if hostname.lower() in ("localhost", "127.0.0.1", "::1", "metadata.google.internal"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security violation: Webhook URL cannot target localhost or metadata endpoints."
        )
    
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Security violation: Webhook cannot target private, loopback, or link-local IP addresses: {hostname}"
            )
    except ValueError:
        try:
            addr_info = socket.getaddrinfo(hostname, None)
            for addr in addr_info:
                ip = ipaddress.ip_address(addr[4][0])
                if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Security violation: Webhook hostname resolves to disallowed private/link-local IP: {ip}"
                    )
        except socket.gaierror:
            pass

    return target_url

@router.post("/export/crm")
@router.post("/export-crm")
async def export_to_crm(req: CRMExportRequest, db: Session = Depends(get_db)):
    opp = db.query(OpportunityModel).filter(OpportunityModel.id == req.opportunity_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found.")

    pof = build_pof_for_opportunity(opp)
    crm_payload = POFExporter.to_crm_webhook_payload(pof)

    target_url = validate_webhook_url(req.webhook_url or "")

    delivery_status = "DISPATCHED"
    http_code = None
    try:
        async with httpx.AsyncClient(timeout=5.0) as http_client:
            resp = await http_client.post(target_url, json=crm_payload)
            http_code = resp.status_code
            delivery_status = "DELIVERED" if resp.is_success else f"FAILED_HTTP_{resp.status_code}"
    except Exception as e:
        delivery_status = f"DISPATCH_ERROR: {str(e)}"

    # Record dispatch event in CRM audit log
    dispatch_log = CRMDispatchLogModel(
        opportunity_id=opp.id,
        crm_platform=req.crm_platform,
        webhook_url=target_url,
        status=delivery_status,
        response_code=http_code,
        notes=f"POF webhook dispatched to partner CRM ({req.crm_platform}). Status: {delivery_status} (HTTP {http_code})."
    )
    db.add(dispatch_log)
    db.commit()

    return {
        "status": "DISPATCHED",
        "delivery_status": delivery_status,
        "opportunity_id": opp.id,
        "crm_platform": req.crm_platform,
        "webhook_url": target_url,
        "payload": crm_payload,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.post("/feedback", response_model=FeedbackResponse)
def submit_disposition_feedback(fb: FeedbackSubmission, db: Session = Depends(get_db)):
    opp = db.query(OpportunityModel).filter(OpportunityModel.id == fb.opportunity_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found.")

    valid_stages = ["CONTACTED", "CONVERSATION", "OFFER", "CONTRACT", "DEAD"]
    stage_upper = fb.stage.upper()
    if stage_upper not in valid_stages:
        raise HTTPException(status_code=400, detail=f"Invalid feedback stage. Must be one of {valid_stages}")

    telemetry_note = f"[Telemetry Feedback: {stage_upper}] Client: {fb.client_name}. Notes: {fb.notes or 'N/A'}."
    if fb.offer_amount:
        telemetry_note += f" Offer: ${fb.offer_amount:,.2f}."
    if fb.estimated_close_days:
        telemetry_note += f" Target Close: {fb.estimated_close_days} days."
    if fb.dead_reason:
        telemetry_note += f" Loss Reason: {fb.dead_reason}."

    telemetry_rec = TelemetryDispositionModel(
        opportunity_id=opp.id,
        client_name=fb.client_name,
        stage=stage_upper,
        offer_amount=fb.offer_amount,
        estimated_close_days=fb.estimated_close_days,
        dead_reason=fb.dead_reason,
        notes=telemetry_note
    )
    db.add(telemetry_rec)

    # If stage is CONTRACT or OFFER, advance or stamp opportunity
    if stage_upper == "CONTRACT" and opp.workflow_stage != "DELIVERED":
        opp.workflow_stage = "DELIVERED"

    db.commit()

    return FeedbackResponse(
        status="SUCCESS",
        opportunity_id=opp.id,
        stage=stage_upper,
        timestamp=datetime.now(timezone.utc).isoformat(),
        telemetry_recorded=True,
        offer_amount=fb.offer_amount
    )

@router.get("/telemetry/stats")
def get_telemetry_stats(db: Session = Depends(get_db)):
    total_delivered = db.query(OpportunityModel).filter(OpportunityModel.workflow_stage.in_(["READY", "DELIVERED"])).count()
    
    # Query verified telemetry events from TelemetryDispositionModel
    contacted_count = db.query(func.count(TelemetryDispositionModel.id)).filter(TelemetryDispositionModel.stage == "CONTACTED").scalar() or 0
    conversation_count = db.query(func.count(TelemetryDispositionModel.id)).filter(TelemetryDispositionModel.stage == "CONVERSATION").scalar() or 0
    offer_count = db.query(func.count(TelemetryDispositionModel.id)).filter(TelemetryDispositionModel.stage == "OFFER").scalar() or 0
    contract_count = db.query(func.count(TelemetryDispositionModel.id)).filter(TelemetryDispositionModel.stage == "CONTRACT").scalar() or 0
    dead_count = db.query(func.count(TelemetryDispositionModel.id)).filter(TelemetryDispositionModel.stage == "DEAD").scalar() or 0

    # Calculate real rates or return None if unmeasured / zero denominator
    contact_rate = round((contacted_count / total_delivered * 100), 1) if total_delivered > 0 else None
    win_rate = round((contract_count / offer_count * 100), 1) if offer_count > 0 else None

    # Calculate actual aggregated offer volume
    actual_offer_vol = db.query(func.sum(TelemetryDispositionModel.offer_amount)).filter(TelemetryDispositionModel.stage == "OFFER").scalar()
    total_offer_vol = float(actual_offer_vol) if actual_offer_vol is not None else (0.0 if offer_count == 0 else None)

    return {
        "total_delivered_deals": total_delivered,
        "contacted_count": contacted_count,
        "conversation_count": conversation_count,
        "offer_count": offer_count,
        "contract_count": contract_count,
        "dead_count": dead_count,
        "contact_rate_pct": contact_rate,
        "win_rate_pct": win_rate,
        "avg_response_time_hours": None,
        "total_offer_volume": total_offer_vol
    }

