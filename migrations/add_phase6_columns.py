"""
Migration Phase 6 — Devis avancés & Templates
Ajoute les colonnes manquantes pour :
- Signature électronique (devis.signature_data, signed_at, signed_by)
- Personnalisation tenant (tenant_config.logo_url, cgv_text, conditions_paiement, remise_max_pct)
- Table devis_templates
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.database import engine


def run_migration():
    """Exécute la migration Phase 6."""

    with engine.connect() as conn:
        print("🚀 Début migration Phase 6...")

        # 1. Ajouter colonnes signature à table devis
        try:
            conn.execute(text("""
                ALTER TABLE devis
                ADD COLUMN IF NOT EXISTS signature_data TEXT,
                ADD COLUMN IF NOT EXISTS signed_at TIMESTAMP,
                ADD COLUMN IF NOT EXISTS signed_by VARCHAR;
            """))
            conn.commit()
            print("✅ Colonnes signature ajoutées à table devis")
        except Exception as e:
            print(f"⚠️  Colonnes signature devis : {e}")

        # 2. Ajouter colonnes personnalisation à tenant_config
        try:
            conn.execute(text("""
                ALTER TABLE tenant_config
                ADD COLUMN IF NOT EXISTS logo_url VARCHAR,
                ADD COLUMN IF NOT EXISTS cgv_text TEXT,
                ADD COLUMN IF NOT EXISTS conditions_paiement VARCHAR DEFAULT 'Comptant',
                ADD COLUMN IF NOT EXISTS remise_max_pct FLOAT DEFAULT 15.0;
            """))
            conn.commit()
            print("✅ Colonnes personnalisation ajoutées à tenant_config")
        except Exception as e:
            print(f"⚠️  Colonnes tenant_config : {e}")

        # 3. Créer table devis_templates
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS devis_templates (
                    id SERIAL PRIMARY KEY,
                    tenant_id INTEGER REFERENCES tenants(id) ON DELETE CASCADE,
                    name VARCHAR NOT NULL,
                    category VARCHAR,
                    type_prestation VARCHAR,
                    template_json JSON NOT NULL DEFAULT '{}',
                    variables_required JSON NOT NULL DEFAULT '[]',
                    is_default BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            conn.commit()
            print("✅ Table devis_templates créée")
        except Exception as e:
            print(f"⚠️  Table devis_templates : {e}")

        # 4. Créer index pour performances
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_devis_templates_tenant
                ON devis_templates(tenant_id);
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_devis_templates_category
                ON devis_templates(category);
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_devis_templates_type
                ON devis_templates(type_prestation);
            """))
            conn.commit()
            print("✅ Index créés")
        except Exception as e:
            print(f"⚠️  Index : {e}")

        print("🎉 Migration Phase 6 terminée avec succès!")


if __name__ == "__main__":
    run_migration()
