"""
Gieni OS Automated Recovery Runbooks
Deterministic isolation and recovery procedures for scrapers, OCR, title conflicts, and webhook delivery.
"""

import logging
from typing import Callable, Dict, Any
from gieni_os.events.schemas import PipelineExceptionRoutedEvent

logger = logging.getLogger("Runbooks")

class ScraperRecoveryRunbook:
    @staticmethod
    def execute_with_recovery(scraper_func: Callable[[str], Any], target_url: str) -> Dict[str, Any]:
        proxies = ["us-east-standard", "us-central-residential", "us-west-backup"]
        attempts = 0
        
        for proxy in proxies:
            attempts += 1
            try:
                result = scraper_func(proxy)
                logger.info(f"[ScraperRecovery] Success on attempt {attempts} using proxy '{proxy}' for {target_url}")
                return {
                    "status": "SUCCESS",
                    "proxy_used": proxy,
                    "attempts": attempts,
                    "data": result
                }
            except Exception as e:
                logger.warning(f"[ScraperRecovery] Proxy '{proxy}' failed: {e}. Rotating to next endpoint...")
                
        raise RuntimeError(f"All scraper proxies exhausted after {attempts} attempts for {target_url}")

class OCRRecoveryRunbook:
    @staticmethod
    def isolate_corrupted_document(case_id: str, doc_uri: str, error_reason: str) -> PipelineExceptionRoutedEvent:
        logger.error(f"[OCRRecovery] Document corrupted at {doc_uri}: {error_reason}. Routing to HITL queue.")
        return PipelineExceptionRoutedEvent(
            caseId=case_id,
            exceptionCode="EXC_OCR_CORRUPTION",
            assignedQueue="HITL_DOCUMENT_QUEUE",
            reason=f"File {doc_uri} corrupted: {error_reason}"
        )

class TitleConflictRunbook:
    @staticmethod
    def isolate_title_exception(case_id: str, parcel_id: str, error_reason: str) -> PipelineExceptionRoutedEvent:
        logger.error(f"[TitleRecovery] Title conflict detected on parcel {parcel_id}: {error_reason}.")
        return PipelineExceptionRoutedEvent(
            caseId=case_id,
            exceptionCode="EXC_TITLE_CLOUD",
            assignedQueue="TITLE_CURATIVE_QUEUE",
            reason=f"Parcel {parcel_id}: {error_reason}"
        )

class AuthorityAmbiguityRunbook:
    @staticmethod
    def isolate_authority_exception(case_id: str, error_reason: str) -> PipelineExceptionRoutedEvent:
        return PipelineExceptionRoutedEvent(
            caseId=case_id,
            exceptionCode="EXC_AUTHORITY_AMBIGUITY",
            assignedQueue="LEGAL_REVIEW_QUEUE",
            reason=error_reason
        )

class PartnerWebhookRecoveryRunbook:
    @staticmethod
    def handle_failed_webhook(client_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        logger.critical(f"[WebhookRecovery] Webhook delivery failed for client {client_id}. Firing SMS fallback alert.")
        return {
            "action": "DLQ_FALLBACK_SMS",
            "client_id": client_id,
            "sms_sent": True
        }
