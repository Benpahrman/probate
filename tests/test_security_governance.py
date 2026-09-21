"""
Test Suite for Gieni OS Security Governance, RBAC, and Encryption
"""

import pytest
from gieni_os.security.governance import (
    DataClassification,
    UserRole,
    SecurityContext,
    SecurityPolicyEnforcer,
    PermissionDeniedError
)

def test_admin_authorization():
    admin = SecurityContext(user_id="admin_01", role=UserRole.ADMIN_CTO)
    assert SecurityPolicyEnforcer.authorize_access(admin, DataClassification.INTERNAL_INTELLIGENCE) is True
    assert SecurityPolicyEnforcer.authorize_access(admin, DataClassification.RESTRICTED_PII) is True

def test_researcher_rbac_denial():
    researcher = SecurityContext(user_id="res_01", role=UserRole.RESEARCH_SPECIALIST)
    assert SecurityPolicyEnforcer.authorize_access(researcher, DataClassification.INTERNAL_OPERATIONAL) is True

    with pytest.raises(PermissionDeniedError):
        SecurityPolicyEnforcer.authorize_access(researcher, DataClassification.INTERNAL_INTELLIGENCE)

def test_partner_field_masking():
    partner = SecurityContext(user_id="part_01", role=UserRole.CLIENT_PARTNER)
    record = {
        "apn": "0321151042",
        "situs_address": "3719 N 28TH ST",
        "compositeViabilityScore": 92,
        "ownershipComplexityScore": 15,
        "internalConfidenceScore": 98.4
    }
    masked = SecurityPolicyEnforcer.mask_record_for_user(partner, record)
    assert "ownershipComplexityScore" not in masked
    assert "internalConfidenceScore" not in masked
    assert masked["apn"] == "0321151042"

def test_aes_at_rest_encryption_cycle():
    raw_secret = "SSN-000-12-3456"
    encrypted = SecurityPolicyEnforcer.encrypt_at_rest(raw_secret)
    assert encrypted.startswith("enc_aes256_")
    assert encrypted != raw_secret

    decrypted = SecurityPolicyEnforcer.decrypt_at_rest(encrypted)
    assert decrypted == raw_secret
