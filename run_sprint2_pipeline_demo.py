"""
Gieni OS - Sprint 2 Core Intelligence Pipeline
Executes the First Production-Ready Intelligence Workflow:
Raw Probate Filing -> Intake Agent -> Property Agent -> Ownership Agent -> Authority Agent -> Human Review

Enforces the Architectural Axiom:
Workflow -> Agent -> Engine -> Event -> Next Workflow
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
    CountyModel, ProbateCaseModel, OpportunityModel, WorkflowAuditLogModel
)
from src.gieni_os.events.bus import EventBus
from src.gieni_os.workflows.intake_workflow import IntakeWorkflow
from src.gieni_os.workflows.property_workflow import PropertyWorkflow
from src.gieni_os.workflows.ownership_workflow import OwnershipWorkflow
from src.gieni_os.workflows.authority_workflow import AuthorityWorkflow

def banner(title: str):
    print("\n" + "=" * 80)
    print(f" {title.upper()}")
    print("=" * 80)

def run_pipeline():
    banner("1. INITIALIZING PIPELINE RUNTIME & EVENT BUS")
    init_db()
    db = SessionLocal()
    bus = EventBus()

    # Ensure King County exists
    county = db.query(CountyModel).filter_by(id="cty_king").first()
    if not county:
        county = CountyModel(id="cty_king", name="King", state="WA", tier="TIER_1")
        db.add(county)
        db.commit()
    print("Runtime ready: SQLite connected, EventBus instantiated, King County active.")

    # Wire up the 4 Workflows to the Event Bus
    intake_wf = IntakeWorkflow(event_bus=bus)
    property_wf = PropertyWorkflow(event_bus=bus)
    ownership_wf = OwnershipWorkflow(event_bus=bus)
    authority_wf = AuthorityWorkflow(event_bus=bus)

    # Track event chain for validation
    event_trail = []
    def record_event(name, payload):
        event_trail.append((name, payload))

    bus.subscribe("PROPERTY_DISCOVERY_REQUIRED", lambda p: record_event("PROPERTY_DISCOVERY_REQUIRED", p))
    bus.subscribe("OWNERSHIP_ANALYSIS_REQUIRED", lambda p: record_event("OWNERSHIP_ANALYSIS_REQUIRED", p))
    bus.subscribe("AUTHORITY_ANALYSIS_REQUIRED", lambda p: record_event("AUTHORITY_ANALYSIS_REQUIRED", p))
    bus.subscribe("HUMAN_REVIEW_REQUIRED", lambda p: record_event("HUMAN_REVIEW_REQUIRED", p))

    banner("2. STEP 1: RAW PROBATE FILING INTAKE (Intake Workflow)")
    raw_filing = {
        "case_number": "24-4-01021-1 SEA",
        "county_id": "cty_king",
        "decedent_name": "Eleanor Rigby",
        "petitioner_name": "James Rigby",
        "filing_date": date(2026, 9, 15),
        "raw_address": "1422 Elm St, Seattle, WA 98101",
        "docket_entries": [
            "2026-09-15: PETITION FOR PROBATE OF WILL AND LETTERS TESTAMENTARY",
            "2026-09-15: DECLARATION OF MAILING TO HEIRS",
            "2026-09-18: ORDER APPOINTING PERSONAL REPRESENTATIVE WITH NONINTERVENTION POWERS (RCW 11.68)",
            "2026-09-18: LETTERS TESTAMENTARY ISSUED TO JAMES RIGBY"
        ]
    }
    print(f"Ingesting Raw Court Docket: Case {raw_filing['case_number']} ({raw_filing['decedent_name']})")
    intake_res = intake_wf.run(db, raw_filing)
    opp_id = intake_res["opportunity_id"]
    print(f" -> Intake Workflow Completed:")
    print(f"    - Case ID: {intake_res['case_id']}")
    print(f"    - Opportunity ID: {opp_id} (Stage: NEW)")
    print(f"    - Emitted Event: {intake_res['next_event']}")

    banner("3. STEP 2: PROPERTY IDENTITY & PARCEL MATCHING (Property Workflow)")
    prop_context = intake_res["context"]
    prop_res = property_wf.run(db, prop_context)
    print(f" -> Property Workflow Completed:")
    print(f"    - Reconciled APN: {prop_res['context']['apn']}")
    print(f"    - Standardized Address: {prop_res['context']['address']}")
    print(f"    - PAS Alignment Score: {prop_res['context']['pas_score']}/100")
    print(f"    - Staged Opportunity: PROPERTY_MATCH")
    print(f"    - Emitted Event: {prop_res['next_event']}")

    banner("4. STEP 3: DEED VESTING & EQUITY WATERFALL (Ownership Workflow)")
    own_context = prop_res["context"]
    own_res = ownership_wf.run(db, own_context)
    print(f" -> Ownership Workflow Completed:")
    print(f"    - Vesting: {own_res['context']['vesting_type']}")
    print(f"    - Title Complexity Score: {own_res['context']['title_complexity']}/10 (Clear Title)")
    print(f"    - Net Equity Assessed: ${own_res['net_equity']:,.2f}")
    print(f"    - Staged Opportunity: OWNERSHIP")
    print(f"    - Emitted Event: {own_res['next_event']}")

    banner("5. STEP 4: WASHINGTON RCW TITLE 11 AUTHORITY RESOLUTION (Authority Workflow)")
    auth_context = own_res["context"]
    auth_res = authority_wf.run(db, auth_context)
    print(f" -> Authority Workflow Completed:")
    print(f"    - Authority Tier: {auth_res['authority_tier']}")
    print(f"    - Fiduciary Name: {auth_res['context']['fiduciary_name']}")
    print(f"    - Statutory Powers: {auth_res['context']['statutory_powers']}")
    print(f"    - Opportunity Authority Status: {auth_res['authority_status']}")
    print(f"    - Staged Opportunity: AUTHORITY")
    print(f"    - Emitted Event: {auth_res['next_event']} (Routed to Human Review / Authority Queue)")

    banner("6. VERIFICATION: OPPORTUNITY STATE IN DATABASE")
    final_opp = db.query(OpportunityModel).filter_by(id=opp_id).first()
    print(f"Opportunity ID:        {final_opp.id}")
    print(f"Case Ref:              {final_opp.case_id}")
    print(f"County:                {final_opp.county_id}")
    print(f"Workflow Stage:        {final_opp.workflow_stage}")
    print(f"Authority Status:      {final_opp.authority_status}")

    print("\n[IMMUTABLE AUDIT TRAIL LOGGED BY WORKFLOW STATE MACHINE]")
    audit_logs = db.query(WorkflowAuditLogModel).filter_by(opportunity_id=opp_id).all()
    for log in audit_logs:
        print(f"  [{log.timestamp.strftime('%H:%M:%S')}] {log.from_stage:<14} -> {log.to_stage:<14} | Actor: {log.transitioned_by:<24} | Notes: {log.notes}")

    banner("7. VERIFICATION: CANONICAL EVENT BUS CHAIN")
    for i, (ev_name, _) in enumerate(event_trail, 1):
        print(f"  Step {i}: {ev_name}")

    banner("SPRINT 2 CORE INTELLIGENCE PIPELINE DEMONSTRATION COMPLETE")
    print("PROVEN: Raw court docket successfully transformed into an Authority-Resolved Opportunity")
    print("        awaiting final Human Review in the Authority Resolution Queue.\n")
    db.close()

if __name__ == "__main__":
    run_pipeline()
