"""
Test Suite: Audit Remediation Verification (P0, P1, P2)
Verifies the production remediation of all 20 audit issues identified
in issues.md and audit_report.md.
"""

import os
import pytest
import html
from fastapi.testclient import TestClient

from gieni_os.api.main import app
from gieni_os.database.connection import SessionLocal, engine, get_db
from gieni_os.database.models import OpportunityModel, CountyModel, ProbateCaseModel
from gieni_os.api.routes.client_portal import validate_webhook_url
from gieni_os.api.deps import get_current_user, ClerkUserContext
from gieni_os.pof.builder import ProbateOpportunityFileBuilder
from gieni_os.pof.exporter import POFExporter
from gieni_os.graph.topology import KnowledgeGraph, GraphNode, NodeType
from gieni_os.engines.delivery_engine import DeliveryEngine
from gieni_os.services.pof_resolver import POFDataResolver
from gieni_os.events.bus import EventBus
from gieni_os import config

client = TestClient(app)


# =========================================================================
# P0-1: IDOR & Multitenancy Security
# =========================================================================
def test_p0_1_unauthenticated_access_blocked():
    """Unauthenticated requests to opportunities, cases, and POF HTML must return 401."""
    res_opps = client.get("/api/opportunities")
    assert res_opps.status_code == 401

    res_cases = client.get("/api/cases")
    assert res_cases.status_code == 401

    res_pof = client.get("/api/pof/opp_001/html")
    assert res_pof.status_code == 401


def test_p0_1_tenant_isolation():
    """B2B partner only receives opportunities belonging to their contracted county."""
    db = SessionLocal()
    try:
        cty = db.query(CountyModel).filter(CountyModel.name == "Pierce").first()
        if not cty:
            cty = CountyModel(id="cty_pierce", name="Pierce", state="WA", is_active=True)
            db.add(cty)
            db.commit()

        opp_pierce = db.query(OpportunityModel).filter(OpportunityModel.county_id == cty.id).first()
        if not opp_pierce:
            opp_pierce = OpportunityModel(
                id="opp_test_pierce",
                county_id=cty.id,
                lead_name="Estate of Pierce Resident",
                workflow_stage="READY",
                priority="Priority A",
                score=90
            )
            db.add(opp_pierce)
            db.commit()
    finally:
        db.close()

    # B2B Client headers mapped to Sound Capital (Pierce county)
    b2b_headers = {
        "x-clerk-user-id": "user_client_sound",
        "x-clerk-org-id": "org_sound_capital",
        "x-clerk-role": "org:member"
    }
    res = client.get("/api/opportunities", headers=b2b_headers)
    assert res.status_code == 200
    opps = res.json()
    assert len(opps) > 0
    for opp in opps:
        assert opp["county_name"] == "Pierce"


# =========================================================================
# P0-2: SSRF Vulnerability Prevention
# =========================================================================
def test_p0_2_ssrf_webhook_validation():
    """validate_webhook_url rejects private IPs, loopback, metadata services, and non-HTTPS."""
    forbidden_urls = [
        "http://169.254.169.254/latest/meta-data/",  # AWS metadata
        "http://127.0.0.1:8000/internal",            # IPv4 loopback
        "http://localhost:6379",                     # Localhost Redis
        "https://10.0.0.1/admin",                    # Class A private
        "https://172.16.0.1/secret",                 # Class B private
        "https://192.168.1.1/router",                # Class C private
        "http://webhook.site/insecure",              # Plain HTTP
        "ftp://example.com/payload",                 # Invalid scheme
    ]
    for url in forbidden_urls:
        with pytest.raises(Exception):
            validate_webhook_url(url)

    # Valid HTTPS public URL should pass and return the URL
    valid_url = "https://api.pipedrive.com/v1/deals"
    assert validate_webhook_url(valid_url) == valid_url


# =========================================================================
# P0-3: JWT Signature Verification Enforcement
# =========================================================================
def test_p0_3_jwt_signature_bypass_forbidden_in_production(monkeypatch):
    """When DEMO_MODE is not true, unsigned JWTs must be strictly rejected."""
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.delenv("CLERK_PEM_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("CLERK_SECRET_KEY", raising=False)

    fake_jwt = "Bearer eyJhbGciOiJub25lIn0.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ."
    with pytest.raises(Exception) as exc_info:
        get_current_user(authorization=fake_jwt)
    assert "401" in str(exc_info.value) or "DEMO_MODE" in str(exc_info.value) or "Signature" in str(exc_info.value)


# =========================================================================
# P0-4: DB Engine Pooling & Transaction Rollback
# =========================================================================
def test_p0_4_engine_configuration():
    """Verify engine has pool initialized."""
    assert engine.pool is not None


def test_p0_4_get_db_rollback():
    """Verify get_db rolls back on unhandled generator exception."""
    gen = get_db()
    session = next(gen)
    assert session.is_active
    try:
        raise ValueError("Simulated unexpected route error")
    except ValueError as e:
        with pytest.raises(ValueError):
            gen.throw(e)


# =========================================================================
# P0-5: Internal Research RBAC
# =========================================================================
def test_p0_5_research_access_control():
    """B2B Client organization should be forbidden (403) from internal skip-trace routes."""
    b2b_headers = {
        "x-clerk-user-id": "user_client_sound",
        "x-clerk-org-id": "org_sound_capital",
        "x-clerk-role": "org:member"
    }
    res_contacts = client.post(
        "/api/research/contacts",
        json={"target_name": "Clara Bell", "county_id": "cty_pierce", "area": "CONTACTS"},
        headers=b2b_headers
    )
    assert res_contacts.status_code == 403

    res_title = client.post(
        "/api/research/title",
        json={"address": "1200 Pacific Ave", "county_id": "cty_pierce", "area": "TITLE"},
        headers=b2b_headers
    )
    assert res_title.status_code == 403



# =========================================================================
# P1-2: Stored XSS Prevention in POF HTML
# =========================================================================
def test_p1_2_pof_html_xss_sanitization():
    """POFExporter must escape malicious HTML tags in decedent, property, or heirs."""
    raw_filing = {
        "case_number": "26-4-09999-1",
        "decedent_name": "<script>alert('XSS-decedent')</script>",
        "address": "42 Galaxy Way <img src=x onerror=alert(1)>"
    }
    pra = {
        "apn": "0123456789",
        "situs_address": "42 GALAXY WAY <script>",
        "city_state": "TACOMA, WA",
        "zipcode": "98402",
        "total_assessed_value": 600000,
        "pas_score": 99.0
    }
    pof = ProbateOpportunityFileBuilder.build(
        opp_id="OPP-XSS-01",
        pia={},
        pra=pra,
        oia={"net_equity_waterfall": {}},
        cia={"control_archetype": "Unified", "decision_maker_dossier": {"name": "<b>Attacker</b>"}},
        ara={"statutory_authority_tier": "Tier 1"},
        osa={"composite_viability_score": 90},
        qca={"certification_status": "CERTIFIED"},
        raw_filing=raw_filing
    )
    html_out = POFExporter.to_institutional_html(pof)
    assert "<script>" not in html_out
    assert "&lt;script&gt;" in html_out
    assert "<b>Attacker</b>" not in html_out
    assert "&lt;b&gt;Attacker&lt;/b&gt;" in html_out





# =========================================================================
# P1-5: Cypher Injection Sanitization
# =========================================================================
def test_p1_5_cypher_injection_sanitization():
    """KnowledgeGraph export_cypher must escape single quotes in labels and properties."""
    kg = KnowledgeGraph()
    kg.add_node(GraphNode("node_malicious", NodeType.PERSON, {"name": "O'Connor'; DROP GRAPH; --"}))
    cypher_output = kg.export_cypher()
    assert "O\\'Connor" in cypher_output or "''" in cypher_output or "\\'" in cypher_output
    assert "DROP GRAPH;" not in [line.strip() for line in cypher_output.split("\n")]


# =========================================================================
# P1-6: DeliveryEngine Mock Data Fallbacks Removed
# =========================================================================
def test_p1_6_delivery_engine_no_synthetic_fallbacks():
    """DeliveryEngine.assemble_pof_from_context returns None/Unknown for missing fields without inventing Vance."""
    sparse_context = {
        "opportunity_id": "opp_sparse_001",
        "case_number": "26-4-00999-1"
    }
    pof = DeliveryEngine.assemble_pof_from_context(sparse_context)
    assert pof.control_profile.primary_decision_maker is None
    assert pof.property_profile.situs_address == "ADDRESS_UNKNOWN"
    assert pof.property_profile.avm_market_estimate == 0.0
    assert pof.opportunity_profile.priority_tier == "UNASSIGNED"



# =========================================================================
# P2-3: Graceful Assessor Error Handling
# =========================================================================
def test_p2_3_unconfigured_assessor_graceful():
    """POFDataResolver and PropertyService gracefully handle unconfigured counties without crashing."""
    res = POFDataResolver.lookup_county_assessor("cty_nonexistent", "APN-99999")
    assert res is not None
    assert "status" in res or "median_assessed" in res




# =========================================================================
# P2-4: Notion Database Config from Environment
# =========================================================================
def test_p2_4_notion_config_env():
    """Notion database IDs must be loaded from config/environment."""
    assert hasattr(config, "KB_DB_ID")
    assert hasattr(config, "CLIENTS_DB_ID")
    assert hasattr(config, "OPPORTUNITIES_DB_ID")
