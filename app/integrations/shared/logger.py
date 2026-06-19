import logging
import json
import time
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class IntegrationLogger:
    @staticmethod
    def log_call(
        integration: str,
        method: str,
        latency_ms: float,
        cache_hit: bool = False,
        status: str = "success",
        circuit_state: str = "closed",
        extra: Optional[Dict[str, Any]] = None
    ):
        log_data = {
            "integration": integration,
            "method": method,
            "latency_ms": latency_ms,
            "cache_hit": cache_hit,
            "status": status,
            "circuit_state": circuit_state,
            "timestamp": time.time()
        }
        if extra:
            log_data.update(extra)
        logger.info(json.dumps(log_data))
