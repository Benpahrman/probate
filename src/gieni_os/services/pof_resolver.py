from gieni_os.database.models import OpportunityModel
from gieni_os.pof.builder import (
    ProbateOpportunityFile,
    PropertyProfile,
    OwnershipProfile,
    ControlProfile,
    AuthorityProfile,
    OpportunityProfile,
    RiskProfile,
    EvidencePackage,
    RecommendedAction
)

class POFDataResolver:
    ASSESSOR_CACHE = {
        "Pierce": {"status": "ACTIVE", "median_assessed": 450000.0},
        "King": {"status": "ACTIVE", "median_assessed": 750000.0},
        "Thurston": {"status": "ACTIVE", "median_assessed": 420000.0},
    }

    @staticmethod
    def lookup_county_assessor(county_id: str, apn: str):
        c_name = "Pierce" if "pierce" in county_id.lower() else ("King" if "king" in county_id.lower() else ("Thurston" if "thurston" in county_id.lower() else "Pierce"))
        info = POFDataResolver.ASSESSOR_CACHE.get(c_name, {"status": "ACTIVE", "median_assessed": 450000.0})
        return info

    @staticmethod
    def resolve_opportunity_pof(opp: OpportunityModel) -> ProbateOpportunityFile:
        # In a real system, this would aggregate data from MemoryEntryModel, CountyModel, etc.
        # For now, we populate it with safe default values or values from the OpportunityModel.
        
        decedent_name = opp.case.decedent if opp.case else "Unknown Decedent"
        
        property_profile = PropertyProfile(
            apn="UNKNOWN-APN",
            situs_address="Address Pending Verification",
            city_state_zip="Pending",
            legal_description="Pending Legal Description",
            avm_market_estimate=0.0,
            total_assessed_value=0.0,
            land_value=0.0,
            improvement_value=0.0,
            landuse="Pending",
            pas_score=0.0
        )
        
        ownership_profile = OwnershipProfile(
            legal_title_vesting="Pending Verification",
            ownership_complexity_score=50,
            net_distributable_equity=50000.0,
            net_equity_pct=50.0,
            target_wholesale_mao=40000.0,
            senior_mortgage_balance=0.0,
            municipal_liens=0.0,
            estimated_repairs=0.0,
            is_free_and_clear=False
        )
        
        control_profile = ControlProfile(
            control_archetype="Personal Representative",
            primary_decision_maker=None, # Rule 4: No fake names
            relationship_to_decedent="Unknown",
            heir_count=0,
            occupancy="UNKNOWN"
        )
        
        is_tier_1 = "Tier 1" in (opp.authority_status or "")
        authority_tier = "TIER_1" if is_tier_1 else ("TIER_2" if "Tier 2" in (opp.authority_status or "") else (opp.authority_status or "UNKNOWN"))
        can_execute_psa = is_tier_1 or (opp.authority_status == "Tier 1: Court Certified")
        authority_profile = AuthorityProfile(
            authority_tier=authority_tier,
            court_oversight_model="NONINTERVENTION" if is_tier_1 else "UNKNOWN",
            can_execute_psa=can_execute_psa,
            court_confirmation_required=not is_tier_1,
            statutory_basis="RCW 11.68.110" if is_tier_1 else "RCW 11.28",
            statutory_power_scope="FULL_INDEPENDENT" if is_tier_1 else "LIMITED"
        )
        
        opportunity_profile = OpportunityProfile(
            composite_viability_score=opp.score,
            priority_tier=opp.priority,
            deal_friction_score=50,
            dispatch_sla="STANDARD"
        )
        
        risk_profile = RiskProfile(
            overall_deal_risk_classification="MODERATE",
            foreclosure_acceleration_risk=False
        )
        
        evidence_package = EvidencePackage(
            qc_certification_stamp="PENDING",
            recorded_deed_instrument="PENDING",
            source_dockets=["Docket 1"]
        )
        
        recommended_action = RecommendedAction(
            transaction_strategy="HOLD",
            first_touch_channel="DIRECT_MAIL",
            conversational_framing_script="Standard Probate Notice"
        )
        
        return ProbateOpportunityFile(
            opportunity_id=opp.id,
            docket_number=opp.case.case_number if opp.case else "UNKNOWN",
            estate_name=f"Estate of {decedent_name}",
            property_profile=property_profile,
            ownership_profile=ownership_profile,
            control_profile=control_profile,
            authority_profile=authority_profile,
            opportunity_profile=opportunity_profile,
            risk_profile=risk_profile,
            evidence_package=evidence_package,
            recommended_action=recommended_action
        )
