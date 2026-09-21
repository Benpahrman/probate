"""
Gieni OS - Clerk Identity Layer & Multi-Tenant Organization Context
Zero custom auth infrastructure. All user identity, authentication, and B2B
organization tenancy are delegated directly to Clerk.

Mapping:
Clerk Org -> County Contract -> Opportunity Visibility
"""

import os
import logging
import jwt
from typing import Optional, Dict, Any
from pydantic import BaseModel
from fastapi import Header, HTTPException, status, Depends

logger = logging.getLogger("gieni_os.auth")

class ClerkUserContext(BaseModel):
    user_id: str
    username: Optional[str] = "Operator"
    org_id: Optional[str] = None
    org_role: str = "member"
    role: str = "Platform Admin"
    is_internal_operator: bool = True
    contracted_county: Optional[str] = None

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

# Static/Contracted Organization -> County mapping table (representing Clerk Org metadata / DB contracts)
CLERK_ORG_COUNTY_MAP: Dict[str, str] = {
    "org_sound_capital": "Pierce",
    "org_nw_acquisitions": "Thurston",
    "org_king_capital": "King",
    "org_snohomish_investors": "Snohomish",
    "org_clark_partners": "Clark"
}

INTERNAL_ROLES = {
    "Platform Admin",
    "Research Lead",
    "Research Analyst",
    "QC Analyst",
    "Admin",
    "Researcher",
    "QC"
}

from gieni_os.security.governance import (
    SecurityPolicyEnforcer,
    SecurityContext,
    UserRole,
    DataClassification,
    PermissionDeniedError
)

def get_current_user(
    x_clerk_user_id: Optional[str] = Header(default=None),
    x_clerk_org_id: Optional[str] = Header(default=None),
    x_clerk_role: Optional[str] = Header(default=None),
    x_user_role: Optional[str] = Header(default=None),
    authorization: Optional[str] = Header(default=None)
) -> ClerkUserContext:
    user_id = None
    role = None
    org_id = None

    # 1. Primary: Server-side JWT Verification from Authorization Bearer token
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
        try:
            clerk_key = os.getenv("CLERK_PEM_PUBLIC_KEY") or os.getenv("CLERK_SECRET_KEY")
            is_demo = os.getenv("DEMO_MODE", "").lower() in ("true", "1", "yes")
            if clerk_key:
                payload = jwt.decode(token, clerk_key, algorithms=["RS256", "HS256"], options={"verify_aud": False})
            elif is_demo:
                payload = jwt.decode(token, options={"verify_signature": False})
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Production security violation: Clerk verification keys are not configured. Unsigned JWTs are strictly prohibited."
                )
            
            user_id = payload.get("sub") or payload.get("user_id") or "user_clerk_authenticated"
            org_id = payload.get("org_id") or payload.get("orgId")
            role = payload.get("org_role") or payload.get("role") or "Platform Admin"
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Authorization credentials: {str(e)}"
            )
    # 2. Secondary: Gated test/dev headers only when DEMO_MODE=true
    elif os.getenv("DEMO_MODE", "").lower() in ("true", "1", "yes") and (x_clerk_user_id or x_clerk_org_id or x_clerk_role or x_user_role):
        user_id = x_clerk_user_id or "user_clerk_authenticated"
        org_id = x_clerk_org_id
        role = x_clerk_role or x_user_role or ("Platform Admin" if (x_clerk_user_id and not x_clerk_org_id) else "member")
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required: No valid Authorization Bearer token or authorized credentials provided."
        )

    # Normalize roles
    if role == "Admin":
        role = "Platform Admin"
    elif role == "Researcher":
        role = "Research Analyst"
    elif role == "Client":
        role = "org:admin"

    is_client_partner = (
        role in ("org:admin", "org:member", "client", "Client", "client_partner")
        or (role and (role.startswith("org:") or "partner" in role.lower()))
        or (org_id is not None and role not in INTERNAL_ROLES)
    )
    is_internal = not is_client_partner

    # Strict contracted county mapping for B2B client organizations
    contracted_county = None
    if org_id:
        if org_id not in CLERK_ORG_COUNTY_MAP:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Organization '{org_id}' does not hold an active county contract."
            )
        contracted_county = CLERK_ORG_COUNTY_MAP[org_id]
    elif not is_internal:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Client partner requests require an active contracted organization context."
        )

    return ClerkUserContext(
        user_id=user_id or "user_clerk_authenticated",
        org_id=org_id,
        org_role=role if not is_internal else "internal",
        role=role or "Platform Admin",
        is_internal_operator=is_internal,
        contracted_county=contracted_county
    )

def get_clerk_county_contract(user: ClerkUserContext) -> Optional[str]:
    """Returns the exclusive county for B2B Client Organizations, or None for Internal Admins."""
    if user.is_internal_operator:
        return None
    return user.contracted_county

def require_operator_role(user: ClerkUserContext = Depends(get_current_user)) -> ClerkUserContext:
    """Verifies that the caller possesses internal Gieni operator privileges."""
    if not user.is_internal_operator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Internal operator privileges required."
        )
    return user

def require_internal_operator(user: ClerkUserContext = Depends(get_current_user)) -> ClerkUserContext:
    """Verifies that the caller possesses internal Gieni operator privileges and passes SecurityPolicyEnforcer."""
    if not user.is_internal_operator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Internal operator privileges required."
        )
    role = UserRole.ADMIN_CTO if user.role == "Platform Admin" else UserRole.RESEARCH_SPECIALIST
    sec_ctx = SecurityContext(
        user_id=user.user_id,
        role=role,
        tenant_id=user.org_id,
        licensed_counties=[user.contracted_county] if user.contracted_county else []
    )
    try:
        SecurityPolicyEnforcer.authorize_access(sec_ctx, DataClassification.INTERNAL_OPERATIONAL)
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    return user

def require_security_context(
    user: ClerkUserContext = Depends(get_current_user),
    classification: DataClassification = DataClassification.INTERNAL_OPERATIONAL
) -> SecurityContext:
    """Active HTTP lifecycle bridge for SecurityPolicyEnforcer."""
    if user.is_internal_operator:
        role = UserRole.ADMIN_CTO if user.role == "Platform Admin" else UserRole.RESEARCH_SPECIALIST
    else:
        role = UserRole.CLIENT_PARTNER
    sec_ctx = SecurityContext(
        user_id=user.user_id,
        role=role,
        tenant_id=user.org_id,
        licensed_counties=[user.contracted_county] if user.contracted_county else []
    )
    try:
        SecurityPolicyEnforcer.authorize_access(sec_ctx, classification)
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    return sec_ctx
