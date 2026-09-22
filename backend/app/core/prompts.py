"""
Prompt Registry & Jurisprudence Templates for Gieni OS
Provides versioned, strictly typed, parameter-validated templates for AI reasoning.
"""

from typing import Dict, Any, List, Optional


class PromptTemplate:
    """Represents a versioned system prompt template."""

    def __init__(
        self,
        key: str,
        version: str,
        category: str,
        template_text: str,
        required_variables: List[str],
        description: str = "",
    ):
        self.key = key
        self.version = version
        self.category = category
        self.template_text = template_text
        self.required_variables = required_variables
        self.description = description

    def format(self, **kwargs) -> str:
        """Render the prompt template ensuring all required variables are supplied."""
        missing = [v for v in self.required_variables if v not in kwargs]
        if missing:
            raise ValueError(f"Prompt '{self.key}:{self.version}' missing required variables: {missing}")
        return self.template_text.format(**kwargs)


class PromptRegistry:
    """Central registry storing and providing versioned templates."""

    def __init__(self):
        self._templates: Dict[str, PromptTemplate] = {}
        self._register_default_templates()

    def register(self, template: PromptTemplate):
        full_key = f"{template.key}:{template.version}"
        self._templates[full_key] = template
        self._templates[template.key] = template

    def get(self, key: str, version: Optional[str] = None) -> PromptTemplate:
        lookup = f"{key}:{version}" if version else key
        if lookup not in self._templates:
            raise KeyError(f"Prompt template '{lookup}' not found in registry.")
        return self._templates[lookup]

    def render(self, key: str, version: Optional[str] = None, **kwargs) -> str:
        tmpl = self.get(key, version)
        return tmpl.format(**kwargs)

    def _register_default_templates(self):
        # 1. Ownership Analysis
        self.register(
            PromptTemplate(
                key="ownership-analysis",
                version="v1",
                category="ownership",
                template_text=(
                    "You are the Gieni Ownership Intelligence Engine (OIE). "
                    "Analyze the title vesting and equity waterfall for {property_address}. "
                    "Assessed Value: ${assessed_value:,.0f} | Estimated ARV: ${arv:,.0f} | Total Encumbrances: ${encumbrances:,.0f}. "
                    "Deed Vesting on Record: {vesting_status}. "
                    "Determine whether title is clouded, identify surviving joint tenants or probate necessity under RCW 11.04, "
                    "and calculate distributable net equity cushion."
                ),
                required_variables=["property_address", "assessed_value", "arv", "encumbrances", "vesting_status"],
                description="Analyzes equity waterfall, encumbrances, and deed vesting.",
            )
        )

        # 2. Authority Reasoning
        self.register(
            PromptTemplate(
                key="authority-reasoning",
                version="v1",
                category="authority",
                template_text=(
                    "You are the Gieni Authority Resolution Engine (ARE). "
                    "Evaluate statutory fiduciary powers for estate of {decedent} in {county_name} County. "
                    "Docket Number: {docket_number} | Oversight: {oversight_model} | Fiduciary: {fiduciary_name}. "
                    "Statutory Basis: {statutory_basis}. "
                    "Determine whether Nonintervention Powers under RCW 11.68.011 exist to allow execution of binding PSAs "
                    "without judicial confirmation."
                ),
                required_variables=["decedent", "county_name", "docket_number", "oversight_model", "fiduciary_name", "statutory_basis"],
                description="Evaluates RCW Title 11 nonintervention powers and fiduciary authority.",
            )
        )

        # 3. Control Classification
        self.register(
            PromptTemplate(
                key="control-classification",
                version="v1",
                category="control",
                template_text=(
                    "You are the Gieni Control Intelligence Engine (CIE). "
                    "Map the decision-making network for {estate_name}. "
                    "Identified Heirs: {heir_count} | Primary Decision Maker: {decision_maker} ({relationship}). "
                    "Classify into archetypes (UNIFIED_SOLE_PR, BALANCED_CONSENSUS, CONFLICT_MULTI_HEIR) "
                    "and prescribe dispute avoidance tactics."
                ),
                required_variables=["estate_name", "heir_count", "decision_maker", "relationship"],
                description="Maps heirship network, friction archetypes, and signing capacity.",
            )
        )

        # 4. QC Validation
        self.register(
            PromptTemplate(
                key="qc-validation",
                version="v1",
                category="qc",
                template_text=(
                    "You are the Gieni Quality Control Engine (QCE). "
                    "Verify the 6-Gate statutory compliance for Opportunity #{opportunity_id}. "
                    "Gates checked: Docket ({gate_docket}), APN ({gate_apn}), Vesting ({gate_vesting}), "
                    "Authority ({gate_auth}), Valuation ({gate_val}), Contact ({gate_contact}). "
                    "State whether opportunity is approved for delivery or flagged for human review."
                ),
                required_variables=["opportunity_id", "gate_docket", "gate_apn", "gate_vesting", "gate_auth", "gate_val", "gate_contact"],
                description="Validates 6-gate statutory integrity prior to dispatch.",
            )
        )

        # 5. Delivery Pitch
        self.register(
            PromptTemplate(
                key="delivery-pitch",
                version="v1",
                category="delivery",
                template_text=(
                    "You are the Gieni Deal Delivery Engine (DDE). "
                    "Generate the institutional investment summary for {situs_address}. "
                    "Net Equity: ${net_equity:,.0f} | Target MAO: ${mao:,.0f} | Priority: {priority_tier}. "
                    "Synthesize the rapid-acquisition thesis for B2B wholesale buyers."
                ),
                required_variables=["situs_address", "net_equity", "mao", "priority_tier"],
                description="Generates executive deal packet and conversational framing script.",
            )
        )


default_prompt_registry = PromptRegistry()
