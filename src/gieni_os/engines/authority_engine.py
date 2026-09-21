"""
Authority Resolution Engine (ARE)
Implements Washington State RCW Title 11 Statutory Rules & Evidentiary Tiers.
"""

from typing import Dict, Any, Optional
from gieni_os.domain.authority import (
    AuthorityTier,
    LettersType,
    FiduciaryAuthorityRecord
)

class AuthorityEngine:
    @classmethod
    def evaluate_authority(
        cls,
        case_number: str,
        property_id: str,
        petitioner_name: str,
        docket_entries: list,
        will_filed: bool = True,
        is_contested: bool = False
    ) -> FiduciaryAuthorityRecord:
        """
        Evaluates Washington State RCW Title 11 statutory authority:
        - Checks for Order Appointing Personal Representative
        - Checks for RCW 11.68 Nonintervention Powers
        """
        if is_contested:
            return FiduciaryAuthorityRecord(
                case_number=case_number,
                property_id=property_id,
                authority_tier=AuthorityTier.TIER_4_UNCERTAIN,
                fiduciary_name=petitioner_name,
                fiduciary_role="Contested Petitioner",
                letters_status=LettersType.NONE,
                statutory_powers="None (Estate In Contest)",
                court_supervision="Full Court Oversight Required (RCW 11.76)",
                requires_human_verification=True,
                evidence_citation="Dispute filed on docket; competing petitions pending."
            )

        # Check docket for Letters and Powers
        letters_granted = any("letters" in str(e).lower() for e in docket_entries)
        nonintervention = any("nonintervention" in str(e).lower() or "11.68" in str(e).lower() for e in docket_entries)

        if letters_granted and nonintervention:
            tier = AuthorityTier.TIER_1_CERTIFIED
            letters = LettersType.LETTERS_TESTAMENTARY if will_filed else LettersType.LETTERS_OF_ADMINISTRATION
            powers = "RCW 11.68 Nonintervention Powers Granted (Sole Power to Sell Real Property)"
            supervision = "None (Independent Fiduciary Sale Authorized)"
            human_review = False
            citation = "Letters Testamentary recorded with RCW 11.68 Order Granting Nonintervention Powers."
        elif letters_granted and not nonintervention:
            tier = AuthorityTier.TIER_2_PROBABLE
            letters = LettersType.LETTERS_TESTAMENTARY if will_filed else LettersType.LETTERS_OF_ADMINISTRATION
            powers = "Limited Fiduciary Powers (Court Approval Required)"
            supervision = "Court Confirmation Hearing Required under RCW 11.76 before closing."
            human_review = True
            citation = "Letters issued with bond; full court confirmation required under RCW 11.76."
        else:
            tier = AuthorityTier.TIER_2_PROBABLE
            letters = LettersType.NONE
            powers = "Nominated in Will (Pre-Letters Capacity)"
            supervision = "Pending hearing on petition for probate."
            human_review = True
            citation = "Petition filed; Order appointing PR pending court clerk calendar."

        return FiduciaryAuthorityRecord(
            case_number=case_number,
            property_id=property_id,
            authority_tier=tier,
            fiduciary_name=petitioner_name,
            fiduciary_role="Personal Representative",
            letters_status=letters,
            statutory_powers=powers,
            court_supervision=supervision,
            requires_human_verification=human_review,
            evidence_citation=citation
        )
