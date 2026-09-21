"""
Gieni OS - Sprint 3 Intelligence Pipeline Demonstration
Demonstrates:
Control Graph (CIE), 5 Control Archetypes, Attorney Bypass Protocol & Decision-Maker Contact Enrichment

Workflow Chain:
IntakeWorkflow -> PropertyWorkflow -> OwnershipWorkflow -> AuthorityWorkflow -> ControlWorkflow -> ContactWorkflow
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
    CountyModel, OpportunityModel, WorkflowAuditLogModel
)
from src.gieni_os.events.bus import EventBus
from src.gieni_os.workflows.intake_workflow import IntakeWorkflow
from src.gieni_os.workflows.property_workflow import PropertyWorkflow
from src.gieni_os.workflows.ownership_workflow import OwnershipWorkflow
from src.gieni_os.workflows.authority_workflow import AuthorityWorkflow
from src.gieni_os.workflows.control_workflow import ControlWorkflow
from src.gieni_os.workflows.contact_workflow import ContactWorkflow

def banner(title: str):
    print("\n" + "=" * 80)
    print(f" {title.upper()}")
    print("=" * 80)

def run_sprint3_demo():
    banner("1. INITIALIZING SPRINT 3 RUNTIME & EVENT BUS")
    init_db()
    db = SessionLocal()
    bus = EventBus()

    county = db.query(CountyModel).filter_by(id="cty_king").first()
    if not county:
        county = CountyModel(id="cty_king", name="King", state="WA", tier="TIER_1")
        db.add(county)
        db.commit()
    print("Database ready. EventBus online. Monitoring King County.")

    # Instantiate Workflows
    intake_wf = IntakeWorkflow(event_bus=bus)
    prop_wf = PropertyWorkflow(event_bus=bus)
    own_wf = OwnershipWorkflow(event_bus=bus)
    auth_wf = AuthorityWorkflow(event_bus=bus)
    control_wf = ControlWorkflow(event_bus=bus)
    contact_wf = ContactWorkflow(event_bus=bus)

    # Subscribe audit recorder
    chain_events = []
    def log_event(name, p):
        chain_events.append(name)

    for ev in [
        "PROPERTY_DISCOVERY_REQUIRED", "OWNERSHIP_ANALYSIS_REQUIRED",
        "AUTHORITY_ANALYSIS_REQUIRED", "CONTACT_ENRICHMENT_REQUIRED", "SCORING_REQUIRED"
    ]:
        bus.subscribe(ev, lambda p, ev=ev: log_event(ev, p))

    banner("2. EXECUTING INTAKE -> PROPERTY -> OWNERSHIP -> AUTHORITY")
    filing = {
        "case_number": "24-4-01888-4 SEA",
        "county_id": "cty_king",
        "decedent_name": "Walter White",
        "petitioner_name": "Skyler White",
        "filing_date": date(2026, 9, 14),
        "raw_address": "308 Negra Arroyo Lane, Seattle, WA 98101",
        "docket_entries": [
            "PETITION FOR PROBATE OF WILL",
            "ORDER APPOINTING PR WITH RCW 11.68 NONINTERVENTION POWERS",
            "LETTERS TESTAMENTARY ISSUED TO SKYLER WHITE"
        ],
        "attorney_name": "Hamlin, Hamlin & McGill PS",
        "heir_names": ["Skyler White", "Walter White Jr."],
        "resident_names": ["Skyler White"]
    }

    # Step 1: Intake
    intake_res = intake_wf.run(db, filing)
    opp_id = intake_res["opportunity_id"]

    # Step 2: Property
    prop_res = prop_wf.run(db, intake_res["context"])

    # Step 3: Ownership
    own_res = own_wf.run(db, prop_res["context"])

    # Step 4: Authority
    auth_res = auth_wf.run(db, own_res["context"])
    print(f"Opportunity {opp_id} advanced through Authority: RESOLVED (Tier 1 Certified).")

    banner("3. STEP 5: SOCIAL DYNAMICS & CONTROL GRAPH (CIE)")
    control_res = control_wf.run(db, auth_res["context"])
    print(f" -> Control Workflow Executed:")
    print(f"    - Classified Archetype:  {control_res['control_archetype']}")
    print(f"    - Occupancy Status:      {control_res['occupancy_status']}")
    print(f"    - Deal Friction Rating:  {control_res['friction_rating']}/10")
    print(f"    - Primary Decision Maker:{control_res['context']['primary_decision_maker']}")
    print(f"    - Knowledge Graph:       {control_res['context']['graph_node_count']} Nodes, {control_res['context']['graph_edge_count']} Edges mapped")
    print(f"\n[WASHINGTON ATTORNEY GATEKEEPER BYPASS PROTOCOL]")
    print(f"  {control_res['context']['attorney_bypass_strategy']}")

    banner("4. STEP 6: DECISION-MAKER CONTACT ENRICHMENT (Contact Workflow)")
    contact_res = contact_wf.run(db, control_res["context"])
    print(f" -> Contact Workflow Executed:")
    print(f"    - Target Name:           {contact_res['context']['decision_maker_name']}")
    print(f"    - Primary Phone:         {contact_res['context']['decision_maker_phone']}")
    print(f"    - Verified Email:        {contact_res['context']['decision_maker_email']}")
    print(f"    - Skip-Trace Confidence: {contact_res['skip_trace_confidence']:.1f}%")
    print(f"    - Recommended Channel:   {contact_res['context']['outreach_channel']}")
    print(f"    - Staged Opportunity:    ENRICHMENT")
    print(f"\n[TAILORED DIRECT-TO-FIDUCIARY OUTREACH SCRIPT]")
    print(f"  \"{contact_res['context']['outreach_script']}\"")

    banner("5. OPPORTUNITY LIFECYCLE AUDIT TRAIL")
    opp = db.query(OpportunityModel).filter_by(id=opp_id).first()
    print(f"Current Opportunity Stage: {opp.workflow_stage}")
    print(f"Authority Status:          {opp.authority_status}")

    audit_logs = db.query(WorkflowAuditLogModel).filter_by(opportunity_id=opp_id).all()
    for log in audit_logs:
        print(f"  [{log.timestamp.strftime('%H:%M:%S')}] {log.from_stage:<14} -> {log.to_stage:<14} | Actor: {log.transitioned_by:<24} | Notes: {log.notes}")

    banner("6. CANONICAL EVENT BUS PROPAGATION")
    for i, ev_name in enumerate(chain_events, 1):
        print(f"  Event {i}: {ev_name}")

    banner("SPRINT 3 DEMONSTRATION COMPLETE: READY FOR SCORING ENGINE (SPRINT 4)")
    db.close()

if __name__ == "__main__":
    run_sprint3_demo()
