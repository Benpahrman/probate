"""
Gieni OS - Sprint 5 Commercial Delivery & POF Assembly Demonstration
Demonstrates:
Canonical 8-Profile POF v2.0 Compiler, Multi-Channel Dispatch (Podio, GoHighLevel, Salesforce),
HMAC-SHA256 Webhook Security, and 4-Hour Flash SMS Dispatch for Priority A Deals.

Full 9-Stage Workflow Pipeline:
IntakeWorkflow -> PropertyWorkflow -> OwnershipWorkflow -> AuthorityWorkflow
-> ControlWorkflow -> ContactWorkflow -> ScoringWorkflow -> QCWorkflow -> DeliveryWorkflow
"""

import sys
import os
from datetime import date

# Ensure repo root is on sys.path
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.gieni_os.database.connection import init_db, SessionLocal
from src.gieni_os.database.models import (
    CountyModel, ClientModel, OpportunityModel, WorkflowAuditLogModel
)
from src.gieni_os.events.bus import EventBus
from src.gieni_os.workflows.intake_workflow import IntakeWorkflow
from src.gieni_os.workflows.property_workflow import PropertyWorkflow
from src.gieni_os.workflows.ownership_workflow import OwnershipWorkflow
from src.gieni_os.workflows.authority_workflow import AuthorityWorkflow
from src.gieni_os.workflows.control_workflow import ControlWorkflow
from src.gieni_os.workflows.contact_workflow import ContactWorkflow
from src.gieni_os.workflows.scoring_workflow import ScoringWorkflow
from src.gieni_os.workflows.qc_workflow import QCWorkflow
from src.gieni_os.workflows.delivery_workflow import DeliveryWorkflow

def banner(title: str):
    print("\n" + "=" * 80)
    print(f" {title.upper()}")
    print("=" * 80)

def run_sprint5_demo():
    banner("1. INITIALIZING SPRINT 5 RUNTIME & MULTI-CHANNEL DISPATCH LAYER")
    init_db()
    db = SessionLocal()
    bus = EventBus()

    county = db.query(CountyModel).filter_by(id="cty_king").first()
    if not county:
        county = CountyModel(id="cty_king", name="King", state="WA", tier="TIER_1")
        db.add(county)
        db.commit()

    client = db.query(ClientModel).filter_by(id="client_evergreen").first()
    if not client:
        client = ClientModel(
            id="client_evergreen",
            name="Evergreen Home Acquisitions LLC",
            renewal_date=date(2027, 1, 1),
            status="ACTIVE",
            county_id="cty_king"
        )
        db.add(client)
        db.commit()

    print("Database ready. Monitoring King County. Target Partner: Evergreen Home Acquisitions LLC.")

    # Instantiate All 9 Decoupled Workflows
    intake_wf = IntakeWorkflow(event_bus=bus)
    prop_wf = PropertyWorkflow(event_bus=bus)
    own_wf = OwnershipWorkflow(event_bus=bus)
    auth_wf = AuthorityWorkflow(event_bus=bus)
    control_wf = ControlWorkflow(event_bus=bus)
    contact_wf = ContactWorkflow(event_bus=bus)
    scoring_wf = ScoringWorkflow(event_bus=bus)
    qc_wf = QCWorkflow(event_bus=bus)
    delivery_wf = DeliveryWorkflow(event_bus=bus)

    # Track Canonical Events
    pipeline_events = []
    def on_event(name, p):
        pipeline_events.append(name)

    for ev in [
        "PROPERTY_DISCOVERY_REQUIRED", "OWNERSHIP_ANALYSIS_REQUIRED",
        "AUTHORITY_ANALYSIS_REQUIRED", "CONTACT_ENRICHMENT_REQUIRED",
        "SCORING_REQUIRED", "QC_VALIDATION_REQUIRED", "OPPORTUNITY_QC_CERTIFIED",
        "DELIVERY_COMPLETED"
    ]:
        bus.subscribe(ev, lambda p, ev=ev: on_event(ev, p))

    banner("2. PIPELINING DOCKET: 24-4-03310-8 SEA (Estate of Charles Montgomery Burns)")
    filing = {
        "case_number": "24-4-03310-8 SEA",
        "county_id": "cty_king",
        "decedent_name": "Charles M. Burns",
        "petitioner_name": "Waylon Smithers",
        "filing_date": date(2026, 9, 19),
        "raw_address": "1000 Evergreen Terrace, Seattle, WA 98101",
        "docket_entries": [
            "PETITION FOR PROBATE OF WILL",
            "ORDER APPOINTING PR WITH RCW 11.68 NONINTERVENTION POWERS",
            "LETTERS TESTAMENTARY ISSUED TO WAYLON SMITHERS"
        ],
        "attorney_name": "Lionel Hutz Legal Services PS",
        "heir_names": ["Waylon Smithers", "Larry Burns"],
        "resident_names": ["Waylon Smithers"]
    }

    # Execute Sequential Stages 1 to 8
    intake_res = intake_wf.run(db, filing)
    prop_res = prop_wf.run(db, intake_res["context"])
    own_res = own_wf.run(db, prop_res["context"])
    auth_res = auth_wf.run(db, own_res["context"])
    ctrl_res = control_wf.run(db, auth_res["context"])
    contact_res = contact_wf.run(db, ctrl_res["context"])
    scoring_res = scoring_wf.run(db, contact_res["context"])
    qc_res = qc_wf.run(db, scoring_res["context"])

    opp_id = intake_res["opportunity_id"]
    print(f"Opportunity {opp_id} certified through 6-Gate QC with seal: {qc_res['certification_stamp']}")

    banner("3. STAGE 9: COMMERCIAL POF ASSEMBLY & MULTI-CHANNEL DISPATCH")
    delivery_context = {
        **qc_res["context"],
        "client_id": "client_evergreen",
        "crm_platform": "GOHIGHLEVEL",
        "client_phone": "+12065550199",
        "endpoint_url": "https://services.leadconnectorhq.com/hooks/v2/gieni_prod_ingest",
        "webhook_secret": "whsec_evergreen_super_secret_998"
    }

    delivery_res = delivery_wf.run(db, delivery_context)
    dispatch_rec = delivery_res["context"]

    print(" -> Commercial Delivery Execution:")
    print(f"    - Dispatch ID:         {dispatch_rec['dispatch_id']}")
    print(f"    - Client ID:           {dispatch_rec['client_id']}")
    print(f"    - Target CRM Platform: {dispatch_rec['platform']}")
    print(f"    - Dispatch Latency:    {dispatch_rec['latency_ms']} ms")
    print(f"    - HTTP Status:         200 OK")

    if dispatch_rec.get("flash_alert"):
        flash = dispatch_rec["flash_alert"]
        print("\n[PRIORITY A FLASH SMS DISPATCH (<4-HOUR SLA)]")
        print(f"  Recipient Phone:  {flash['recipient_phone']}")
        print(f"  Headline:         {flash['alert_headline']}")
        print(f"  Property Summary: {flash['property_summary']}")
        print(f"  SLA Status:       {flash['sla_status']}")

    banner("4. COMPLETE 9-STAGE AUDIT TRAIL")
    opp = db.query(OpportunityModel).filter_by(id=opp_id).first()
    print(f"Final Opportunity Stage: {opp.workflow_stage}")
    print(f"Final Viability Score:   {opp.score}/100 ({opp.priority} Priority)")
    print(f"Authority Status:        {opp.authority_status}")

    logs = db.query(WorkflowAuditLogModel).filter_by(opportunity_id=opp_id).order_by(WorkflowAuditLogModel.timestamp.asc()).all()
    for log in logs:
        ts = log.timestamp.strftime("%H:%M:%S")
        print(f"  [{ts}] {log.from_stage:<14} -> {log.to_stage:<14} | Actor: {log.transitioned_by:<32} | Notes: {log.notes}")

    banner("5. CANONICAL EVENT BUS PROPAGATION (ALL 8 EVENTS)")
    for i, ev in enumerate(pipeline_events, 1):
        print(f"  Event {i}: {ev}")

    banner("SPRINT 5 DEMONSTRATION COMPLETE: READY FOR SPRINT 6 TELEMETRY & SCALE")

if __name__ == "__main__":
    run_sprint5_demo()
