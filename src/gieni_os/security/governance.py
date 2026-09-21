"""
Gieni OS Security & Governance
Four-tier data classification, RBAC enforcement, field masking, and encryption at rest.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import base64
import hashlib
from cryptography.fernet import Fernet
from gieni_os import config

def _get_fernet() -> Fernet:
    key_bytes = hashlib.sha256(config.AES_SECRET_KEY.encode("utf-8")).digest()
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(fernet_key)

class DataClassification(Enum):
    PUBLIC = "PUBLIC"
    INTERNAL_OPERATIONAL = "INTERNAL_OPERATIONAL"
    COMMERCIAL_PARTNER = "COMMERCIAL_PARTNER"
    INTERNAL_INTELLIGENCE = "INTERNAL_INTELLIGENCE"
    RESTRICTED_PII = "RESTRICTED_PII"

class UserRole(Enum):
    ADMIN_CTO = "ADMIN_CTO"
    RESEARCH_SPECIALIST = "RESEARCH_SPECIALIST"
    CLIENT_PARTNER = "CLIENT_PARTNER"

@dataclass
class SecurityContext:
    user_id: str
    role: UserRole
    tenant_id: Optional[str] = None
    licensed_counties: List[str] = field(default_factory=list)

class PermissionDeniedError(Exception):
    pass

class SecurityPolicyEnforcer:
    @staticmethod
    def authorize_access(context: SecurityContext, classification: DataClassification) -> bool:
        if context.role == UserRole.ADMIN_CTO:
            return True
        if context.role == UserRole.RESEARCH_SPECIALIST:
            if classification in (DataClassification.INTERNAL_INTELLIGENCE, DataClassification.RESTRICTED_PII):
                raise PermissionDeniedError(f"User {context.user_id} with role {context.role.value} denied access to {classification.value}")
            return True
        if context.role == UserRole.CLIENT_PARTNER:
            if classification != DataClassification.COMMERCIAL_PARTNER and classification != DataClassification.PUBLIC:
                raise PermissionDeniedError(f"Partner {context.user_id} restricted to COMMERCIAL_PARTNER data tier.")
            return True
        return False

    @staticmethod
    def mask_record_for_user(context: SecurityContext, record: Dict[str, Any]) -> Dict[str, Any]:
        result = dict(record)
        if context.role == UserRole.CLIENT_PARTNER:
            # Mask internal complexity and underwriting formulas
            result.pop("ownershipComplexityScore", None)
            result.pop("internalConfidenceScore", None)
            result.pop("scraperSignature", None)
        return result

    @staticmethod
    def encrypt_at_rest(plaintext: str) -> str:
        if not plaintext:
            return ""
        fernet = _get_fernet()
        token = fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")
        return f"enc_aes256_{token}"

    @staticmethod
    def decrypt_at_rest(ciphertext: str) -> str:
        if not ciphertext:
            return ""
        if ciphertext.startswith("enc_aes256_"):
            token = ciphertext[len("enc_aes256_"):]
            try:
                fernet = _get_fernet()
                return fernet.decrypt(token.encode("utf-8")).decode("utf-8")
            except Exception as e:
                raise ValueError(f"Decryption failed: corrupted ciphertext or invalid encryption key ({e}).")
        return ciphertext
