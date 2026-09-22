from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import VestingType


class OwnershipComplexityInputs(BaseModel):
    vesting_type: VestingType
    heir_count: int = Field(default=1, ge=1, description="Count of statutory intestate heirs or devisees")
    ancestor_probates_unresolved: int = Field(default=0, ge=0, description="Generations of unprobated conveyances in title chain")
    has_unrecorded_trust_reference: bool = Field(default=False, description="Deed references trust lacking public certificate")
    has_title_cloud_or_wild_deed: bool = Field(default=False, description="Unbroken chain gap or competing conveyance")
    has_foreign_or_ancillary_jurisdiction: bool = Field(default=False, description="Requires out-of-state ancillary filings")

    model_config = ConfigDict(extra="forbid")


class OwnershipComplexityResult(BaseModel):
    complexity_score: int = Field(..., ge=10, le=100)
    base_score: int
    penalties_applied: int
    title_clearance_strategy: str


VESTING_ARCHETYPES: dict[VestingType, tuple[int, str]] = {
    VestingType.SOLE_FEE_SIMPLE: (
        10,
        "Direct testamentary probate transfer or independent administrator deed."
    ),
    VestingType.JTWROS: (
        35,
        "Non-probate operation of law; record certified death certificate and affidavit of survivorship."
    ),
    VestingType.REVOCABLE_LIVING_TRUST: (
        45,
        "Private non-court disposition; obtain Certificate of Trust and verify Successor Trustee powers."
    ),
    VestingType.TENANCY_IN_COMMON: (
        65,
        "Multi-heir intestate consensus; require partition mediation or joinder of all fractional co-tenants."
    ),
    VestingType.HEIR_PROPERTY: (
        85,
        "Ancestral quiet title action or serial probate administration across multiple estates."
    ),
    VestingType.ENTITY_OWNERSHIP: (
        100,
        "Corporate entity resolution; inspect operating agreement for deceased managing member transfer powers."
    ),
}


FLAG_PENALTIES: tuple[tuple[str, int], ...] = (
    ("has_unrecorded_trust_reference", 10),
    ("has_title_cloud_or_wild_deed", 15),
    ("has_foreign_or_ancillary_jurisdiction", 10),
)


def _calculate_penalties(inputs: OwnershipComplexityInputs) -> int:
    heir_penalty = min(20, (inputs.heir_count - 4) * 4) if inputs.heir_count > 4 else 0
    ancestor_penalty = inputs.ancestor_probates_unresolved * 15 if inputs.ancestor_probates_unresolved > 0 else 0
    flag_penalties = sum(points for attr, points in FLAG_PENALTIES if getattr(inputs, attr, False))
    return heir_penalty + ancestor_penalty + flag_penalties


def compute_ownership_complexity(inputs: OwnershipComplexityInputs) -> OwnershipComplexityResult:
    """Computes the Ownership Complexity Score (OCS, 10-100) based on title structure."""
    base_score, strategy = VESTING_ARCHETYPES.get(
        inputs.vesting_type,
        VESTING_ARCHETYPES[VestingType.ENTITY_OWNERSHIP]
    )
    penalties = _calculate_penalties(inputs)
    total_score = min(100, max(10, base_score + penalties))

    return OwnershipComplexityResult(
        complexity_score=total_score,
        base_score=base_score,
        penalties_applied=penalties,
        title_clearance_strategy=strategy
    )
