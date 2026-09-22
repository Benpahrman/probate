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


ENCUMBRANCE_FIELDS: tuple[str, ...] = (
    "open_mortgage_balance",
    "junior_mortgages_and_helocs",
    "delinquent_real_property_taxes",
    "municipal_and_mechanics_liens",
    "federal_and_state_tax_liens",
    "merp_statutory_claim",
    "estimated_probate_statutory_fees",
    "recorded_creditor_claims",
)

EQUITY_TIER_THRESHOLDS: tuple[tuple[float, EquityTier], ...] = (
    (0.70, EquityTier.EXCEPTIONAL),
    (0.50, EquityTier.HIGH),
    (0.30, EquityTier.MODERATE),
)


def _sum_encumbrances(inputs: EncumbranceWaterfallInputs) -> float:
    return round(sum(getattr(inputs, field, 0.0) for field in ENCUMBRANCE_FIELDS), 2)


def _classify_equity_tier(equity_pct: float) -> EquityTier:
    for threshold, tier in EQUITY_TIER_THRESHOLDS:
        if equity_pct >= threshold:
            return tier
    return EquityTier.LOW_OR_UNDERWATER


def _validate_gate_3(net_equity: float, equity_pct: float) -> tuple[bool, str | None]:
    if net_equity < 50000.0:
        return False, f"Net equity ${net_equity:,.2f} is below the $50,000 statutory minimum threshold."
    if equity_pct < 0.30:
        return False, f"Equity percentage {equity_pct * 100:.2f}% is below the 30.0% viable minimum threshold."
    return True, None


def compute_net_actionable_equity(inputs: EncumbranceWaterfallInputs) -> EquityWaterfallResult:
    """Audits the legal and debt encumbrance waterfall to isolate actionable net equity.
    
    Gate 3 Standard: Net Actionable Equity must be >= $50,000 AND Equity Percentage >= 30.0%.
    """
    total_encumbrances = _sum_encumbrances(inputs)
    net_equity = round(inputs.gross_market_value - total_encumbrances, 2)
    equity_pct = round(net_equity / inputs.gross_market_value, 4) if inputs.gross_market_value > 0.0 else 0.0
    tier = _classify_equity_tier(equity_pct)
    gate_3_passed, disqualification_reason = _validate_gate_3(net_equity, equity_pct)

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
