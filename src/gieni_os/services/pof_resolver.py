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
    ASSESSOR_CACHE = {}

    @staticmethod
    def lookup_county_assessor(county_id: str, apn: str):
        return {"status": "UNCONFIGURED", "median_assessed": 0.0}

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
        
        authority_profile = AuthorityProfile(
            authority_tier="UNKNOWN",
            court_oversight_model="UNKNOWN",
            can_execute_psa=False,
            court_confirmation_required=True,
            statutory_basis="RCW 11.68.110",
            statutory_power_scope="UNKNOWN"
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
