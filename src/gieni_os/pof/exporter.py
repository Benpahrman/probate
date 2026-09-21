"""
Gieni OS POF Exporter
Renders canonical POF records into CRM Webhook JSON, institutional HTML Executive Dossiers, and Notion block trees.
"""

import html
from typing import Dict, Any, List
from gieni_os.pof.builder import ProbateOpportunityFile

class POFExporter:
    @staticmethod
    def to_crm_webhook_payload(pof: ProbateOpportunityFile) -> Dict[str, Any]:
        return {
            "opportunity_id": pof.opportunity_id,
            "docket_number": pof.docket_number,
            "estate_name": pof.estate_name,
            "qc_status": pof.evidence_package.qc_certification_stamp,
            "property_profile": {
                "apn": pof.property_profile.apn,
                "situs_address": pof.property_profile.situs_address,
                "city_state_zip": pof.property_profile.city_state_zip,
                "avm_market_estimate": pof.property_profile.avm_market_estimate,
                "total_assessed_value": pof.property_profile.total_assessed_value,
                "landuse": pof.property_profile.landuse,
                "pas_score": pof.property_profile.pas_score
            },
            "ownership_profile": {
                "legal_title_vesting": pof.ownership_profile.legal_title_vesting,
                "senior_mortgage_balance": pof.ownership_profile.senior_mortgage_balance,
                "net_distributable_equity": pof.ownership_profile.net_distributable_equity,
                "net_equity_pct": pof.ownership_profile.net_equity_pct,
                "target_wholesale_mao": pof.ownership_profile.target_wholesale_mao
            },
            "control_profile": {
                "primary_decision_maker": pof.control_profile.primary_decision_maker,
                "relationship_to_decedent": pof.control_profile.relationship_to_decedent,
                "control_archetype": pof.control_profile.control_archetype,
                "occupancy": pof.control_profile.occupancy
            },
            "authority_profile": {
                "authority_tier": pof.authority_profile.authority_tier,
                "can_execute_psa": pof.authority_profile.can_execute_psa,
                "statutory_power_scope": pof.authority_profile.statutory_power_scope,
                "court_oversight_model": pof.authority_profile.court_oversight_model
            },
            "opportunity_profile": {
                "composite_score": pof.opportunity_profile.composite_viability_score,
                "priority_tier": pof.opportunity_profile.priority_tier,
                "deal_friction_score": pof.opportunity_profile.deal_friction_score,
                "dispatch_sla": pof.opportunity_profile.dispatch_sla
            },
            "recommended_action": {
                "strategy": pof.recommended_action.transaction_strategy,
                "channel": pof.recommended_action.first_touch_channel,
                "script": pof.recommended_action.conversational_framing_script
            }
        }

    @staticmethod
    def to_institutional_html(pof: ProbateOpportunityFile) -> str:
        def esc(val: Any) -> str:
            return html.escape(str(val)) if val is not None else ""

        opp_id = esc(pof.opportunity_id)
        situs = esc(pof.property_profile.situs_address)
        docket = esc(pof.docket_number)
        estate = esc(pof.estate_name)
        tier = esc(pof.opportunity_profile.priority_tier)
        apn = esc(pof.property_profile.apn)
        vesting = esc(pof.ownership_profile.legal_title_vesting)
        dm = esc(pof.control_profile.primary_decision_maker)
        rel = esc(pof.control_profile.relationship_to_decedent)
        arch = esc(pof.control_profile.control_archetype)
        occ = esc(pof.control_profile.occupancy.capitalize()) if pof.control_profile.occupancy else ""
        auth_tier = esc(pof.authority_profile.authority_tier)
        power_scope = esc(pof.authority_profile.statutory_power_scope)
        oversight = esc(pof.authority_profile.court_oversight_model)
        strat = esc(pof.recommended_action.transaction_strategy)
        channel = esc(pof.recommended_action.first_touch_channel)
        script = esc(pof.recommended_action.conversational_framing_script)
        qc_stamp = esc(pof.evidence_package.qc_certification_stamp)
        deed_inst = esc(pof.evidence_package.recorded_deed_instrument)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Probate Opportunity Dossier | {opp_id}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; color: #1e293b; background: #f8fafc; padding: 40px; }}
  .card {{ background: #ffffff; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.06); padding: 32px; max-width: 900px; margin: 0 auto; border: 1px solid #e2e8f0; }}
  .header {{ border-bottom: 2px solid #0f172a; padding-bottom: 20px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: flex-start; }}
  .badge {{ background: #0ea5e9; color: white; padding: 4px 12px; border-radius: 9999px; font-weight: 700; font-size: 14px; text-transform: uppercase; }}
  .grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-bottom: 24px; }}
  .section-title {{ font-size: 16px; font-weight: 700; color: #0f172a; text-transform: uppercase; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px; margin-bottom: 12px; }}
  .val {{ font-weight: 600; color: #0f172a; }}
  .callout {{ background: #f0fdf4; border-left: 4px solid #22c55e; padding: 16px; border-radius: 4px; margin-top: 20px; }}
</style>
</head>
<body>
<div class="card">
  <div class="header">
    <div>
      <div style="font-size: 12px; font-weight: 700; letter-spacing: 0.1em; color: #64748b;">GIENI ACQUISITION DECISION INTELLIGENCE</div>
      <h1 style="margin: 4px 0; font-size: 26px;">{situs}</h1>
      <div style="color: #64748b;">Docket: {docket} • {estate}</div>
    </div>
    <div>
      <span class="badge">{tier}</span>
      <div style="text-align: right; font-size: 28px; font-weight: 800; color: #0284c7; margin-top: 4px;">{pof.opportunity_profile.composite_viability_score}<span style="font-size: 16px; font-weight: 500; color: #64748b;">/100</span></div>
    </div>
  </div>

  <div class="grid">
    <div>
      <div class="section-title">Property Profile</div>
      <div>APN: <span class="val">{apn}</span></div>
      <div>AVM Market Value: <span class="val">${pof.property_profile.avm_market_estimate:,.0f}</span></div>
      <div>Assessed Value: <span class="val">${pof.property_profile.total_assessed_value:,.0f}</span></div>
      <div>PAS Match Score: <span class="val">{pof.property_profile.pas_score:.1f}%</span></div>
    </div>
    <div>
      <div class="section-title">Ownership & Equity</div>
      <div>Vesting: <span class="val">{vesting}</span></div>
      <div>Senior Mortgages: <span class="val">${pof.ownership_profile.senior_mortgage_balance:,.0f}</span></div>
      <div>Net Protected Equity: <span class="val" style="color: #16a34a;">${pof.ownership_profile.net_distributable_equity:,.0f} ({pof.ownership_profile.net_equity_pct*100:.1f}%)</span></div>
      <div>Target Wholesaler MAO: <span class="val">${pof.ownership_profile.target_wholesale_mao:,.0f}</span></div>
    </div>
  </div>

  <div class="grid">
    <div>
      <div class="section-title">Control Profile</div>
      <div>Decision-Maker: <span class="val">{dm}</span></div>
      <div>Relationship: <span class="val">{rel}</span></div>
      <div>Control Model: <span class="val">{arch}</span></div>
      <div>Occupancy: <span class="val">{occ}</span></div>
    </div>
    <div>
      <div class="section-title">Authority Profile (RCW Title 11)</div>
      <div>Authority Tier: <span class="val">{auth_tier}</span></div>
      <div>Statutory Powers: <span class="val">{power_scope}</span></div>
      <div>Court Oversight: <span class="val">{oversight}</span></div>
      <div>Can Execute PSA: <span class="val" style="color: #16a34a;">YES</span></div>
    </div>
  </div>

  <div class="callout">
    <div style="font-weight: 700; color: #166534;">RECOMMENDED ACQUISITION PLAYBOOK</div>
    <div>Strategy: <span class="val">{strat}</span> • Channel: <span class="val">{channel}</span></div>
    <div style="margin-top: 8px; font-style: italic;">"{script}"</div>
  </div>

  <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #94a3b8; display: flex; justify-content: space-between;">
    <div>QC Stamp: {qc_stamp} • Deed Instrument: {deed_inst}</div>
    <div>GIENI CONFIDENTIAL & PROPRIETARY</div>
  </div>
</div>
</body>
</html>
"""

    @staticmethod
    def to_notion_blocks(pof: ProbateOpportunityFile) -> List[Dict[str, Any]]:
        def h2(text):
            return {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": text}}]}}
        def p(text, bold=False):
            return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": text}, "annotations": {"bold": bold}}]}}
        def b_item(text):
            return {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": text}}]}}

        blocks = [
            h2("1. Property Profile"),
            b_item(f"APN: {pof.property_profile.apn} | Situs: {pof.property_profile.situs_address}"),
            b_item(f"AVM Market Estimate: ${pof.property_profile.avm_market_estimate:,.0f}"),
            h2("2. Ownership & Equity"),
            b_item(f"Vesting: {pof.ownership_profile.legal_title_vesting}"),
            b_item(f"Net Distributable Equity: ${pof.ownership_profile.net_distributable_equity:,.0f} ({pof.ownership_profile.net_equity_pct*100:.1f}%)"),
            h2("3. Control Profile"),
            b_item(f"Primary Decision-Maker: {pof.control_profile.primary_decision_maker} ({pof.control_profile.relationship_to_decedent})"),
            h2("4. Authority Profile (RCW Title 11)"),
            b_item(f"Authority Tier: {pof.authority_profile.authority_tier}"),
            b_item(f"Statutory Powers: {pof.authority_profile.statutory_power_scope}"),
            h2("5. Recommended Action"),
            p(f"Strategy: {pof.recommended_action.transaction_strategy}", True),
            p(f"Script Angle: {pof.recommended_action.conversational_framing_script}")
        ]
        return blocks
