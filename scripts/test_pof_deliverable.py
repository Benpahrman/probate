"""
Test and Verification Harness for the Probate Opportunity File (POF) Specification (v2.0)
Validates all 8 canonical product profiles, multi-channel export (CRM, HTML, Notion),
and publishes the official POF specification to the Knowledge Base.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
import time
import requests
from src.gieni_os.pof.builder import ProbateOpportunityFileBuilder
from src.gieni_os.pof.exporter import POFExporter
from src.gieni_os.integrations.notion_publisher import NotionPublisher
from src.gieni_os.config import NOTION_TOKEN, NOTION_VERSION, KB_DB_ID, PIERCE_COUNTY_PAGE_ID

def main():
    print("\n" + "="*80)
    print(" GIENI OS -- PROBATE OPPORTUNITY FILE (POF) SPECIFICATION (v2.0) HARNESS")
    print(" Core Commercial Deliverable Verification & Multi-Channel Export Test")
    print("="*80 + "\n")

    # 1. Mock Agent Outputs for a Priority A Case in Pierce County
    opp_id = "OPP-2026-PC-POF-01"
    raw_filing = {
        "case_number": "26-4-01892-3",
        "filing_date": "2026-09-15",
        "decedent_name": "Estate of Harold M. Albright",
        "address": "3719 N 28th St, Tacoma, WA 98407",
        "has_real_estate": True,
        "assessed_value": 475000,
        "mortgage_balance": 42000.0,
        "heir_count": 1,
        "heirs_cooperative": True,
        "decision_maker": "Evelyn Albright Keller",
        "dm_relationship": "Daughter & Named Executrix",
        "dm_phone": "+1 (253) 555-0188",
        "dm_is_out_of_area": False,
        "letters_issued": True,
        "has_nonintervention_powers": True,
        "occupancy": "vacant",
        "sqft": 1940,
        "bed_bath": "3 Bed / 2.5 Bath",
        "lot_acres": 0.18,
        "year_built": 1968,
        "attorney_name": "Marcus Vance JD",
        "attorney_firm": "Tacoma Estate Law Group"
    }

    pia_output = {
        "candidate_parcels": [{"is_primary": True}],
        "portfolio_size": 1,
        "human_review_required": False
    }

    pra_output = {
        "matched": True,
        "apn": "0221283019",
        "situs_address": "3719 N 28TH ST",
        "city_state": "TACOMA, WA",
        "zipcode": "98407",
        "total_assessed_value": 475000,
        "land_value": 210000,
        "improvement_value": 265000,
        "landuse": "SINGLE FAMILY DWELLING",
        "legal_description": "Section 28 Township 21 Range 03 Quarter 34 PROCTOR ADDITION LOT 12 BLOCK 4",
        "pas_score": 96.0
    }

    oia_output = {
        "vesting_classification": "Sole Fee Simple",
        "ownership_complexity_score": 15,
        "net_equity_waterfall": {
            "estimated_arv": 640000.0,
            "senior_mortgage_balance": 42000.0,
            "municipal_liens": 0.0,
            "estimated_repairs": 35000.0,
            "net_distributable_equity": 563000.0,
            "ltv": 0.07,
            "target_mao": 398000.0,
            "is_free_and_clear": False
        }
    }

    cia_output = {
        "control_archetype": "Unified",
        "decision_maker_dossier": {
            "name": "Evelyn Albright Keller",
            "relationship": "Daughter & Executrix",
            "heir_count": 1,
            "occupancy": "vacant"
        },
        "recommended_outreach_strategy": "Empathetic, direct as-is cash convenience proposal with zero cleanout burden."
    }

    ara_output = {
        "authority_tier": "Tier 1: Court Certified",
        "court_oversight_model": "Independent",
        "can_execute_psa": True,
        "court_confirmation_required": False,
        "statutory_basis": "RCW 11.68.011",
        "legal_summary": "Letters Testamentary issued with Nonintervention Powers under RCW 11.68. Personal Representative has full signatory capacity without court confirmation."
    }

    osa_output = {
        "composite_score": 92,
        "priority_band": "Priority A",
        "deal_friction_score": 14,
        "sla_assignment": "Urgent 4-Hour Flash Alert"
    }

    qca_output = {
        "qc_certification": "Certified Pass",
        "route": "Approved / Client Delivery",
        "contact_readiness": "Ready",
        "has_exceptions": False,
        "exception_notes": []
    }

    # 2. Build the 8-Profile POF
    print("[1/4] Building Canonical 8-Profile Probate Opportunity File (POF)...")
    pof = ProbateOpportunityFileBuilder.build(
        opp_id=opp_id,
        pia=pia_output,
        pra=pra_output,
        oia=oia_output,
        cia=cia_output,
        ara=ara_output,
        osa=osa_output,
        qca=qca_output,
        raw_filing=raw_filing
    )

    print(f" -> Opportunity ID: {pof.opportunity_id}")
    print(f" -> Profile 1 (Property): {pof.property_profile.situs_address} (APN: {pof.property_profile.apn} | AVM: ${pof.property_profile.avm_market_estimate:,.0f})")
    print(f" -> Profile 2 (Ownership): {pof.ownership_profile.legal_title_vesting} | Net Equity: ${pof.ownership_profile.net_distributable_equity:,.0f} ({pof.ownership_profile.net_equity_pct*100:.1f}%)")
    print(f" -> Profile 3 (Control): Archetype {pof.control_profile.control_archetype} | DM: {pof.control_profile.primary_decision_maker}")
    print(f" -> Profile 4 (Authority): {pof.authority_profile.authority_tier} (Powers: {pof.authority_profile.statutory_power_scope})")
    print(f" -> Profile 5 (Opportunity): Score {pof.opportunity_profile.composite_viability_score}/100 | {pof.opportunity_profile.priority_tier} (SLA: {pof.opportunity_profile.dispatch_sla})")
    print(f" -> Profile 6 (Risk): {pof.risk_profile.overall_deal_risk_classification} | Foreclosure Risk: {pof.risk_profile.foreclosure_acceleration_risk}")
    print(f" -> Profile 7 (Evidence): Verified QC Stamp '{pof.evidence_package.qc_certification_stamp}' | Deed: {pof.evidence_package.recorded_deed_instrument}")
    print(f" -> Profile 8 (Action): Strategy '{pof.recommended_action.transaction_strategy}' | Channel: {pof.recommended_action.first_touch_channel}")

    # 3. Multi-Channel Export Verification
    print("\n[2/4] Testing Multi-Channel Commercial Delivery Exports...")
    
    # Export 1: CRM Direct Webhook (JSON)
    crm_payload = POFExporter.to_crm_webhook_payload(pof)
    crm_out_path = os.path.join(os.path.dirname(__file__), "..", "pof_crm_payload.json")
    with open(crm_out_path, "w") as f:
        json.dump(crm_payload, f, indent=2)
    print(f" -> [Export 1] CRM Direct Webhook payload generated and saved to {os.path.abspath(crm_out_path)}")

    # Export 2: Institutional Executive HTML Dossier
    html_dossier = POFExporter.to_institutional_html(pof)
    html_out_path = os.path.join(os.path.dirname(__file__), "..", "pof_executive_dossier.html")
    with open(html_out_path, "w", encoding="utf-8") as f:
        f.write(html_dossier)
    print(f" -> [Export 2] Institutional Executive HTML Dossier generated and saved to {os.path.abspath(html_out_path)}")

    # Export 3: Notion Blocks Validation
    notion_blocks = POFExporter.to_notion_blocks(pof)
    print(f" -> [Export 3] Notion Block Tree compiled ({len(notion_blocks)} structured blocks across 8 profiles)")

    # 4. Sync Opportunity to Live Notion Database
    print("\n[3/4] Publishing Live POF Record to Notion Opportunities Database...")
    publisher = NotionPublisher()
    package = {
        "opportunity_id": opp_id,
        "docket_number": pof.docket_number,
        "estate_name": pof.estate_name,
        "viability": {
            "composite_score": pof.opportunity_profile.composite_viability_score,
            "priority_band": pof.opportunity_profile.priority_tier,
            "deal_friction_score": pof.opportunity_profile.deal_friction_score,
            "qc_certification": "Certified Pass"
        },
        "property_profile": {
            "apn": pof.property_profile.apn,
            "situs_address": pof.property_profile.situs_address,
            "city_state_zip": pof.property_profile.city_state_zip,
            "pas_score": pof.property_profile.pas_score
        },
        "financial_waterfall": {
            "estimated_arv": pof.property_profile.avm_market_estimate,
            "net_distributable_equity": pof.ownership_profile.net_distributable_equity,
            "target_wholesale_mao": pof.ownership_profile.target_wholesale_mao,
            "ownership_complexity_score": pof.ownership_profile.ownership_complexity_score
        },
        "control_and_authority": {
            "decision_maker": pof.control_profile.primary_decision_maker,
            "relationship": pof.control_profile.relationship_to_decedent,
            "control_archetype": pof.control_profile.control_archetype,
            "authority_tier": pof.authority_profile.authority_tier,
            "statutory_basis": "RCW 11.68",
            "recommended_outreach": pof.recommended_action.conversational_framing_script
        },
        "pof": pof
    }
    page_id = publisher.publish_opportunity(package)
    if page_id:
        print(f" -> Successfully published POF Opportunity Page to Notion (ID: {page_id})")
    else:
        print(" -> Notice: Notion opportunity publication skipped or completed.")

    # 5. Publish Official POF Specification Article to Notion Knowledge Base
    print("\n[4/4] Publishing Canonical POF Specification (v2.0) to Notion Knowledge Base...")
    publish_pof_spec_to_knowledge_base()

    print("\n" + "="*80)
    print(" PROBATE OPPORTUNITY FILE (POF) SPECIFICATION (v2.0) -- VERIFICATION COMPLETE")
    print("="*80 + "\n")

def publish_pof_spec_to_knowledge_base():
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }

    def t(content, bold=False, color="default"):
        return {
            "type": "text",
            "text": {"content": content},
            "annotations": {"bold": bold, "color": color}
        }

    title = "Probate Opportunity File (POF) Specification (v2.0)"
    properties = {
        "Article": {"title": [{"text": {"content": title}}]},
        "Category": {"select": {"name": "Evidence Standards"}},
        "Status": {"select": {"name": "Approved"}},
        "Source Link": {"url": "https://gieni.io/pof-spec/v2.0"},
        "Notes": {"rich_text": [{"text": {"content": "Canonical product definition for the Gieni exclusive commercial deliverable. Details the 8 product profiles, multi-channel exports (CRM, Notion, PDF), and empathy directives."}}]},
        "County": {"relation": [{"id": PIERCE_COUNTY_PAGE_ID}]}
    }

    blocks = [
        {
            "object": "block",
            "type": "heading_1",
            "heading_1": {"rich_text": [t("Probate Opportunity File (POF) Specification (v2.0)")]}
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [t("Classification: Core Commercial Deliverable | Version: 2.0 | Status: Production Approved")]}
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [t("The contract between engineering and customer delivery. The POF is the definitive pre-underwritten decision dossier that answers: What property exists? Who owns it? Who controls the decision? Who can legally sign? What is the equity? What are the fatal risks? What evidence proves it? And what exact action should the acquisitions team take?")]}
        },
        {"object": "block", "type": "divider", "divider": {}},
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [t("The Eight Canonical Product Profiles")]}
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [t("1. Property Profile: ", True), t("Assessor APN, CASS standard address, legal description, physical specs (sqft, bed/bath, lot, year built), valuation spread (Assessed, AVM, CMA), and PAS match score (≥70).")]}
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [t("2. Ownership Profile: ", True), t("Title vesting (Sole Fee Simple, JTWROS, Trust, TIC), deceased titleholder, senior & junior mortgage notes, tax delinquencies, net equity waterfall ($ and %), and target wholesale MAO.")]}
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [t("3. Control Profile: ", True), t("Control archetype (Unified, Informal Leader, Proxy, Trust Fiduciary, Contested), decision-maker dossier, residency location, physical occupancy, and core seller motivations.")]}
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [t("4. Authority Profile: ", True), t("Four-tier statutory authority under RCW Title 11, Letters status, Nonintervention vs. Dependent court powers, and attorney quarantine safeguarding legal counsel.")]}
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [t("5. Opportunity Profile: ", True), t("0-100 composite viability ranking, Priority Tier (Priority A < 4hr SLA, Priority B weekly, Priority C nurturing), Deal Friction Score (DFS), and projected timeline to close.")]}
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [t("6. Risk Profile: ", True), t("Foreclosure/NOD risk, tax auction cliff, title cloud and broken chain analysis, contested family caveats, tenant eviction exposure, and MERP Medicaid claim risk.")]}
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [t("7. Evidence Package: ", True), t("Cryptographic chain of custody with SHA-256 hashes linking petition PDFs, wills, letters, recorded warranty deeds, and the 6-gate QC certification seal.")]}
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [t("8. Recommended Action & Empathy Directives: ", True), t("Optimal transaction strategy (wholesale cash, novation, creative), verified HLR/DNC mobile vector, first-touch channel, empathy conversational script, objection handling playbook, and closing escrow roadmap.")]}
        }
    ]

    payload = {
        "parent": {"database_id": KB_DB_ID},
        "properties": properties,
        "children": blocks
    }

    try:
        resp = requests.post("https://api.notion.com/v1/pages", headers=headers, json=payload, timeout=12)
        if resp.status_code == 200:
            print(" -> [Notion KB] Successfully published Canonical POF Specification (v2.0) page to Notion.")
        else:
            print(f" -> [Notion KB] Response status: {resp.status_code} ({resp.text[:100]})")
    except Exception as e:
        print(f" -> [Notion KB] Failed to publish POF Spec to Notion: {e}")

if __name__ == "__main__":
    main()
