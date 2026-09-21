"""
Ownership Complexity Score (OCS) Engine
Computes a 10-100 integer score reflecting the legal complexity of clearing
title for a probate-estate transaction. Higher scores indicate greater friction
and longer time-to-close.

Transplanted from backend/app/engines/complexity.py.
Imports rewritten: app.models.enums → gieni_os.domain.enums
"""

from pydantic import BaseModel, Field, ConfigDict
from gieni_os.domain.enums import VestingType


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


def compute_ownership_complexity(inputs: OwnershipComplexityInputs) -> OwnershipComplexityResult:
    """Computes the Ownership Complexity Score (OCS, 10-100) based on title structure:

    Base Archetypes:
    - Sole Fee Simple: 10 pts
    - Joint Tenancy (JTWROS / TBE): 35 pts
    - Revocable Living Trust: 45 pts
    - Tenancy in Common / Multi-Heir: 65 pts
    - Ancestral Heir Property: 85 pts
    - Entity Ownership Stack: 100 pts
    """
    if inputs.vesting_type == VestingType.SOLE_FEE_SIMPLE:
        base_score = 10
        strategy = "Direct testamentary probate transfer or independent administrator deed."
    elif inputs.vesting_type == VestingType.JTWROS:
        base_score = 35
        strategy = "Non-probate operation of law; record certified death certificate and affidavit of survivorship."
    elif inputs.vesting_type == VestingType.REVOCABLE_LIVING_TRUST:
        base_score = 45
        strategy = "Private non-court disposition; obtain Certificate of Trust and verify Successor Trustee powers."
    elif inputs.vesting_type == VestingType.TENANCY_IN_COMMON:
        base_score = 65
        strategy = "Multi-heir intestate consensus; require partition mediation or joinder of all fractional co-tenants."
    elif inputs.vesting_type == VestingType.HEIR_PROPERTY:
        base_score = 85
        strategy = "Ancestral quiet title action or serial probate administration across multiple estates."
    else:  # ENTITY_OWNERSHIP
        base_score = 100
        strategy = "Corporate entity resolution; inspect operating agreement for deceased managing member transfer powers."

    penalties = 0

    # Additional Heir Fragmentation Penalties
    if inputs.heir_count > 4:
        penalties += min(20, (inputs.heir_count - 4) * 4)

    # Unresolved Ancestor Probates (+15 per generation)
    if inputs.ancestor_probates_unresolved > 0:
        penalties += inputs.ancestor_probates_unresolved * 15

    # Clouded Title Flags
    if inputs.has_unrecorded_trust_reference:
        penalties += 10
    if inputs.has_title_cloud_or_wild_deed:
        penalties += 15
    if inputs.has_foreign_or_ancillary_jurisdiction:
        penalties += 10

    total_score = min(100, max(10, base_score + penalties))

    return OwnershipComplexityResult(
        complexity_score=total_score,
        base_score=base_score,
        penalties_applied=penalties,
        title_clearance_strategy=strategy
    )
