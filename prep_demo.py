import asyncio
import os
from app.config import settings
from app.integrations.pdf.service import PdfService
from app.integrations.twilio.service import TwilioService
from app.integrations.shared.fallbacks import FALLBACK_DATA
import redis.asyncio as redis

async def prep_demo():
    """Prep the demo: pre-sync resources, pre-generate PDFs, warm up caches!"""
    print("=== Preparing Demo ===")
    
    # 1. Pre-generate sample PDFs
    print("Generating sample PDFs...")
    pdf_service = PdfService()
    
    sample_checklist_en = {
        "id": "sample_en",
        "state": "TX",
        "court_date": "2026-07-15",
        "court_address": "123 Justice St, Austin, TX",
        "documents_needed": [
            "Lease agreement",
            "Proof of payment",
            "Photo ID"
        ]
    }
    
    sample_checklist_es = {
        "id": "sample_es",
        "state": "TX",
        "court_date": "2026-07-15",
        "court_address": "123 Justice St, Austin, TX",
        "documents_needed": [
            "Contrato de arrendamiento",
            "Prueba de pago",
            "Identificación con foto"
        ]
    }
    
    await pdf_service.generate_checklist_pdf(sample_checklist_en, language="EN")
    await pdf_service.generate_checklist_pdf(sample_checklist_es, language="ES")
    print("✅ Sample PDFs generated!")
    
    # 2. Pre-warm caches with fallback data
    print("Warming up caches with fallback data...")
    r = await redis.from_url(settings.REDIS_URL)
    
    for state in FALLBACK_DATA.keys():
        await r.setex(f"hud:{state}:all", 3600, str([
            {
                "name": "Housing Assistance (Local)",
                "description": "Local housing resources available - call 211 for details",
                "state": state,
                "county": None,
                "eligibility": "Contact 211 for eligibility info",
                "website": "https://211.org",
                "phone": "211",
                "source": "FALLBACK_HUD"
            } for _ in range(3)
        ] + FALLBACK_DATA[state]))
        
        await r.setex(f"211:all:all", 3600, str(FALLBACK_DATA[state]))
        
        print(f"✅ Pre-warmed cache for {state}!")
    
    print("\n=== Demo Prep Complete! ===")
    print("You're ready to show the Housing Stability AI Guide!")


if __name__ == "__main__":
    asyncio.run(prep_demo())
