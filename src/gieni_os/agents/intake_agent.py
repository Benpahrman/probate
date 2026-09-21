"""
Probate Intake Agent
Parses raw court filings, validates docket completeness, and initializes the Case domain model.
"""

from typing import Dict, Any
from gieni_os.agents.base import BaseAgent
from gieni_os.domain.probate import DocketRecord

class ProbateIntakeAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="agt_probate_intake",
            agent_name="Probate Intake Agent",
            version="2.0.0"
        )

    def validate(self, payload: Dict[str, Any]) -> bool:
        return bool(payload.get("case_number") and payload.get("county_id") and payload.get("decedent_name"))

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.validate(payload):
            raise ValueError("Invalid docket payload: missing case_number, county_id, or decedent_name.")

        docket = DocketRecord(
            case_number=payload["case_number"],
            county_id=payload["county_id"],
            decedent_name=payload["decedent_name"],
            filing_date=payload.get("filing_date"),
            attorney_name=payload.get("attorney_name"),
            petitioner_name=payload.get("petitioner_name"),
            raw_court_data=payload.get("raw_court_data", {})
        )

        return {
            "status": "VALIDATED",
            "docket": docket,
            "case_number": docket.case_number,
            "county_id": docket.county_id,
            "decedent_name": docket.decedent_name,
            "petitioner_name": docket.petitioner_name,
            "raw_address": payload.get("raw_address")
        }

    def return_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result
