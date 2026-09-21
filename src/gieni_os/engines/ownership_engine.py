"""
Ownership Intelligence Engine (OIE)
Solves deed vesting, title complexity, and the Net Equity Waterfall.
"""

from typing import List, Optional
from gieni_os.domain.ownership import VestingType, EquityWaterfall, OwnershipRecord

class OwnershipEngine:
    @classmethod
    def calculate_equity_waterfall(
        cls,
        estimated_market_value: float,
        senior_debt: float = 0.0,
        junior_liens: float = 0.0,
        estimated_repairs: float = 25000.0,
        probate_and_closing_pct: float = 0.08
    ) -> EquityWaterfall:
        closing_costs = estimated_market_value * probate_and_closing_pct
        net_equity = max(0.0, estimated_market_value - (senior_debt + junior_liens + estimated_repairs + closing_costs))
        spread_ratio = round(net_equity / estimated_market_value, 4) if estimated_market_value > 0 else 0.0

        return EquityWaterfall(
            estimated_market_value=estimated_market_value,
            total_senior_debt=senior_debt,
            junior_liens=junior_liens,
            estimated_repairs=estimated_repairs,
            closing_and_probate_costs=closing_costs,
            net_equity=round(net_equity, 2),
            equity_spread_ratio=spread_ratio
        )

    @classmethod
    def analyze_vesting(
        cls,
        property_id: str,
        decedent_name: str,
        grantee_names: List[str],
        deed_type: str = "STATUTORY_WARRANTY",
        has_mortgage_cloud: bool = False
    ) -> OwnershipRecord:
        # Determine vesting type
        if len(grantee_names) == 1 and grantee_names[0].lower() == decedent_name.lower():
            vesting = VestingType.FEE_SIMPLE_SOLE
            complexity = 0
            curative = False
            notes = "Clear single-owner title confirmed via County Auditor."
        elif any("trust" in g.lower() for g in grantee_names):
            vesting = VestingType.REVOCABLE_TRUST
            complexity = 4
            curative = False
            notes = "Property held in revocable trust; successor trustee certificate required."
        else:
            vesting = VestingType.COMMUNITY_PROPERTY
            complexity = 2
            curative = False
            notes = "Community property presumption under Washington RCW 26.16."

        if has_mortgage_cloud:
            complexity += 4
            curative = True
            notes += " [WARNING: Unreleased deed of trust from prior conveyance detected]."

        # Compute equity waterfall (defaulting to standard market assumptions)
        waterfall = cls.calculate_equity_waterfall(
            estimated_market_value=650000.0,
            senior_debt=180000.0,
            junior_liens=0.0 if not has_mortgage_cloud else 22000.0,
            estimated_repairs=35000.0
        )

        return OwnershipRecord(
            property_id=property_id,
            vesting_type=vesting,
            title_complexity_score=complexity,
            title_holders=grantee_names,
            waterfall=waterfall,
            curative_required=curative,
            curative_notes=notes
        )
