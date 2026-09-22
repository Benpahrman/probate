from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class PASCategory(str, Enum):
    VERIFIED_MATCH = "VERIFIED_MATCH"       # 90.0 - 100.0: Certified for Automated Pipeline
    PROBABLE_MATCH = "PROBABLE_MATCH"       # 70.0 - 89.99: Delivered with Validation Tag
    MANUAL_REVIEW = "MANUAL_REVIEW"         # < 70.0: Routed to Tasks & Exceptions Queue


class ParcelAttributionInputs(BaseModel):
    source_agreement: float = Field(
        ..., ge=0.0, le=1.0,
        description="Assessor + Recorder + Court agreement confidence (Weight: 30%)"
    )
    name_similarity: float = Field(
        ..., ge=0.0, le=1.0,
        description="Jaro-Winkler string similarity between decedent and titleholder (Weight: 25%)"
    )
    address_correlation: float = Field(
        ..., ge=0.0, le=1.0,
        description="Situs address correlation against death certificate/voter registry (Weight: 20%)"
    )
    title_continuity: float = Field(
        ..., ge=0.0, le=1.0,
        description="Unbroken chain of recorded conveyance instruments (Weight: 15%)"
    )
    tax_alignment: float = Field(
        ..., ge=0.0, le=1.0,
        description="Current taxpayer of record correlation (Weight: 10%)"
    )

    model_config = ConfigDict(extra="forbid")


class ParcelAttributionResult(BaseModel):
    pas_score: float = Field(..., ge=0.0, le=100.0)
    category: PASCategory
    gate_2_passed: bool
    requires_manual_triage: bool


def _find_matches(s1: str, s2: str, max_dist: int) -> tuple[int, list[bool], list[bool]]:
    len1, len2 = len(s1), len(s2)
    s1_matches = [False] * len1
    s2_matches = [False] * len2
    matches = 0

    for i in range(len1):
        start = max(0, i - max_dist)
        end = min(i + max_dist + 1, len2)
        for j in range(start, end):
            if not s2_matches[j] and s1[i] == s2[j]:
                s1_matches[i] = True
                s2_matches[j] = True
                matches += 1
                break

    return matches, s1_matches, s2_matches


def _count_transpositions(s1: str, s2: str, s1_matches: list[bool], s2_matches: list[bool]) -> int:
    k = 0
    transpositions = 0
    for i in range(len(s1)):
        if not s1_matches[i]:
            continue
        while not s2_matches[k]:
            k += 1
        if s1[i] != s2[k]:
            transpositions += 1
        k += 1
    return transpositions // 2


def _common_prefix_length(s1: str, s2: str, max_prefix: int = 4) -> int:
    prefix = 0
    for c1, c2 in zip(s1[:max_prefix], s2[:max_prefix]):
        if c1 == c2:
            prefix += 1
        else:
            break
    return prefix


def calculate_jaro_winkler(s1: str, s2: str, scaling_factor: float = 0.1) -> float:
    """Deterministic Jaro-Winkler similarity implementation for legal entity names."""
    s1 = s1.strip().upper()
    s2 = s2.strip().upper()

    if s1 == s2:
        return 1.0
    if not s1 or not s2:
        return 0.0

    len1, len2 = len(s1), len(s2)
    max_dist = max(0, max(len1, len2) // 2 - 1)

    matches, s1_matches, s2_matches = _find_matches(s1, s2, max_dist)
    if matches == 0:
        return 0.0

    transpositions = _count_transpositions(s1, s2, s1_matches, s2_matches)

    # Jaro Metric
    jaro = (
        (matches / len1) +
        (matches / len2) +
        ((matches - transpositions) / matches)
    ) / 3.0

    prefix = _common_prefix_length(s1, s2, max_prefix=4)
    return round(jaro + (prefix * scaling_factor * (1.0 - jaro)), 4)


def _classify_pas_tier(score: float) -> tuple[PASCategory, bool, bool]:
    """Classifies PAS score into gate verification category, pass status, and triage requirement."""
    if score >= 90.0:
        return PASCategory.VERIFIED_MATCH, True, False
    if score >= 70.0:
        return PASCategory.PROBABLE_MATCH, True, False
    return PASCategory.MANUAL_REVIEW, False, True


def calculate_pas(inputs: ParcelAttributionInputs) -> ParcelAttributionResult:
    """Computes the 0-100 Parcel Attribution Score (PAS) using the 5-variable weight matrix:

    PAS = (Source Agreement * 30) + (Name Match * 25) + (Address Correlation * 20)
          + (Title Continuity * 15) + (Tax Alignment * 10)
    """
    raw_score = (
        (inputs.source_agreement * 30.0) +
        (inputs.name_similarity * 25.0) +
        (inputs.address_correlation * 20.0) +
        (inputs.title_continuity * 15.0) +
        (inputs.tax_alignment * 10.0)
    )
    score = round(max(0.0, min(100.0, raw_score)), 2)
    category, gate_2_passed, requires_manual_triage = _classify_pas_tier(score)

    return ParcelAttributionResult(
        pas_score=score,
        category=category,
        gate_2_passed=gate_2_passed,
        requires_manual_triage=requires_manual_triage
    )
