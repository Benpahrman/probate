"""
Gieni OS - Sprint 4 Scoring & 6-Gate QC Demonstration
Demonstrates:
Opportunity Scoring Engine (OSE), Deal Friction Score (DFS),
Automated 6-Gate Quality Control Pass (QCA), Cryptographic Notarization,
and Progression into READY stage for Sprint 5 Delivery.

Workflow Chain (8 sequential stages):
IntakeWorkflow -> PropertyWorkflow -> OwnershipWorkflow -> AuthorityWorkflow
-> ControlWorkflow -> ContactWorkflow -> ScoringWorkflow -> QCWorkflow
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
from src.gieni_os.workflows.scoring_workflow import ScoringWorkflow
from src.gieni_os.workflows.qc_workflow import QCWorkflow

def banner(title: str):
    print("\n" + "=" * 80)
    print(f" {title.upper()}")
    print("=" * 80)

def run_sprint4_demo():
    banner("1. INITIALIZING SPRINT 4 RUNTIME & EVENT BUS")
    init_db()
    db = SessionLocal()
    bus = EventBus()

    county = db.query(CountyModel).filter_by(id="cty_king").first()
    if not county:
        county = CountyModel(id="cty_king", name="King", state="WA", tier="TIER_1")
        db.add(county)
        db.commit()
    print("Database ready. EventBus online. Monitoring King County.")

    # Instantiate All 8 Workflows
    intake_wf = IntakeWorkflow(event_bus=bus)
    prop_wf = PropertyWorkflow(event_bus=bus)
    own_wf = OwnershipWorkflow(event_bus=bus)
    auth_wf = AuthorityWorkflow(event_bus=bus)
    control_wf = ControlWorkflow(event_bus=bus)
    contact_wf = ContactWorkflow(event_bus=bus)
    scoring_wf = ScoringWorkflow(event_bus=bus)
    qc_wf = QCWorkflow(event_bus=bus)

    # Track Canonical Events
    emitted_events = []
    def record_event(name, p):
        emitted_events.append(name)

    for ev in [
        "PROPERTY_DISCOVERY_REQUIRED", "OWNERSHIP_ANALYSIS_REQUIRED",
        "AUTHORITY_ANALYSIS_REQUIRED", "CONTACT_ENRICHMENT_REQUIRED",
        "SCORING_REQUIRED", "QC_VALIDATION_REQUIRED", "OPPORTUNITY_QC_CERTIFIED"
    ]:
        bus.subscribe(ev, lambda p, ev=ev: record_event(ev, p))

    banner("2. EXECUTING INTAKE -> PROPERTY -> OWNERSHIP -> AUTHORITY -> CONTROL -> CONTACT")
    filing = {
        "case_number": "24-4-02490-7 SEA",
        "county_id": "cty_king",
        "decedent_name": "Logan Roy",
        "petitioner_name": "Shiv Roy",
        "filing_date": date(2026, 9, 18),
        "raw_address": "1000 2nd Ave, Seattle, WA 98104",
        "docket_entries": [
            "PETITION FOR PROBATE OF WILL",
            "ORDER APPOINTING PR WITH RCW 11.68 NONINTERVENTION POWERS",
            "LETTERS TESTAMENTARY ISSUED TO SHIV ROY"
        ],
        "attorney_name": "Gerri Kellman, Esq.",
        "heir_names": ["Shiv Roy", "Kendall Roy", "Roman Roy", "Connor Roy"],
        "resident_names": ["Shiv Roy"]
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

    # Step 5: Control Graph
    ctrl_res = control_wf.run(db, auth_res["context"])

    # Step 6: Contact Enrichment
    contact_res = contact_wf.run(db, ctrl_res["context"])

    print(f"Opportunity {opp_id} advanced through Contact Enrichment (Stage: ENRICHMENT).")

    banner("3. STEP 7: OPPORTUNITY SCORING ENGINE (OSE)")
    # Step 7: Scoring
    scoring_res = scoring_wf.run(db, contact_res["context"])
    opp_score = scoring_res["context"]["opportunity_score"]

    print(" -> Opportunity Scoring Engine Output:")
    print(f"    - Equity Score (35%):       {opp_score.equity_score}/100")
    print(f"    - Authority Score (30%):    {opp_score.authority_score}/100")
    print(f"    - Distress Score (20%):     {opp_score.distress_score}/100")
    print(f"    - Liquidity Score (15%):    {opp_score.liquidity_score}/100")
    print(f"    - Gross Upside:             {opp_score.gross_upside:.1f}/100")
    print(f"    - Deal Friction Score (DFS):-{opp_score.deal_friction.total_dfs} pts")
    print(f"      (Title: -{opp_score.deal_friction.title_complexity_penalty}, Auth: -{opp_score.deal_friction.authority_friction_penalty}, Occ: -{opp_score.deal_friction.occupancy_penalty}, Heir: -{opp_score.deal_friction.heir_gridlock_penalty})")
    print(f"    - COMPOSITE SCORE:          {opp_score.composite_score}/100")
    print(f"    - PRIORITY TIER:            {opp_score.priority_tier.value}")
    print(f"    - RECOMMENDED STRATEGY:     {opp_score.recommended_strategy.value}")

    banner("4. STEP 8: AUTOMATED 6-GATE QUALITY CONTROL PASS (QCA)")
    # Step 8: QC Workflow
    qc_res = qc_wf.run(db, scoring_res["context"])
    qc_report = qc_res["context"]["qc_report"]

    print(" -> Programmatic 6-Gate Validation:")
    for gate in qc_report.gates:
        status_icon = "PASS" if gate.passed else "FAIL"
        print(f"    [{status_icon}] Gate {gate.gate_number}: {gate.gate_name:<38} | Score: {gate.score:>8.1f} | Threshold: {gate.threshold:>7.1f} | {gate.rationale}")

    print("\n[CRYPTOGRAPHIC NOTARIZATION]")
    print(f"  Seal:      {qc_res['certification_stamp']}")
    print(f"  Timestamp: {qc_report.certification_timestamp:.2f}")
    print(f"  Status:    {qc_res['status']} -> Advanced to READY (Delivery Ready)")

    banner("5. COMPLETE 8-STAGE AUDIT TRAIL")
    opp = db.query(OpportunityModel).filter_by(id=opp_id).first()
    print(f"Final Opportunity Stage: {opp.workflow_stage}")
    print(f"Final Opportunity Score: {opp.score}/100 ({opp.priority} Priority)")
    print(f"Authority Status:        {opp.authority_status}")

    logs = db.query(WorkflowAuditLogModel).filter_by(opportunity_id=opp_id).order_by(WorkflowAuditLogModel.timestamp.asc()).all()
    for log in logs:
        ts = log.timestamp.strftime("%H:%M:%S")
        print(f"  [{ts}] {log.from_stage:<14} -> {log.to_stage:<14} | Actor: {log.transitioned_by:<32} | Notes: {log.notes}")

    banner("6. CANONICAL EVENT PROPAGATION (ALL 7 EVENTS)")
    for i, ev in enumerate(emitted_events, 1):
        print(f"  Event {i}: {ev}")

    banner("SPRINT 4 DEMONSTRATION COMPLETE: READY FOR DELIVERY LAYER (SPRINT 5)")

if __name__ == "__main__":
    run_sprint4_demo()
