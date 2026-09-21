"""
Gieni OS Contexts Layer (Top-Level Context Architecture)
Provides canonical context modules:
- probate
- property
- ownership
- authority
- control
- opportunity
- delivery
- telemetry
- intelligence (The Brain)
"""

from gieni_os.intelligence import IntelligenceContext, get_intelligence_context

__all__ = [
    "IntelligenceContext",
    "get_intelligence_context",
]
