"""
Domain Model: Washington State Statutory Authority (RCW Title 11)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List

class AuthorityTier(str, Enum):
    TIER_1_CERTIFIED = "Tier 1: Court Certified"       # Letters issued + RCW 11.68 Nonintervention Powers
    TIER_2_PROBABLE = "Tier 2: Probable Fiduciary"     # Will nominated or sole heir
    TIER_3_NON_PROBATE = "Tier 3: Non-Probate Successor"# Affidavit of Successor / Small Estate
    TIER_4_UNCERTAIN = "Tier 4: Contested / Uncertain" # Competing petitions or no fiduciary

class LettersType(str, Enum):
    LETTERS_TESTAMENTARY = "Letters Testamentary"
    LETTERS_OF_ADMINISTRATION = "Letters of Administration"
    LIMITED_LETTERS = "Limited Letters"
    NONE = "None"

@dataclass
class FiduciaryAuthorityRecord:
    case_number: str
    property_id: str
    authority_tier: AuthorityTier
    fiduciary_name: str
    fiduciary_role: str               # e.g., "Personal Representative", "Executor"
    letters_status: LettersType
    statutory_powers: str             # e.g., "RCW 11.68 Nonintervention Powers Granted"
    court_supervision: str            # "None (Full Power of Sale)" or "Confirmation Hearing Required (RCW 11.76)"
    requires_human_verification: bool
    evidence_citation: str
