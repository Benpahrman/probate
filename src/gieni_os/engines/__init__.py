"""
Gieni OS Engines Package
Deterministic business logic & statutory rules
"""

# ── Existing rich engine classes ───────────────────────────────────────────────
from gieni_os.engines.property_engine import PropertyEngine
from gieni_os.engines.ownership_engine import OwnershipEngine
from gieni_os.engines.authority_engine import AuthorityEngine
from gieni_os.engines.control_engine import ControlEngine
from gieni_os.engines.contact_engine import ContactEngine
from gieni_os.engines.scoring_engine import ScoringEngine
from gieni_os.engines.qc_engine import QCEngine
from gieni_os.engines.delivery_engine import DeliveryEngine, CRMAdapter
from gieni_os.engines.telemetry_engine import TelemetryEngine
from gieni_os.engines.expansion_engine import ExpansionEngine

# ── Canonical deterministic mathematical engines (transplanted from backend/) ──
from gieni_os.engines.pas import (
    calculate_pas,
    calculate_jaro_winkler,
    ParcelAttributionInputs,
    ParcelAttributionResult,
    PASCategory,
)
from gieni_os.engines.equity import (
    compute_net_actionable_equity,
    EncumbranceWaterfallInputs,
    EquityWaterfallResult,
    EquityTier,
)
from gieni_os.engines.complexity import (
    compute_ownership_complexity,
    OwnershipComplexityInputs,
    OwnershipComplexityResult,
)
from gieni_os.engines.scoring import (
    compute_opportunity_viability,
    OpportunityScoringInputs,
    OpportunityScoringResult,
)
