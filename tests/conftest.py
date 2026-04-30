"""
Configuration pytest pour tests Proprexis
"""
import pytest
import os
from dotenv import load_dotenv

# Charger .env pour tests
load_dotenv()

# Importer tous les modèles pour SQLAlchemy
from app.models import (
    prospect, client, devis, chantier, facture,
    email_log, conversation, activity_log, ai_memory,
    tenant, product, escalation, devis_template
)


@pytest.fixture(scope="session")
def db_session():
    """Fixture pour session base de données."""
    from app.core.database import SessionLocal
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture
def sample_prospect():
    """Fixture prospect d'exemple pour tests."""
    return {
        "company_name": "Test Company",
        "email": "test@example.com",
        "phone": "0123456789",
        "city": "Paris",
        "lead_score": 50,
        "status": "new"
    }


@pytest.fixture
def groq_api_key():
    """Fixture clé API Groq."""
    key = os.getenv("GROQ_API_KEY")
    if not key:
        pytest.skip("GROQ_API_KEY not configured")
    return key
