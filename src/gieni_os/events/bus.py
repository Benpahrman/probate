import fnmatch
import json
import logging
import os
from typing import Callable, Dict, List, Any, Optional
from gieni_os import config

logger = logging.getLogger("EventBus")

try:
    import redis
    _HAS_REDIS = True
except ImportError:
    _HAS_REDIS = False

class DeadLetterQueue:
    def __init__(self, redis_client: Optional[Any] = None):
        self._queue: List[Any] = []
        self.redis_client = redis_client

    def push(self, item: Any) -> None:
        self._queue.append(item)
        if self.redis_client:
            try:
                payload = json.dumps(item, default=str)
                self.redis_client.rpush("gieni_dlq", payload)
            except Exception as e:
                logger.warning(f"[DLQ] Redis persistence failed: {e}")
        logger.warning(f"[DLQ] Stored corrupted or unhandled event. DLQ size: {len(self._queue)}")

    def size(self) -> int:
        if self.redis_client:
            try:
                r_size = self.redis_client.llen("gieni_dlq")
                return max(len(self._queue), r_size)
            except Exception as e:
                logger.warning(f"[DLQ] Failed to inspect Redis queue size: {e}")
        return len(self._queue)

    def pop(self) -> Any:
        if self.redis_client:
            try:
                val = self.redis_client.lpop("gieni_dlq")
                if val:
                    return json.loads(val)
            except Exception as e:
                logger.warning(f"[DLQ] Failed to pop item from Redis queue: {e}")
        return self._queue.pop(0) if self._queue else None

class EventBus:
    def __init__(self, redis_url: Optional[str] = None):
        self._listeners: Dict[str, List[Callable[[Any], None]]] = {}
        self.redis_client = None

        url = redis_url or getattr(config, "REDIS_URL", None)
        if _HAS_REDIS and url:
            try:
                r = redis.Redis.from_url(url, decode_responses=True, socket_connect_timeout=0.5)
                r.ping()
                self.redis_client = r
                logger.info(f"[EventBus] Connected to Redis broker at {url}")
            except Exception as e:
                logger.debug(f"[EventBus] Redis broker unavailable ({e}), using resilient in-memory mode")

        self.dlq = DeadLetterQueue(redis_client=self.redis_client)

    def subscribe(self, event_pattern: str, callback: Callable[[Any], None]) -> None:
        if event_pattern not in self._listeners:
            self._listeners[event_pattern] = []
        self._listeners[event_pattern].append(callback)

    def publish(self, event_or_name: Any, payload: Optional[Any] = None) -> None:
        if payload is not None:
            event_type = str(event_or_name)
            event_data = payload
        elif isinstance(event_or_name, dict) and "eventType" in event_or_name:
            event_type = event_or_name["eventType"]
            event_data = event_or_name
        else:
            event_type = getattr(event_or_name, "eventType", str(type(event_or_name).__name__))
            event_data = event_or_name

        # Publish to Redis broker if connected
        if self.redis_client:
            try:
                serialized = json.dumps(event_data if isinstance(event_data, dict) else getattr(event_data, "__dict__", str(event_data)), default=str)
                self.redis_client.publish(f"gieni_events:{event_type}", serialized)
            except Exception as e:
                logger.debug(f"[EventBus] Redis publish failed ({e}), relying on local dispatch")

        handled = False
        for pattern, callbacks in self._listeners.items():
            if pattern == "*" or fnmatch.fnmatch(event_type, pattern) or pattern == event_type:
                for cb in callbacks:
                    try:
                        cb(event_data)
                        handled = True
                    except Exception as e:
                        logger.error(f"[EventBus] Error in callback for event {event_type}: {e}", exc_info=True)
                        self.dlq.push({"event": event_data, "error": str(e)})

        if not handled and event_type != "*":
            logger.debug(f"[EventBus] No listeners registered for event pattern '{event_type}'")
