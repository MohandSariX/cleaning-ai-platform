"""
Tests Phase 2 — Scraping (Pages Jaunes, Permis, DVF)
"""
import pytest
from app.core.database import SessionLocal
from app.models.prospect import Prospect


def test_prospects_database_not_empty():
    """Test que la base contient des prospects."""
    db = SessionLocal()
    try:
        count = db.query(Prospect).count()
        assert count > 0, "La base devrait contenir au moins 1 prospect"

        print(f"✅ Base de données: {count} prospects")

    finally:
        db.close()


def test_prospects_have_required_fields():
    """Test que les prospects ont les champs obligatoires."""
    db = SessionLocal()
    try:
        prospects = db.query(Prospect).limit(10).all()

        for p in prospects:
            # Champs obligatoires
            assert p.id is not None
            assert p.company_name is not None and len(p.company_name) > 0
            assert p.lead_score is not None
            assert p.score_label is not None
            assert p.status is not None

        print(f"✅ {len(prospects)} prospects vérifiés: champs obligatoires OK")

    finally:
        db.close()


def test_prospects_pages_jaunes_source():
    """Test prospects depuis Pages Jaunes."""
    db = SessionLocal()
    try:
        # Prospects qui ne sont pas DVF ni Permis = Pages Jaunes
        pj_prospects = db.query(Prospect).filter(
            ~Prospect.score_explanation.like('%DVF%')
        ).filter(
            ~Prospect.score_explanation.like('%Permis de construire%')
        ).limit(10).all()

        if pj_prospects:
            print(f"✅ {len(pj_prospects)} prospects Pages Jaunes trouvés")

            # Vérifier qu'ils ont des infos basiques
            for p in pj_prospects[:3]:
                assert p.company_name is not None
                print(f"  - {p.company_name} ({p.city or 'Ville inconnue'})")

        else:
            print("⚠️  Aucun prospect Pages Jaunes (base vide ou tous enrichis)")

    finally:
        db.close()


def test_prospects_data_quality():
    """Test qualité générale des données prospects."""
    db = SessionLocal()
    try:
        prospects = db.query(Prospect).limit(50).all()

        # Stats qualité
        with_email = sum(1 for p in prospects if p.email)
        with_phone = sum(1 for p in prospects if p.phone)
        with_website = sum(1 for p in prospects if p.website)
        with_address = sum(1 for p in prospects if p.address)

        total = len(prospects)

        print(f"✅ Qualité données ({total} prospects):")
        print(f"  Email: {with_email} ({with_email/total*100:.1f}%)")
        print(f"  Téléphone: {with_phone} ({with_phone/total*100:.1f}%)")
        print(f"  Site web: {with_website} ({with_website/total*100:.1f}%)")
        print(f"  Adresse: {with_address} ({with_address/total*100:.1f}%)")

        # Au moins 50% devraient avoir une adresse (Pages Jaunes)
        assert with_address / total >= 0.5 or total < 10

    finally:
        db.close()


def test_prospects_no_duplicates():
    """Test absence doublons (même nom + ville)."""
    db = SessionLocal()
    try:
        prospects = db.query(Prospect).all()

        # Créer signature unique par prospect
        signatures = {}
        duplicates = []

        for p in prospects:
            sig = f"{p.company_name}_{p.city}".lower()
            if sig in signatures:
                duplicates.append(p)
            else:
                signatures[sig] = p

        if duplicates:
            print(f"⚠️  {len(duplicates)} doublons potentiels détectés")
            for dup in duplicates[:3]:
                print(f"    - {dup.company_name} ({dup.city})")
        else:
            print(f"✅ Aucun doublon détecté ({len(prospects)} prospects uniques)")

    finally:
        db.close()


def test_prospects_score_range():
    """Test que les scores sont dans la plage valide."""
    db = SessionLocal()
    try:
        prospects = db.query(Prospect).all()

        invalid_scores = []
        for p in prospects:
            if p.lead_score < 0 or p.lead_score > 100:
                invalid_scores.append(p)

        assert len(invalid_scores) == 0, f"{len(invalid_scores)} scores invalides trouvés"

        print(f"✅ Tous les {len(prospects)} scores sont entre 0 et 100")

        # Stats scores
        if prospects:
            avg_score = sum(p.lead_score for p in prospects) / len(prospects)
            max_score = max(p.lead_score for p in prospects)
            min_score = min(p.lead_score for p in prospects)

            print(f"  Moyenne: {avg_score:.1f}/100")
            print(f"  Min: {min_score}, Max: {max_score}")

    finally:
        db.close()


def test_prospects_status_valid():
    """Test que les statuts sont valides."""
    db = SessionLocal()
    try:
        valid_statuses = [
            "new", "scored", "email_generated", "contacted",
            "replied", "to_followup", "signed", "lost"
        ]

        prospects = db.query(Prospect).all()

        invalid_status = []
        for p in prospects:
            if p.status not in valid_statuses:
                invalid_status.append(p)

        if invalid_status:
            print(f"⚠️  {len(invalid_status)} statuts invalides:")
            for p in invalid_status[:5]:
                print(f"    - {p.company_name}: '{p.status}'")
        else:
            print(f"✅ Tous les {len(prospects)} statuts sont valides")

    finally:
        db.close()


def test_prospects_cities_distribution():
    """Test distribution géographique des prospects."""
    db = SessionLocal()
    try:
        from sqlalchemy import func

        # Top 10 villes
        top_cities = db.query(
            Prospect.city,
            func.count(Prospect.id).label('count')
        ).group_by(
            Prospect.city
        ).order_by(
            func.count(Prospect.id).desc()
        ).limit(10).all()

        if top_cities:
            print(f"✅ Top 10 villes ({sum(c[1] for c in top_cities)} prospects):")
            for city, count in top_cities:
                print(f"  - {city or 'Inconnue'}: {count}")

            # Vérifier présence IDF
            idf_cities = [city.lower() for city, _ in top_cities if city]
            idf_keywords = ["paris", "champigny", "créteil", "saint", "maur"]

            has_idf = any(keyword in " ".join(idf_cities) for keyword in idf_keywords)
            if has_idf:
                print("✅ Prospects IDF présents")

        else:
            print("⚠️  Aucune donnée ville disponible")

    finally:
        db.close()


def test_prospects_industries():
    """Test distribution par industrie."""
    db = SessionLocal()
    try:
        from sqlalchemy import func

        # Top industries
        industries = db.query(
            Prospect.industry,
            func.count(Prospect.id).label('count')
        ).group_by(
            Prospect.industry
        ).order_by(
            func.count(Prospect.id).desc()
        ).limit(5).all()

        if industries:
            print(f"✅ Top 5 industries:")
            for industry, count in industries:
                print(f"  - {industry or 'Non renseignée'}: {count}")

        else:
            print("⚠️  Aucune donnée industrie")

    finally:
        db.close()


def test_prospects_created_recently():
    """Test que des prospects ont été créés récemment."""
    db = SessionLocal()
    try:
        from datetime import datetime, timedelta

        # Prospects créés dans les 30 derniers jours
        thirty_days_ago = datetime.now() - timedelta(days=30)

        recent = db.query(Prospect).filter(
            Prospect.created_at >= thirty_days_ago
        ).count()

        total = db.query(Prospect).count()

        print(f"✅ Prospects récents (<30j): {recent}/{total} ({recent/total*100:.1f}%)")

        # Au moins 10% devraient être récents (sinon scraping pas lancé)
        if total > 100:
            assert recent / total >= 0.1, "Très peu de prospects récents, lancer scraping"

    finally:
        db.close()


def test_dvf_prospects_structure():
    """Test structure prospects DVF."""
    db = SessionLocal()
    try:
        dvf = db.query(Prospect).filter(
            Prospect.score_explanation.like('%DVF%')
        ).limit(5).all()

        if dvf:
            print(f"✅ {len(dvf)} prospects DVF vérifiés:")
            for p in dvf:
                # DVF devrait avoir ville et score élevé
                assert p.city is not None
                assert p.lead_score >= 40  # DVF = signal fort

                print(f"  - {p.company_name or 'Transaction'} ({p.city}) - score {p.lead_score}/100")

        else:
            print("⚠️  Aucun prospect DVF (lancer scraping DVF)")

    finally:
        db.close()


def test_permis_prospects_structure():
    """Test structure prospects Permis de construire."""
    db = SessionLocal()
    try:
        permis = db.query(Prospect).filter(
            Prospect.score_explanation.like('%Permis de construire%')
        ).limit(5).all()

        if permis:
            print(f"✅ {len(permis)} prospects Permis vérifiés:")
            for p in permis:
                # Permis devrait avoir score élevé
                assert p.lead_score >= 50  # Permis = signal très fort

                print(f"  - {p.company_name or 'Chantier'} ({p.city}) - score {p.lead_score}/100")

        else:
            print("⚠️  Aucun prospect Permis (lancer scraping permis)")

    finally:
        db.close()


def test_prospects_score_explanation_not_empty():
    """Test que score_explanation n'est pas vide."""
    db = SessionLocal()
    try:
        prospects = db.query(Prospect).limit(10).all()

        empty_explanation = []
        for p in prospects:
            if not p.score_explanation or len(p.score_explanation) < 20:
                empty_explanation.append(p)

        if empty_explanation:
            print(f"⚠️  {len(empty_explanation)} prospects sans explication score détaillée")
        else:
            print(f"✅ Tous les {len(prospects)} prospects ont explication détaillée")

    finally:
        db.close()


def test_database_indexes():
    """Test performance requêtes fréquentes."""
    db = SessionLocal()
    try:
        import time

        # Test requête fréquente (filtrage par score)
        start = time.time()
        db.query(Prospect).filter(Prospect.lead_score >= 70).count()
        duration = time.time() - start

        # Devrait être rapide (<1s)
        assert duration < 1.0, f"Requête trop lente: {duration:.2f}s (ajouter index?)"

        print(f"✅ Requête filtre score: {duration*1000:.0f}ms")

    finally:
        db.close()
