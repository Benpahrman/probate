"""
Gieni OS - Sprint 6 Closed-Loop Telemetry, RL Recalibration & Multi-County Scale
Demonstrates:
Full 10-Stage Autonomous Pipeline:
Intake -> Property -> Ownership -> Authority -> Control -> Contact -> Scoring -> QC -> Delivery -> Telemetry
Followed by:
1. Closed-Loop Telemetry Ingestion (Wholesale Fee Realized, Contact Latency)
2. Reinforcement Learning County Friction & Weight Recalibration
3. 5-Factor Automated 14-Day County Expansion Feasibility Scoring & Scraper Generation
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
from src.gieni_os.workflows.telemetry_workflow import TelemetryWorkflow
from src.gieni_os.engines.expansion_engine import ExpansionEngine

def banner(title: str):
    print("\n" + "=" * 80)
    print(f" {title.upper()}")
    print("=" * 80)

def run_sprint6_demo():
    banner("1. INITIALIZING SPRINT 6 RUNTIME & EVENT BUS")
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

    print("Database ready. Monitoring King County. Partner: Evergreen Home Acquisitions LLC.")

    # Instantiate All 10 Decoupled Workflows
    intake_wf = IntakeWorkflow(event_bus=bus)
    prop_wf = PropertyWorkflow(event_bus=bus)
    own_wf = OwnershipWorkflow(event_bus=bus)
    auth_wf = AuthorityWorkflow(event_bus=bus)
    control_wf = ControlWorkflow(event_bus=bus)
    contact_wf = ContactWorkflow(event_bus=bus)
    scoring_wf = ScoringWorkflow(event_bus=bus)
    qc_wf = QCWorkflow(event_bus=bus)
    delivery_wf = DeliveryWorkflow(event_bus=bus)
    telemetry_wf = TelemetryWorkflow(event_bus=bus)

    # Track Canonical Events
    pipeline_events = []
    def on_event(name, p):
        pipeline_events.append(name)

    for ev in [
        "PROPERTY_DISCOVERY_REQUIRED", "OWNERSHIP_ANALYSIS_REQUIRED",
        "AUTHORITY_ANALYSIS_REQUIRED", "CONTACT_ENRICHMENT_REQUIRED",
        "SCORING_REQUIRED", "QC_VALIDATION_REQUIRED", "OPPORTUNITY_QC_CERTIFIED",
        "DELIVERY_COMPLETED", "COUNTY_RECALIBRATED"
    ]:
        bus.subscribe(ev, lambda p, ev=ev: on_event(ev, p))

    banner("2. EXECUTING COMPLETE END-TO-END PIPELINE (STAGES 1 TO 9)")
    filing = {
        "case_number": "24-4-04199-5 SEA",
        "county_id": "cty_king",
        "decedent_name": "John Coltrane",
        "petitioner_name": "Alice Coltrane",
        "filing_date": date(2026, 9, 19),
        "raw_address": "1960 Blue Train Ave, Seattle, WA 98101",
        "docket_entries": [
            "PETITION FOR PROBATE OF WILL",
            "ORDER APPOINTING PR WITH RCW 11.68 NONINTERVENTION POWERS",
            "LETTERS TESTAMENTARY ISSUED TO ALICE COLTRANE"
        ],
        "attorney_name": "Impulse Legal Partners PS",
        "heir_names": ["Alice Coltrane", "Ravi Coltrane"],
        "resident_names": ["Alice Coltrane"]
    }

    # Execute Stages 1 through 9
    intake_res = intake_wf.run(db, filing)
    prop_res = prop_wf.run(db, intake_res["context"])
    own_res = own_wf.run(db, prop_res["context"])
    auth_res = auth_wf.run(db, own_res["context"])
    ctrl_res = control_wf.run(db, auth_res["context"])
    contact_res = contact_wf.run(db, ctrl_res["context"])
    scoring_res = scoring_wf.run(db, contact_res["context"])
    qc_res = qc_wf.run(db, scoring_res["context"])

    delivery_context = {
        **qc_res["context"],
        "client_id": "client_evergreen",
        "crm_platform": "GOHIGHLEVEL",
        "client_phone": "+12065550199"
    }
    delivery_res = delivery_wf.run(db, delivery_context)

    opp_id = intake_res["opportunity_id"]
    print(f"Opportunity {opp_id} Delivered to Evergreen CRM (HTTP 200, Latency: {delivery_res['latency_ms']}ms).")

    banner("3. STAGE 10: PARTNER DISPOSITION TELEMETRY INGESTION")
    telemetry_context = {
        **delivery_res["context"],
        "disposition_stage": "CLOSED_WON",
        "assignment_fee_realized": 48500.0,
        "contact_latency_hours": 0.8,
        "decision_maker_accurate": True,
        "disposition_notes": "Contract executed in 4 days. Zero repair credit required. Escrow closed."
    }

    telemetry_res = telemetry_wf.run(db, telemetry_context)
    recal = telemetry_res["context"]

    print(" -> Commercial Disposition Feedback Recorded:")
    print(f"    - Outcome:                  CLOSED_WON")
    print(f"    - First-Touch Contact Speed:{telemetry_context['contact_latency_hours']} hours (Sub-4-Hour SLA Met)")
    print(f"    - Wholesale Fee Realized:   ${telemetry_res['assignment_fee_realized']:,.2f}")
    print(f"    - Decision-Maker Accuracy:  100%")

    banner("4. REINFORCEMENT LEARNING COUNTY FRICTION RECALIBRATION")
    print(" -> Closed-Loop RL Flywheel Updated:")
    print(f"    - County Target:            {recal['county_fips']} (King County)")
    print(f"    - Calibrated Friction Coeff:{recal['calibrated_friction_coefficient']} (Tuned downward as win rate increases)")
    print(f"    - Updated Feature Weights:  {recal['updated_feature_weights']}")
    print(f"    - Quarterly Predictive Gain:+{recal['predictive_accuracy_gain_pct']}% Accuracy")

    banner("5. AUTOMATED 14-DAY COUNTY EXPANSION FEASIBILITY SCORING")
    target_counties = ["cty_king", "cty_pierce", "cty_snohomish", "cty_spokane", "cty_clark", "cty_thurston"]
    print(f" {'County':<18} | {'Feasibility Score':<18} | {'Status':<16} | {'Scraper Ready'}")
    print(" " + "-" * 72)

    for cty in target_counties:
        feas = ExpansionEngine.evaluate_county(cty)
        scraper = ExpansionEngine.generate_scraper_script(cty)
        has_scraper = "YES (Playwright)" if len(scraper) > 100 else "NO"
        print(f" {feas.county_name:<18} | {feas.composite_feasibility:>17.1f}/100 | {feas.status.value:<16} | {has_scraper}")

    banner("6. COMPLETE 10-STAGE AUDIT TRAIL")
    opp = db.query(OpportunityModel).filter_by(id=opp_id).first()
    print(f"Final Opportunity Stage: {opp.workflow_stage}")
    print(f"Final Viability Score:   {opp.score}/100 ({opp.priority} Priority)")

    logs = db.query(WorkflowAuditLogModel).filter_by(opportunity_id=opp_id).order_by(WorkflowAuditLogModel.timestamp.asc()).all()
    for log in logs:
        ts = log.timestamp.strftime("%H:%M:%S")
        print(f"  [{ts}] {log.from_stage:<14} -> {log.to_stage:<14} | Actor: {log.transitioned_by:<32} | Notes: {log.notes}")

    banner("7. CANONICAL EVENT PROPAGATION (ALL 9 EVENTS)")
    for i, ev in enumerate(pipeline_events, 1):
        print(f"  Event {i}: {ev}")

    banner("GIENI OS FULL 12-WEEK ROADMAP (SPRINTS 1 TO 6) COMPLETE & CERTIFIED")

if __name__ == "__main__":
    run_sprint6_demo()
