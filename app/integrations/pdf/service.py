import asyncio
import time
from typing import Dict, Optional
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from app.integrations.shared.logger import IntegrationLogger
from app.config import settings
import redis.asyncio as redis
import sentry_sdk
import os

redis_client: Optional[redis.Redis] = None


async def get_redis_client() -> redis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(settings.REDIS_URL)
    assert redis_client is not None
    return redis_client


class PdfService:
    def __init__(self):
        template_dir = os.path.join(os.path.dirname(__file__), "templates")
        self.env = Environment(loader=FileSystemLoader(template_dir))

    async def generate_checklist_pdf(
        self,
        checklist_data: Dict,
        language: str = "EN"
    ) -> bytes:
        start_time = time.time()
        checklist_id = checklist_data.get("id", "unknown")
        cache_key = f"pdf:{checklist_id}:{language}"
        
        r = await get_redis_client()
        cached = await r.get(cache_key)
        if cached is not None:
            IntegrationLogger.log_call(
                integration="pdf",
                method="generate_checklist_pdf",
                latency_ms=(time.time() - start_time) * 1000,
                cache_hit=True,
                status="success"
            )
            return cached
        
        try:
            template_name = "checklist_en.html" if language == "EN" else "checklist_es.html"
            template = self.env.get_template(template_name)
            html_content = template.render(**checklist_data)
            
            pdf_bytes = await asyncio.to_thread(
                lambda: HTML(string=html_content).write_pdf()
            )
            
            await r.setex(cache_key, settings.CACHE_TTL_PDF, pdf_bytes)
            
            IntegrationLogger.log_call(
                integration="pdf",
                method="generate_checklist_pdf",
                latency_ms=(time.time() - start_time) * 1000,
                cache_hit=False,
                status="success"
            )
            
            return pdf_bytes
        except Exception as e:
            sentry_sdk.capture_exception(e)
            # Return a minimal fallback PDF placeholder
            return b"PDF generation failed - please call 211 for assistance"
