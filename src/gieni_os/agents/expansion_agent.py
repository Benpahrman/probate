"""
County Expansion Agent
Evaluates multi-county market feasibility and compiles rapid 14-day scraper deployment assets.
"""

from typing import Dict, Any
from gieni_os.agents.base import BaseAgent
from gieni_os.engines.expansion_engine import ExpansionEngine

class ExpansionAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="agt_expansion",
            agent_name="County Expansion Agent",
            version="2.0.0"
        )
        self.engine = ExpansionEngine()

    def validate(self, payload: Dict[str, Any]) -> bool:
        return bool(payload.get("county_id"))

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.validate(payload):
            raise ValueError("Invalid expansion payload: county_id required.")

        county_id = payload["county_id"]
        feasibility = self.engine.evaluate_county(county_id)
        scraper_code = self.engine.generate_scraper_script(county_id)

        return {
            "status": "EXPANSION_EVALUATED",
            "county_id": county_id,
            "feasibility_score": feasibility.composite_feasibility,
            "expansion_status": feasibility.status.value,
            "county_feasibility": feasibility,
            "scraper_script": scraper_code
        }

    def return_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result
