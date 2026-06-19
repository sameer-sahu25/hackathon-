import asyncio
import logging
from alembic.config import Config
from alembic import command
from sqlalchemy import text, select
from app.db.session import async_engine
from app.db.models.base_model import BaseModel
from app.db.models.analytics import AnalyticsEvent
from app.db.models import (
    User, Resource, RightsCard
)
from datetime import datetime, UTC

logger = logging.getLogger(__name__)


async def init_db():
    """Initialize database with Alembic and seed data"""
    logger.info("Starting database initialization...")
    
    # Run Alembic migrations programmatically
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    logger.info("Alembic migrations applied successfully!")
    
    # Seed initial data
    await seed_data()
    await seed_demo_data()
    logger.info("Database initialization complete!")


async def seed_data():
    """Seed initial rights cards and resources"""
    # Sample rights cards for 5 demo states (EN and ES)
    states = ["CA", "TX", "NY", "FL", "IL"]
    languages = ["EN", "ES"]
    
    rights_data = {
        "CA": {
            "headline": "California Renters' Rights Overview",
            "notice_requirement": "30 days for eviction",
            "can_be_evicted_for": ["Non-payment", "Lease violation"],
            "cannot_be_evicted_for": ["Retaliation", "Discrimination"],
            "key_protections": ["Rent control in some cities", "Just cause eviction"],
            "rent_control_applies": True,
            "just_cause_required": True
        },
        "TX": {
            "headline": "Texas Renters' Rights Overview",
            "notice_requirement": "30 days for eviction",
            "can_be_evicted_for": ["Non-payment", "Lease violation"],
            "cannot_be_evicted_for": ["Retaliation", "Discrimination"],
            "key_protections": ["30-day notice requirement"],
            "rent_control_applies": False,
            "just_cause_required": False
        },
        "NY": {
            "headline": "New York Renters' Rights Overview",
            "notice_requirement": "30 days for eviction",
            "can_be_evicted_for": ["Non-payment", "Lease violation"],
            "cannot_be_evicted_for": ["Retaliation", "Discrimination"],
            "key_protections": ["Rent control in NYC", "Just cause eviction"],
            "rent_control_applies": True,
            "just_cause_required": True
        },
        "FL": {
            "headline": "Florida Renters' Rights Overview",
            "notice_requirement": "3 days for eviction",
            "can_be_evicted_for": ["Non-payment", "Lease violation"],
            "cannot_be_evicted_for": ["Retaliation", "Discrimination"],
            "key_protections": ["3-day notice requirement"],
            "rent_control_applies": False,
            "just_cause_required": False
        },
        "IL": {
            "headline": "Illinois Renters' Rights Overview",
            "notice_requirement": "30 days for eviction",
            "can_be_evicted_for": ["Non-payment", "Lease violation"],
            "cannot_be_evicted_for": ["Retaliation", "Discrimination"],
            "key_protections": ["30-day notice requirement"],
            "rent_control_applies": False,
            "just_cause_required": True
        }
    }
    
    async with async_engine.begin() as conn:
        from sqlalchemy.ext.asyncio import AsyncSession
        async with AsyncSession(async_engine) as session:
            from app.db.repositories.analytics_repo import AnalyticsRepository
            
            # Seed initial analytics event
            analytics_repo = AnalyticsRepository(session)
            await analytics_repo.log_event("system_initialized")
            
            # Seed rights cards
            for state in states:
                for lang in languages:
                    result = await session.execute(
                        select(RightsCard).where(
                            RightsCard.state == state,
                            RightsCard.language == lang,
                            RightsCard.is_deleted == False
                        )
                    )
                    existing = result.scalar_one_or_none()
                    
                    if not existing:
                        data = rights_data[state].copy()
                        data['state'] = state
                        data['language'] = lang
                        data['full_content'] = data.copy()
                        data['generated_by_model'] = 'demo'
                        data['is_current'] = True
                        rc = RightsCard(**data)
                        session.add(rc)
            
            await session.commit()


async def seed_demo_data():
    """Seed demo data for testing and presentation"""
    logger.info("Seeding demo data...")
    
    demo_resources = [
        # California Resources
        {
            "name": "Bay Area Legal Aid",
            "resource_type": "LEGAL_AID",
            "description": "Free legal assistance for renters",
            "state": "CA",
            "county": "San Francisco",
            "city": "San Francisco",
            "phone": "+1-415-477-9000",
            "url": "https://baylegal.org",
            "languages_supported": ["EN", "ES"],
            "is_active": True,
            "source": "MANUAL"
        },
        {
            "name": "ERAP California",
            "resource_type": "RENTAL_ASSISTANCE",
            "description": "Emergency Rental Assistance Program for California",
            "state": "CA",
            "url": "https://ca.gov/erap",
            "is_active": True,
            "source": "MANUAL"
        },
        
        # Texas Resources
        {
            "name": "Texas RioGrande Legal Aid",
            "resource_type": "LEGAL_AID",
            "description": "Free legal help for low-income Texans",
            "state": "TX",
            "county": "Travis",
            "city": "Austin",
            "phone": "+1-888-988-9996",
            "url": "https://trla.org",
            "languages_supported": ["EN", "ES"],
            "is_active": True,
            "source": "MANUAL"
        },
        {
            "name": "Texas Emergency Rental Assistance",
            "resource_type": "RENTAL_ASSISTANCE",
            "description": "Emergency Rental Assistance Program for Texas",
            "state": "TX",
            "url": "https://texasrentrelief.com",
            "is_active": True,
            "source": "MANUAL"
        },
        
        # New York Resources
        {
            "name": "Legal Aid Society",
            "resource_type": "LEGAL_AID",
            "description": "Free legal assistance to low-income New Yorkers",
            "state": "NY",
            "county": "New York",
            "city": "New York",
            "phone": "+1-844-385-7234",
            "url": "https://legal-aid.org",
            "languages_supported": ["EN", "ES"],
            "is_active": True,
            "source": "MANUAL"
        },
        
        # Florida Resources
        {
            "name": "Florida Legal Services",
            "resource_type": "LEGAL_AID",
            "description": "Free civil legal aid for low-income Floridians",
            "state": "FL",
            "city": "Miami",
            "phone": "+1-800-342-8011",
            "url": "https://floridalegalservices.org",
            "languages_supported": ["EN", "ES"],
            "is_active": True,
            "source": "MANUAL"
        },
        
        # Illinois Resources
        {
            "name": "LA Chicago",
            "resource_type": "LEGAL_AID",
            "description": "Legal Assistance Foundation of Metropolitan Chicago",
            "state": "IL",
            "city": "Chicago",
            "phone": "+1-312-939-1663",
            "url": "https://lafchicago.org",
            "languages_supported": ["EN", "ES"],
            "is_active": True,
            "source": "MANUAL"
        }
    ]
    
    async with async_engine.begin() as conn:
        from sqlalchemy.ext.asyncio import AsyncSession
        async with AsyncSession(async_engine) as session:
            from app.db.repositories.resource_repo import ResourceRepository
            repo = ResourceRepository(session)
            
            for data in demo_resources:
                # Check if resource already exists by name and state
                result = await session.execute(
                    select(Resource).where(
                        Resource.name == data['name'],
                        Resource.state == data['state'],
                        Resource.is_deleted == False
                    )
                )
                existing = result.scalar_one_or_none()
                
                if not existing:
                    await repo.create(data)
            await session.commit()
            
            logger.info("Demo data seeded!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(init_db())
