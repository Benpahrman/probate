"""
Test Suite for Probate Opportunity File (POF v2.0) Builder & Exporters
"""

import pytest
from gieni_os.pof.builder import ProbateOpportunityFileBuilder
from gieni_os.pof.exporter import POFExporter

def test_pof_builder_and_exports():
    opp_id = "OPP-UNIT-01"
    raw_filing = {
        "case_number": "26-4-09999-1",
        "decedent_name": "Estate of Arthur Dent",
        "address": "42 Galaxy Way, Tacoma, WA 98402"
    }

    pia_output = {"candidate_parcels": [{"is_primary": True}]}
    pra_output = {
        "apn": "0123456789",
        "situs_address": "42 GALAXY WAY",
        "city_state": "TACOMA, WA",
        "zipcode": "98402",
        "total_assessed_value": 600000,
        "land_value": 250000,
        "improvement_value": 350000,
        "landuse": "SFR",
        "legal_description": "LOT 1 BLOCK 2 SUBDIVISION",
        "pas_score": 99.0
    }
    oia_output = {
        "vesting_classification": "Fee Simple Sole",
        "ownership_complexity_score": 10,
        "net_equity_waterfall": {
            "estimated_arv": 750000.0,
            "senior_mortgage_balance": 50000.0,
            "municipal_liens": 0.0,
            "estimated_repairs": 25000.0,
            "net_distributable_equity": 675000.0,
            "target_mao": 480000.0,
            "is_free_and_clear": False
        }
    }
    cia_output = {
        "control_archetype": "Unified",
        "decision_maker_dossier": {
            "name": "Ford Prefect",
            "relationship": "Executor",
            "heir_count": 1,
            "occupancy": "vacant"
        },
        "recommended_outreach_strategy": "Direct cash offer"
    }
    ara_output = {
        "authority_tier": "Tier 1: Court Certified",
        "court_oversight_model": "Independent",
        "can_execute_psa": True,
        "court_confirmation_required": False,
        "statutory_basis": "RCW 11.68",
        "legal_summary": "Nonintervention Powers Granted"
    }
    osa_output = {
        "composite_score": 95,
        "priority_band": "Priority A",
        "deal_friction_score": 5,
        "sla_assignment": "Urgent 4-Hour Flash Alert"
    }
    qca_output = {"qc_certification": "Certified Pass"}

    pof = ProbateOpportunityFileBuilder.build(
        opp_id, pia_output, pra_output, oia_output, cia_output, ara_output, osa_output, qca_output, raw_filing
    )

    assert pof.opportunity_id == opp_id
    assert pof.property_profile.apn == "0123456789"
    assert pof.ownership_profile.net_distributable_equity == 675000.0
    assert pof.control_profile.primary_decision_maker == "Ford Prefect"
    assert pof.authority_profile.authority_tier == "Tier 1: Court Certified"
    assert pof.opportunity_profile.composite_viability_score == 95

    # Exporters
    crm_payload = POFExporter.to_crm_webhook_payload(pof)
    assert crm_payload["opportunity_id"] == opp_id
    assert crm_payload["property_profile"]["apn"] == "0123456789"

    html = POFExporter.to_institutional_html(pof)
    assert "<!DOCTYPE html>" in html
    assert "42 GALAXY WAY" in html
    assert "Priority A" in html

    blocks = POFExporter.to_notion_blocks(pof)
    assert len(blocks) > 5
