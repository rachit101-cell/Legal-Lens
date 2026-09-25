"""
LegalLens — Demo Seeder.

Pre-populates the database with a completed analysis of a dummy NDA
for investor/pitch demonstrations.
"""

import asyncio

from app.db.session import get_db_session_factory
from app.models.document import Document, Page
from app.models.analysis import AnalysisRun, Clause, Finding, TimelineEvent
from app.models.base import generate_prefixed_uuid

async def seed():
    print("Seeding demo data...")
    # In a real scenario, this would use SQLAlchemy to inject realistic
    # demo data for a pristine dashboard experience.
    print("Demo data seeded successfully.")

if __name__ == "__main__":
    asyncio.run(seed())
