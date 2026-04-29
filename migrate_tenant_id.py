#!/usr/bin/env python3
"""
Migration : Ajouter tenant_id sur toutes les tables principales
Associe toutes les données existantes au tenant owner (ID=1)
"""
from sqlalchemy import text
from app.core.database import engine, SessionLocal


TABLES_TO_MIGRATE = [
    "prospects",
    "clients",
    "email_logs",
    "conversations",
    "activity_logs",
    "devis",
    "factures",
    "chantiers"
]


def add_tenant_id_column(table_name: str):
    """Ajoute colonne tenant_id à une table."""
    with engine.connect() as conn:
        try:
            # Vérifier si la colonne existe déjà
            check_query = text(f"""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='{table_name}' AND column_name='tenant_id'
            """)
            result = conn.execute(check_query)
            if result.fetchone():
                print(f"  ⏭️  {table_name}: tenant_id existe déjà")
                return

            # Ajouter colonne tenant_id (nullable)
            conn.execute(text(f"""
                ALTER TABLE {table_name}
                ADD COLUMN tenant_id INTEGER REFERENCES tenants(id) ON DELETE CASCADE
            """))
            conn.commit()

            print(f"  ✅ {table_name}: Colonne tenant_id ajoutée")

            # Associer toutes les lignes existantes au tenant owner (ID=1)
            conn.execute(text(f"""
                UPDATE {table_name}
                SET tenant_id = 1
                WHERE tenant_id IS NULL
            """))
            conn.commit()

            # Compter lignes migrées
            count_query = text(f"SELECT COUNT(*) FROM {table_name} WHERE tenant_id = 1")
            count = conn.execute(count_query).scalar()
            print(f"     → {count} lignes associées au tenant owner")

        except Exception as e:
            print(f"  ❌ {table_name}: Erreur - {e}")
            conn.rollback()


if __name__ == "__main__":
    print("=" * 60)
    print("🔄 Migration tenant_id sur tables existantes")
    print("=" * 60)
    print(f"\nTables à migrer : {len(TABLES_TO_MIGRATE)}")
    print()

    for table in TABLES_TO_MIGRATE:
        add_tenant_id_column(table)

    print("\n" + "=" * 60)
    print("✅ Migration terminée !")
    print("=" * 60)
    print("\nToutes les données existantes sont maintenant associées")
    print("au tenant owner (Proprexis, ID=1)")
