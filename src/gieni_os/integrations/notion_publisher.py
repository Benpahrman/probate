"""
Gieni OS Notion Publisher Integration
Synchronizes verified opportunities and reference architecture articles to the Notion workspace.
"""

import httpx
import logging
from typing import Dict, Any, Optional
from gieni_os.config import NOTION_TOKEN, NOTION_VERSION, OPPORTUNITIES_DB_ID, PIERCE_COUNTY_PAGE_ID
from gieni_os.pof.exporter import POFExporter

logger = logging.getLogger("NotionPublisher")

class NotionPublishError(Exception):
    """Raised when publishing to Notion API fails."""
    pass

class NotionPublisher:
    def __init__(self, token: str = NOTION_TOKEN):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json"
        }

    def _build_payload(self, package: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        opp_id = package.get("opportunity_id", "OPP-UNKNOWN")
        prop = package.get("property_profile", {})
        viab = package.get("viability", {})
        fin = package.get("financial_waterfall", {})
        pof = package.get("pof")

        title = f"{opp_id} | {prop.get('situs_address', 'UNKNOWN')}"

        payload = {
            "parent": {"database_id": OPPORTUNITIES_DB_ID},
            "properties": {
                "Opportunity": {
                    "title": [{"text": {"content": title}}]
                },
                "Status": {
                    "select": {"name": "Qualified"}
                },
                "Priority Band": {
                    "select": {"name": viab.get("priority_band", "Priority A")}
                },
                "Composite Score": {
                    "number": viab.get("composite_score", 90)
                },
                "Net Distributable Equity": {
                    "number": fin.get("net_distributable_equity", 0.0)
                }
            }
        }

        if pof:
            payload["children"] = POFExporter.to_notion_blocks(pof)[:10]

        return opp_id, payload

    async def publish_opportunity_async(self, package: Dict[str, Any]) -> Optional[str]:
        """Asynchronous non-blocking Notion publishing."""
        opp_id, payload = self._build_payload(package)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post("https://api.notion.com/v1/pages", headers=self.headers, json=payload)
                if resp.status_code in (200, 201):
                    page_id = resp.json().get("id")
                    logger.info(f"[NotionPublisher] Successfully created Notion page {page_id} for {opp_id}")
                    return page_id
                else:
                    logger.error(f"[NotionPublisher] Notion returned HTTP {resp.status_code}: {resp.text[:200]}")
                    return None
        except Exception as e:
            logger.error(f"[NotionPublisher] Network error calling Notion: {e}")
            return None

    def publish_opportunity(self, package: Dict[str, Any]) -> Optional[str]:
        """Synchronous publishing using httpx.Client."""
        opp_id, payload = self._build_payload(package)
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post("https://api.notion.com/v1/pages", headers=self.headers, json=payload)
                if resp.status_code in (200, 201):
                    page_id = resp.json().get("id")
                    logger.info(f"[NotionPublisher] Successfully created Notion page {page_id} for {opp_id}")
                    return page_id
                else:
                    logger.error(f"[NotionPublisher] Notion returned HTTP {resp.status_code}: {resp.text[:200]}")
                    return None
        except Exception as e:
            logger.error(f"[NotionPublisher] Network error calling Notion: {e}")
            return None
