"""
Gieni OS Models — Compatibility Shim
The canonical 17-table SQLAlchemy 2.0 ORM now lives in orm.py.
This module re-exports everything for backward compatibility with any
existing code that imports from gieni_os.models.entities.
"""

from gieni_os.models.orm import (
    Base,
    County,
    Person,
    ContactPoint,
    ProbateCase,
    Property,
    PropertyAssessment,
    Encumbrance,
    TaxLien,
    OwnershipAssessment,
    ControlAssessment,
    AuthorityAssessment,
    Opportunity,
    Client,
    TerritoryAgreement,
    OpportunityDelivery,
    EvidenceRecord,
    TaskException,
)

__all__ = [
    "Base",
    "County", "Person", "ContactPoint",
    "ProbateCase", "Property", "PropertyAssessment",
    "Encumbrance", "TaxLien", "OwnershipAssessment",
    "ControlAssessment", "AuthorityAssessment",
    "Opportunity", "Client", "TerritoryAgreement",
    "OpportunityDelivery", "EvidenceRecord", "TaskException",
]
