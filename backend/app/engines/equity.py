from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class EquityTier(str, Enum):
    EXCEPTIONAL = "EXCEPTIONAL"              # >= 70.0% net equity spread
    HIGH = "HIGH"                            # 50.0% - 69.99% net equity spread
    MODERATE = "MODERATE"                    # 30.0% - 49.99% net equity spread
    LOW_OR_UNDERWATER = "LOW_OR_UNDERWATER"  # < 30.0% net equity spread (Disqualified)


class EncumbranceWaterfallInputs(BaseModel):
    gross_market_value: float = Field(..., ge=0.0, description="Conservative AVM or tax assessment baseline")
    open_mortgage_balance: float = Field(default=0.0, ge=0.0, description="Senior note principal balance")
    junior_mortgages_and_helocs: float = Field(default=0.0, ge=0.0, description="Open 2nd/3rd liens and revolving credit lines")
    delinquent_real_property_taxes: float = Field(default=0.0, ge=0.0, description="Tax arrears with interest and penalties")
    municipal_and_mechanics_liens: float = Field(default=0.0, ge=0.0, description="Code violations, weed, and contractor liens")
    federal_and_state_tax_liens: float = Field(default=0.0, ge=0.0, description="IRS and state revenue claims against decedent")
    merp_statutory_claim: float = Field(default=0.0, ge=0.0, description="Medicaid Estate Recovery Program healthcare lien")
    estimated_probate_statutory_fees: float = Field(default=0.0, ge=0.0, description="Clerk fees, publication, and fiduciary commissions")
    recorded_creditor_claims: float = Field(default=0.0, ge=0.0, description="Valid claims filed against the estate docket")

    model_config = ConfigDict(extra="forbid")


class EquityWaterfallResult(BaseModel):
    gross_market_value: float
    total_encumbrances: float
    net_actionable_equity: float
    equity_percentage: float
    tier: EquityTier
    gate_3_passed: bool
    is_disqualified: bool
    disqualification_reason: str | None = None


def compute_net_actionable_equity(inputs: EncumbranceWaterfallInputs) -> EquityWaterfallResult:
    """Audits the legal and debt encumbrance waterfall to isolate actionable net equity.
    
    Gate 3 Standard: Net Actionable Equity must be >= $50,000 AND Equity Percentage >= 30.0%.
    """
    total_encumbrances = round(
        inputs.open_mortgage_balance +
        inputs.junior_mortgages_and_helocs +
        inputs.delinquent_real_property_taxes +
        inputs.municipal_and_mechanics_liens +
        inputs.federal_and_state_tax_liens +
        inputs.merp_statutory_claim +
        inputs.estimated_probate_statutory_fees +
        inputs.recorded_creditor_claims,
        2
    )

    net_equity = round(inputs.gross_market_value - total_encumbrances, 2)
    
    if inputs.gross_market_value > 0.0:
        equity_pct = round(net_equity / inputs.gross_market_value, 4)
    else:
        equity_pct = 0.0

    # Classify Equity Tier
    if equity_pct >= 0.70:
        tier = EquityTier.EXCEPTIONAL
    elif equity_pct >= 0.50:
        tier = EquityTier.HIGH
    elif equity_pct >= 0.30:
        tier = EquityTier.MODERATE
    else:
        tier = EquityTier.LOW_OR_UNDERWATER

    # Validate Gate 3 Economic Viability
    gate_3_passed = True
    disqualification_reason = None

    if net_equity < 50000.0:
        gate_3_passed = False
        disqualification_reason = f"Net equity ${net_equity:,.2f} is below the $50,000 statutory minimum threshold."
    elif equity_pct < 0.30:
        gate_3_passed = False
        disqualification_reason = f"Equity percentage {equity_pct * 100:.2f}% is below the 30.0% viable minimum threshold."

    return EquityWaterfallResult(
        gross_market_value=inputs.gross_market_value,
        total_encumbrances=total_encumbrances,
        net_actionable_equity=net_equity,
        equity_percentage=equity_pct,
        tier=tier,
        gate_3_passed=gate_3_passed,
        is_disqualified=not gate_3_passed,
        disqualification_reason=disqualification_reason
    )
