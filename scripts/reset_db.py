import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import Base, engine
from app.models import prospect  # important : charge le modèle

print("\n⚠️  Cette action va supprimer toutes les données existantes.")
confirm = input("   Tape 'oui' pour confirmer : ").strip().lower()

if confirm != "oui":
    print("❌ Annulé.")
    exit()

print("\n🗑  Suppression de la table...")
Base.metadata.drop_all(bind=engine)

print("🔨 Recréation de la table...")
Base.metadata.create_all(bind=engine)

print("✅ Base de données réinitialisée avec le nouveau schéma.\n")
print("   Lance maintenant : python3 run_pipeline.py\n")