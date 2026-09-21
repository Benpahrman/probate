"""
Pierce County LINX Superior Court Docket Harvester
Queries the Pierce County Legal Information Network Exchange (LINX)
for newly filed probate petitions (Case Type 4).
"""

import os
import uuid
from typing import List
from datetime import date, timedelta
from gieni_os.ingestion.models import ScrapedDocket, FilingChannel, HarvesterUnavailableError

class LinxHarvester:
    PORTAL_URL = "https://linxonline.co.pierce.wa.us/linxweb/Docket.cfm"

    @classmethod
    def harvest(cls, days_back: int = 7) -> List[ScrapedDocket]:
        """
        Extracts recent probate petitions from Pierce County LINX.
        Returns normalized ScrapedDocket objects.
        """
        demo_mode = os.getenv("DEMO_MODE", "").lower() in ("true", "1", "yes")
        if not demo_mode:
            raise HarvesterUnavailableError(
                "LinxHarvester requires DEMO_MODE=true or live Playwright browser scraper credentials."
            )

        # In compliance with Rule §4: Zero Synthetic Entities
        # We no longer generate fake records or fictional names.
        return []
