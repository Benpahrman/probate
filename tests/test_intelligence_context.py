"""
Test Suite: Gieni OS Intelligence Context (The Brain)
Validates all 8 subsystems: Memory, Reasoning, Retrieval, Knowledge,
Learning, Recommendations, Prompt Registry, and Vector Layer, plus API routes.
"""

import pytest
from fastapi.testclient import TestClient

from gieni_os.api.main import app
from gieni_os.database.connection import SessionLocal, init_db
from gieni_os.database.models import (
    CountyModel,
    ProbateCaseModel,
    OpportunityModel,
)
from gieni_os.intelligence.models import (
    MemoryScope,
    ObservationSource,
    StakeholderRole,
    LearningOutcomeType,
)
from gieni_os.intelligence.memory.service import MemoryService
from gieni_os.intelligence.prompts.registry import PromptRegistry, PromptTemplate
from gieni_os.intelligence.embeddings.vector_service import VectorService
from gieni_os.intelligence.knowledge.service import KnowledgeService
from gieni_os.intelligence.learning.service import LearningService
from gieni_os.intelligence.recommendations.service import RecommendationService
from gieni_os.intelligence.reasoning.service import ReasoningService
from gieni_os.intelligence.context import IntelligenceContext

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_memory_service(db_session):
    import uuid
    service = MemoryService(db=db_session)
    entry_id = f"case_test_mem_{uuid.uuid4().hex[:8]}"

    # 1. Store
    entry = service.store(
        scope=MemoryScope.CASE,
        entity_id=entry_id,
        summary="Initial filing discovered on Odyssey",
        observations=["Will filed with court", "No objections filed"],
        attributes={"court": "Thurston Superior", "docket": "26-4-00123-1"},
        confidence=0.88,
    )
    assert entry.entity_id == entry_id
    assert entry.scope == MemoryScope.CASE
    assert len(entry.observations) == 2
    assert entry.confidence == 0.88

    # 2. Retrieve
    retrieved = service.retrieve(scope=MemoryScope.CASE, entity_id=entry_id)
    assert retrieved is not None
    assert retrieved.summary == "Initial filing discovered on Odyssey"
    assert "court" in retrieved.attributes

    # 3. Merge
    merged = service.merge(
        scope=MemoryScope.CASE,
        entity_id=entry_id,
        new_observations=["Letters Testamentary issued to PR"],
        summary_update="Letters Testamentary confirmed",
        confidence_delta=0.05,
    )
    assert len(merged.observations) == 3
    assert merged.summary == "Letters Testamentary confirmed"
    assert merged.confidence > 0.90

    # 4. Search
    results = service.search(query="Letters", scope=MemoryScope.CASE)
    assert len(results) >= 1
    assert any(r.entity_id == entry_id for r in results)


def test_prompt_registry():
    registry = PromptRegistry()

    # 1. Check default registered templates
    tmpl = registry.get("ownership-analysis", "v1")
    assert tmpl.category == "ownership"
    assert "property_address" in tmpl.required_variables

    # 2. Render successfully
    rendered = tmpl.format(
        property_address="123 Main St, Tacoma, WA",
        assessed_value=350000,
        arv=450000,
        encumbrances=80000,
        vesting_status="Estate of John Doe",
    )
    assert "123 Main St" in rendered
    assert "$350,000" in rendered

    # 3. Missing variable validation
    with pytest.raises(ValueError):
        tmpl.format(property_address="123 Main St")


def test_vector_service(db_session):
    vservice = VectorService(db=db_session, dimension=64)

    # 1. Generate embedding
    vec = vservice.generate_embedding("Probate nonintervention powers under RCW 11.68")
    assert len(vec) == 64
    assert any(x != 0.0 for x in vec)

    # 2. Store vector
    rec = vservice.store(
        entity_type="OPPORTUNITY",
        entity_id="opp_vec_test_1",
        text="Estate in Tacoma with high equity and autonomous letters testamentary.",
        metadata={"priority": "PRIORITY_A"},
    )
    assert rec.entity_id == "opp_vec_test_1"

    # 3. Similar match
    matches = vservice.similar(
        text="Tacoma estate with high equity and letters",
        entity_type="OPPORTUNITY",
        top_k=3,
        threshold=0.01,
    )
    assert len(matches) >= 1
    assert matches[0]["entity_id"] == "opp_vec_test_1"
    assert matches[0]["score"] > 0.0


def test_knowledge_service(db_session):
    ks = KnowledgeService(db=db_session)

    # 1. Check seeded articles
    thurston_rules = ks.get_county_rules("Thurston")
    assert len(thurston_rules) >= 1
    assert "Thurston County" in thurston_rules[0].title

    sop = ks.get_statutory_sop("11.68")
    assert len(sop) >= 1
    assert "RCW 11.68" in sop[0].title

    # 2. Add custom article
    custom = ks.add_article(
        category="ATTORNEY_PATTERN",
        title="Probate Law Firm Benchmark Timelines",
        content="Average timeline to resolve objections under TEDRA is 90 days.",
        statutory_reference="RCW 11.96A",
    )
    assert custom.title == "Probate Law Firm Benchmark Timelines"


def test_learning_service(db_session):
    ls = LearningService(db=db_session)

    # Ensure test opp exists
    opp = db_session.query(OpportunityModel).first()
    opp_id = opp.id if opp else "opp_001"
    county_id = opp.county_id if opp else "county-pierce"

    # Record CLOSING event
    event = ls.record_outcome(
        opportunity_id=opp_id,
        county_id=county_id,
        event_type=LearningOutcomeType.CLOSING,
        realized_margin=25000.0,
        notes="Closed cash transaction with PR in 14 days",
    )
    assert event.event_type == LearningOutcomeType.CLOSING
    assert event.delta_score == 5.0
    assert event.realized_margin == 25000.0

    # Check county friction
    friction = ls.get_county_friction("Pierce")
    assert friction > 0.0


def test_recommendation_service():
    rs = RecommendationService()

    # Context 1: Authority pending
    ctx_pending = {
        "authority_profile": {"authority_tier": "UNRESOLVED", "can_execute_psa": False},
        "ownership_profile": {"net_distributable_equity": 120000},
        "control_profile": {"primary_decision_maker": "Jane Doe"},
    }
    actions_res = rs.next_action(ctx_pending, role=StakeholderRole.RESEARCHER)
    assert len(actions_res) >= 1
    assert actions_res[0].action_type == "SEARCH_DOCKET"

    # Context 2: Authority verified
    ctx_verified = {
        "authority_profile": {"authority_tier": "TIER_1_UNCONTESTED_NONINTERVENTION", "can_execute_psa": True},
        "ownership_profile": {"net_distributable_equity": 150000},
        "control_profile": {"primary_decision_maker": "Jane Doe"},
    }
    actions_client = rs.next_action(ctx_verified, role=StakeholderRole.CLIENT_INVESTOR)
    assert len(actions_client) >= 1
    assert actions_client[0].action_type == "SUBMIT_CASH_PSA"


def test_reasoning_service():
    reasoning = ReasoningService()
    ctx = {
        "property_profile": {"situs_address": "8842 Pacific Ave, Tacoma, WA"},
        "ownership_profile": {"net_distributable_equity": 210000, "net_equity_pct": 0.65},
        "authority_profile": {"statutory_basis": "RCW 11.68.011 (Nonintervention Powers)"},
    }

    res = reasoning.reason(
        inquiry="Why is this opportunity viable?",
        context=ctx,
        retrieved_memory=["PR appointed with zero bond required"],
        retrieved_knowledge=["Pierce County permits ex parte nonintervention grants"],
    )
    assert len(res.narrative) > 20
    assert res.confidence > 0.85
    assert len(res.recommendations) >= 1


def test_intelligence_context_evaluate_opportunity(db_session):
    opp = db_session.query(OpportunityModel).first()
    opp_id = opp.id if opp else "opp_001"

    intel = IntelligenceContext(db=db_session)
    response = intel.evaluate_opportunity(
        opportunity_id=opp_id,
        inquiry="Who controls disposition and what is the statutory basis?",
        county_name="Pierce",
    )
    assert response.confidence > 0.85
    assert len(response.recommendations) >= 1

    # Verify memory observation was recorded
    mem = intel.memory.retrieve(scope=MemoryScope.OPPORTUNITY, entity_id=opp_id)
    assert mem is not None
    assert len(mem.observations) >= 1


def test_intelligence_api_endpoints():
    # 1. Status
    res_status = client.get("/api/intelligence/status")
    assert res_status.status_code == 200
    assert res_status.json()["status"] == "OPERATIONAL"
    assert "memory_service" in res_status.json()["subsystems"]

    # 2. Knowledge
    res_kb = client.get("/api/intelligence/knowledge")
    assert res_kb.status_code == 200
    assert isinstance(res_kb.json(), list)

    # 3. Recommendations
    res_recs = client.post(
        "/api/intelligence/recommendations",
        json={"context": {"authority_profile": {"can_execute_psa": True}}, "role": "CLIENT_INVESTOR"},
    )
    assert res_recs.status_code == 200
    assert len(res_recs.json()) >= 1

    # 4. Memory Store & Retrieve
    res_mem_store = client.post(
        "/api/intelligence/memory",
        json={
            "scope": "OPPORTUNITY",
            "entity_id": "opp_api_test_mem",
            "summary": "API Memory Test Entry",
            "observations": ["Initial observation from API"],
            "attributes": {"source": "unit_test"},
            "confidence": 0.95,
        },
        headers={"x-clerk-user-id": "op_admin_1", "x-clerk-role": "Platform Admin"},
    )
    assert res_mem_store.status_code == 200
    assert res_mem_store.json()["entity_id"] == "opp_api_test_mem"

    res_mem_get = client.get("/api/intelligence/memory/OPPORTUNITY/opp_api_test_mem")
    assert res_mem_get.status_code == 200
    assert res_mem_get.json()["summary"] == "API Memory Test Entry"

    # 5. Learn Outcome
    res_learn = client.post(
        "/api/intelligence/learn",
        json={
            "opportunity_id": "opp_api_test_mem",
            "county_id": "county-pierce",
            "event_type": "OFFER",
            "realized_margin": 15000.0,
            "notes": "Offer presented by client",
        },
        headers={"x-clerk-user-id": "op_admin_1", "x-clerk-role": "Platform Admin"},
    )
    assert res_learn.status_code == 200
    assert res_learn.json()["event_type"] == "OFFER"

    # 6. Reason
    res_reason = client.post(
        "/api/intelligence/reason",
        json={
            "inquiry": "What is the authority path for this opportunity?",
            "context": {"authority_profile": {"statutory_basis": "RCW 11.68.011"}},
        },
        headers={"x-clerk-user-id": "op_admin_1", "x-clerk-role": "Platform Admin"},
    )
    assert res_reason.status_code == 200
    assert "narrative" in res_reason.json()
    assert "confidence" in res_reason.json()
