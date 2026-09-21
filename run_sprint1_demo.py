"""
Gieni OS - Sprint 1 Foundation End-to-End Simulation & Verification Script
Demonstrates:
Case -> Workflow -> Opportunity -> Queue -> Human Review
(Zero AI, Deterministic Foundation, State Transitions & Audit Trails)
"""

import sys
import os
from datetime import date, datetime

# Ensure repo root is on path
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.gieni_os.database.connection import init_db, SessionLocal
from src.gieni_os.database.models import (
    CountyModel, ClientModel, ProbateCaseModel,
    OpportunityModel, ExceptionModel, WorkflowAuditLogModel
)
from src.gieni_os.workflow.engine import WorkflowEngine, WorkflowStage
from src.gieni_os.agents.registry import AgentRegistry
from src.gieni_os.agents.intake_agent import ProbateIntakeAgent
from src.gieni_os.agents.qc_agent import QCAgent
from src.gieni_os.events.bus import EventBus

def format_banner(title: str):
    print("\n" + "=" * 80)
    print(f" {title.upper()}")
    print("=" * 80)

def run_sprint1_demo():
    format_banner("1. INITIALIZING GIENI OS DATABASE FOUNDATION")
    init_db()
    db = SessionLocal()

    # Clear previous run demo data cleanly
    db.query(WorkflowAuditLogModel).delete()
    db.query(ExceptionModel).delete()
    db.query(OpportunityModel).delete()
    db.query(ProbateCaseModel).delete()
    db.query(ClientModel).delete()
    db.query(CountyModel).delete()
    db.commit()
    print("Database tables initialized cleanly.")

    format_banner("2. CREATING JURISDICTIONS (COUNTIES)")
    counties_data = [
        ("cty_king", "King", "WA", "TIER_1"),
        ("cty_pierce", "Pierce", "WA", "TIER_1"),
        ("cty_snohomish", "Snohomish", "WA", "TIER_2"),
    ]
    for cid, name, state, tier in counties_data:
        c = CountyModel(id=cid, name=name, state=state, tier=tier, status="ACTIVE")
        db.add(c)
    db.commit()
    print(f"Created {len(counties_data)} operational counties.")

    format_banner("3. REGISTERING CLIENTS")
    clients_data = [
        ("cl_nw_estates", "Northwest Estate Buyers LLC", date(2027, 1, 1), "cty_king"),
        ("cl_cascade", "Cascade Legacy Properties", date(2027, 3, 15), "cty_pierce"),
    ]
    for cid, name, rdate, county_id in clients_data:
        cl = ClientModel(id=cid, name=name, renewal_date=rdate, county_id=county_id, status="ACTIVE")
        db.add(cl)
    db.commit()
    print(f"Created {len(clients_data)} active enterprise clients.")

    format_banner("4. INGESTING PROBATE CASES")
    cases_data = [
        ("case_01", "24-4-01021-1", "cty_king", "Eleanor Rigby", date(2026, 9, 10)),
        ("case_02", "24-4-00894-3", "cty_pierce", "Arthur Pendelton", date(2026, 9, 12)),
        ("case_03", "24-4-00512-8", "cty_snohomish", "Dorothy Gale", date(2026, 9, 14)),
        ("case_04", "24-4-01099-2", "cty_king", "Walter White", date(2026, 9, 16)),
    ]
    created_cases = []
    for cid, num, county_id, dec, fdate in cases_data:
        pcase = ProbateCaseModel(id=cid, case_number=num, county_id=county_id, decedent=dec, filing_date=fdate)
        db.add(pcase)
        created_cases.append(pcase)
    db.commit()
    print(f"Ingested {len(created_cases)} court filings.")

    format_banner("5. PIPELINING OPPORTUNITIES IN 9-STAGE STATE MACHINE")
    opps = []
    for i, c in enumerate(created_cases, start=1):
        opp = OpportunityModel(
            id=f"opp_00{i}",
            case_id=c.id,
            county_id=c.county_id,
            workflow_stage=WorkflowStage.NEW.value,
            authority_status="UNRESOLVED",
            priority="HIGH" if i == 1 else "MEDIUM",
            score=0
        )
        db.add(opp)
        opps.append(opp)
    db.commit()

    # --- ADVANCE OPPORTUNITY 1 ALL THE WAY TO QC GATE ---
    print("\n--> Transitioning Opportunity 1 (Eleanor Rigby) through 6 deterministic stages to QC Gate:")
    stages_flow = [
        (WorkflowStage.PROPERTY_MATCH.value, "Property matched to 1422 Elm St Seattle WA (Parcel #90210)"),
        (WorkflowStage.OWNERSHIP.value, "Title clear: sole ownership confirmed via King County Assessor"),
        (WorkflowStage.AUTHORITY.value, "Letters of Administration granted to PR James Rigby"),
        (WorkflowStage.ENRICHMENT.value, "PR phone verified (206-555-0144), skip trace confident"),
        (WorkflowStage.SCORING.value, "Equity assessed: $680k estimated equity, pipeline score 88/100"),
        (WorkflowStage.QC.value, "Placed in Gate 6 QC Queue awaiting final human review")
    ]

    for target_stage, note in stages_flow:
        WorkflowEngine.transition(
            db=db,
            opportunity_id="opp_001",
            to_stage=target_stage,
            transitioned_by="WorkflowDaemon",
            notes=note
        )
        print(f"    [STAGED] -> {target_stage}")

    # Mark authority resolved on opp_001
    opp_1 = db.query(OpportunityModel).filter_by(id="opp_001").first()
    opp_1.authority_status = "RESOLVED"
    opp_1.score = 88
    db.commit()

    # --- ADVANCE OPPORTUNITY 2 TO AUTHORITY QUEUE ---
    print("\n--> Transitioning Opportunity 2 (Arthur Pendelton) to AUTHORITY stage:")
    WorkflowEngine.transition(
        db=db,
        opportunity_id="opp_002",
        to_stage=WorkflowStage.PROPERTY_MATCH.value,
        transitioned_by="WorkflowDaemon",
        notes="Parcel matched to Puyallup acreage"
    )
    WorkflowEngine.transition(
        db=db,
        opportunity_id="opp_002",
        to_stage=WorkflowStage.OWNERSHIP.value,
        transitioned_by="WorkflowDaemon",
        notes="Title verified"
    )
    WorkflowEngine.transition(
        db=db,
        opportunity_id="opp_002",
        to_stage=WorkflowStage.AUTHORITY.value,
        transitioned_by="WorkflowDaemon",
        notes="Awaiting fiduciary court confirmation (Authority Queue)"
    )
    print("    [STAGED] -> AUTHORITY (Needs human authority verification)")

    # --- OPPORTUNITY 3 LOGS AN EXCEPTION ---
    print("\n--> Logging Exception on Opportunity 3 (Dorothy Gale):")
    WorkflowEngine.transition(
        db=db,
        opportunity_id="opp_003",
        to_stage=WorkflowStage.PROPERTY_MATCH.value,
        transitioned_by="WorkflowDaemon",
        notes="Multiple parcel candidates found"
    )
    exc = ExceptionModel(
        id="exc_001",
        opportunity_id="opp_003",
        type="TITLE_AMBIGUITY",
        severity="HIGH",
        status="OPEN",
        assignee="Researcher_Sarah",
        notes="Two properties found in Snohomish county with matching decedent name; requires parcel deed lookup."
    )
    db.add(exc)
    db.commit()
    print("    [EXCEPTION LOGGED] -> TITLE_AMBIGUITY on opp_003 assigned to Researcher_Sarah")

    # --- OPPORTUNITY 4 DEMONSTRATES QC REWORK LOOP ---
    print("\n--> Demonstrating QC Rework Loop on Opportunity 4:")
    for stage in [
        WorkflowStage.PROPERTY_MATCH.value,
        WorkflowStage.OWNERSHIP.value,
        WorkflowStage.AUTHORITY.value,
        WorkflowStage.ENRICHMENT.value,
        WorkflowStage.SCORING.value,
        WorkflowStage.QC.value
    ]:
        WorkflowEngine.transition(db=db, opportunity_id="opp_004", to_stage=stage, transitioned_by="WorkflowDaemon")
    
    print("    opp_004 reached QC. QC Reviewer rejects title due to cloud.")
    WorkflowEngine.transition(
        db=db,
        opportunity_id="opp_004",
        to_stage=WorkflowStage.OWNERSHIP.value,
        transitioned_by="QC_Inspector",
        notes="REWORK: Second lien detected on title. Routed back to OWNERSHIP stage."
    )
    print("    [REWORK APPLIED] -> opp_004 sent back from QC to OWNERSHIP.")

    format_banner("6. AGENT REGISTRY & EVENT BUS VERIFICATION")
    event_bus = EventBus()

    # Spin up production agents
    intake_agent = ProbateIntakeAgent()
    qc_agent = QCAgent()

    AgentRegistry.register_agent(
        db=db,
        agent_id=intake_agent.agent_id,
        agent_name=intake_agent.agent_name,
        capabilities="docket_parsing,event_listening"
    )
    AgentRegistry.register_agent(
        db=db,
        agent_id=qc_agent.agent_id,
        agent_name=qc_agent.agent_name,
        capabilities="gate_verification,score_thresholds"
    )

    registered_agents = AgentRegistry.list_agents(db)
    print(f"Registered Agents in Database Registry: {len(registered_agents)}")
    for a in registered_agents:
        print(f"  - {a.agent_name} ({a.id}): Status = {a.status} | Capabilities = {a.capabilities}")

    # Fire canonical event
    event_bus.publish("CASE_CREATED", {
        "case_id": "case_01",
        "case_number": "24-4-01021-1",
        "county_id": "cty_king"
    })

    format_banner("7. OPERATIONS DASHBOARD STATE SUMMARY")
    print(f"Total Cases:         {db.query(ProbateCaseModel).count()}")
    print(f"Total Opportunities: {db.query(OpportunityModel).count()}")
    print(f"Active Counties:     {db.query(CountyModel).count()}")
    print(f"Active Clients:      {db.query(ClientModel).count()}")
    print(f"Open Exceptions:     {db.query(ExceptionModel).filter_by(status='OPEN').count()}")

    print("\n[QC QUEUE - GATE 6 HUMAN REVIEW]")
    qc_queue = db.query(OpportunityModel).filter_by(workflow_stage="QC").all()
    for q in qc_queue:
        print(f"  * Opp ID: {q.id} | Case ID: {q.case_id} | County: {q.county_id} | Score: {q.score}/100 | Authority: {q.authority_status}")

    print("\n[AUTHORITY QUEUE - FIDUCIARY RESOLUTION]")
    auth_queue = db.query(OpportunityModel).filter_by(workflow_stage="AUTHORITY").all()
    for a in auth_queue:
        print(f"  * Opp ID: {a.id} | Case ID: {a.case_id} | County: {a.county_id} | Stage: {a.workflow_stage} | Authority: {a.authority_status}")

    print("\n[EXCEPTION QUEUE - TRIAGE]")
    exc_queue = db.query(ExceptionModel).filter_by(status="OPEN").all()
    for e in exc_queue:
        print(f"  * Exc ID: {e.id} | Opp: {e.opportunity_id} | Type: {e.type} | Severity: {e.severity} | Assignee: {e.assignee}")

    print("\n[AUDIT TRAIL SAMPLE - OPP_001]")
    audit_logs = db.query(WorkflowAuditLogModel).filter_by(opportunity_id="opp_001").all()
    for log in audit_logs:
        print(f"  {log.timestamp.strftime('%H:%M:%S')} | {log.from_stage:<14} -> {log.to_stage:<14} | User: {log.transitioned_by:<14} | {log.notes}")

    db.close()
    format_banner("SPRINT 1 PLATFORM SKELETON DEMO COMPLETE")
    print("To launch the live dashboard UI, run:")
    print("    python -m uvicorn src.gieni_os.api.main:app --reload --port 8000")
    print("Then open: http://localhost:8000\n")

if __name__ == "__main__":
    run_sprint1_demo()
