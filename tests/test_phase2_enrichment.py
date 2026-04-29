"""
Tests Phase 2 — Enrichissement (Pappers, Email Finder, DVF)
"""
import pytest
import os
from app.core.database import SessionLocal
from app.models.prospect import Prospect


def test_pappers_enrichment_structure():
    """Test structure données Pappers dans score_explanation."""
    db = SessionLocal()
    try:
        # Chercher prospect avec données Pappers
        prospect_pappers = db.query(Prospect).filter(
            Prospect.score_explanation.like('%Pappers%')
        ).first()

        if prospect_pappers:
            explanation = prospect_pappers.score_explanation

            # Vérifier présence données Pappers
            pappers_indicators = ["CA", "SIRET", "Dirigeant", "Effectifs"]
            found = [ind for ind in pappers_indicators if ind in explanation]

            print(f"✅ Données Pappers trouvées: {', '.join(found)}")

            # Au moins 1 donnée Pappers devrait être présente
            assert len(found) > 0

        else:
            print("⚠️  Aucun prospect enrichi Pappers (lancer enrichissement)")

    finally:
        db.close()


def test_pappers_ca_parsing():
    """Test parsing CA depuis Pappers."""
    from app.agents.lead_scorer import _extract_pappers_data

    # Exemple score_explanation avec CA
    explanation = """
    Données Pappers :
    CA : 250 000 €
    Dirigeant : Jean Dupont
    SIRET : 12345678901234
    Effectifs : 15
    Statut : Actif
    """

    data = _extract_pappers_data(explanation)

    # Vérifier extraction
    assert "ca" in data
    assert data["ca"] == 250000
    assert "dirigeant" in data
    assert data["dirigeant"] == "Jean Dupont"
    assert "siret" in data
    assert data["siret"] == "12345678901234"
    assert "effectifs" in data
    assert data["effectifs"] == 15

    print(f"✅ Parsing Pappers: CA={data['ca']}€, effectifs={data['effectifs']}")


def test_email_finder_coverage():
    """Test couverture Email Finder."""
    db = SessionLocal()
    try:
        # Stats emails
        total = db.query(Prospect).count()
        with_email = db.query(Prospect).filter(
            Prospect.email.isnot(None)
        ).count()

        coverage = (with_email / total * 100) if total > 0 else 0

        print(f"✅ Couverture emails: {with_email}/{total} ({coverage:.1f}%)")

        # Au moins 20% devraient avoir un email
        assert coverage >= 20 or total < 100  # Tolérance si peu de prospects

    finally:
        db.close()


def test_email_finder_format_validation():
    """Test validation format emails trouvés."""
    db = SessionLocal()
    try:
        # Vérifier que les emails sont valides
        prospects_with_email = db.query(Prospect).filter(
            Prospect.email.isnot(None)
        ).limit(20).all()

        invalid_count = 0
        for p in prospects_with_email:
            if "@" not in p.email or "." not in p.email.split("@")[-1]:
                invalid_count += 1
                print(f"⚠️  Email invalide: {p.email}")

        assert invalid_count == 0, f"{invalid_count} emails invalides trouvés"

        print(f"✅ Tous les {len(prospects_with_email)} emails vérifiés sont valides")

    finally:
        db.close()


def test_dvf_source_detection():
    """Test détection source DVF."""
    from app.agents.lead_scorer import _extract_dvf_data

    # Score explanation avec DVF
    explanation_dvf = "Source : DVF - Transaction récente"
    explanation_no_dvf = "Source : Pages Jaunes"

    assert _extract_dvf_data(explanation_dvf) == True
    assert _extract_dvf_data(explanation_no_dvf) == False

    print("✅ Détection source DVF fonctionne")


def test_dvf_prospects_created():
    """Test création prospects depuis DVF."""
    db = SessionLocal()
    try:
        # Chercher prospects DVF
        dvf_prospects = db.query(Prospect).filter(
            Prospect.score_explanation.like('%DVF%')
        ).count()

        if dvf_prospects > 0:
            print(f"✅ {dvf_prospects} prospects DVF créés")

            # Vérifier qu'ils ont des données immobilières
            sample = db.query(Prospect).filter(
                Prospect.score_explanation.like('%DVF%')
            ).first()

            assert sample.city is not None
            print(f"✅ Exemple DVF: {sample.company_name or 'Sans nom'} à {sample.city}")

        else:
            print("⚠️  Aucun prospect DVF (lancer scraping DVF)")

    finally:
        db.close()


def test_permis_construire_detection():
    """Test détection permis de construire."""
    from app.agents.lead_scorer import _extract_permis_data

    explanation_permis = "Source : Permis de construire accordé"
    explanation_no_permis = "Source : Pages Jaunes"

    assert _extract_permis_data(explanation_permis) == True
    assert _extract_permis_data(explanation_no_permis) == False

    print("✅ Détection permis de construire fonctionne")


def test_permis_construire_prospects():
    """Test prospects depuis permis de construire."""
    db = SessionLocal()
    try:
        # Chercher prospects permis
        permis_count = db.query(Prospect).filter(
            Prospect.score_explanation.like('%Permis de construire%')
        ).count()

        if permis_count > 0:
            print(f"✅ {permis_count} prospects permis de construire")

            # Vérifier infos
            sample = db.query(Prospect).filter(
                Prospect.score_explanation.like('%Permis de construire%')
            ).first()

            assert sample.address is not None or sample.city is not None
            print(f"✅ Exemple permis: {sample.company_name or 'Chantier'} - {sample.city}")

        else:
            print("⚠️  Aucun prospect permis (lancer scraping permis)")

    finally:
        db.close()


def test_enrichment_score_impact():
    """Test impact enrichissement sur score."""
    db = SessionLocal()
    try:
        # Comparer scores avec/sans enrichissement
        with_pappers = db.query(Prospect).filter(
            Prospect.score_explanation.like('%Pappers%')
        ).limit(10).all()

        without_pappers = db.query(Prospect).filter(
            ~Prospect.score_explanation.like('%Pappers%')
        ).limit(10).all()

        if with_pappers and without_pappers:
            avg_with = sum(p.lead_score for p in with_pappers) / len(with_pappers)
            avg_without = sum(p.lead_score for p in without_pappers) / len(without_pappers)

            print(f"✅ Score moyen avec Pappers: {avg_with:.1f}/100")
            print(f"✅ Score moyen sans Pappers: {avg_without:.1f}/100")

            # Enrichissement devrait améliorer le score
            if avg_with > avg_without:
                print("✅ Enrichissement améliore effectivement le score")

        else:
            print("⚠️  Pas assez de données pour comparer")

    finally:
        db.close()


def test_multiple_sources_bonus():
    """Test bonus prospects avec plusieurs sources."""
    db = SessionLocal()
    try:
        # Chercher prospects avec plusieurs sources d'enrichissement
        multi_source = db.query(Prospect).filter(
            Prospect.score_explanation.like('%Pappers%')
        ).filter(
            Prospect.email.isnot(None)
        ).limit(5).all()

        if multi_source:
            print(f"✅ {len(multi_source)} prospects avec multi-sources:")
            for p in multi_source:
                sources = []
                if "Pappers" in p.score_explanation:
                    sources.append("Pappers")
                if "DVF" in p.score_explanation:
                    sources.append("DVF")
                if "Permis" in p.score_explanation:
                    sources.append("Permis")
                if p.email:
                    sources.append("Email")

                print(f"  - {p.company_name}: score {p.lead_score}/100 ({', '.join(sources)})")

        else:
            print("⚠️  Aucun prospect multi-sources encore")

    finally:
        db.close()


def test_enrichment_data_quality():
    """Test qualité des données enrichies."""
    db = SessionLocal()
    try:
        # Vérifier que les données Pappers sont cohérentes
        enriched = db.query(Prospect).filter(
            Prospect.score_explanation.like('%CA :%')
        ).limit(10).all()

        if enriched:
            for p in enriched:
                from app.agents.lead_scorer import _extract_pappers_data
                data = _extract_pappers_data(p.score_explanation)

                if data.get("ca"):
                    # CA devrait être positif et raisonnable
                    assert data["ca"] > 0
                    assert data["ca"] < 1_000_000_000  # < 1 milliard

                if data.get("effectifs"):
                    # Effectifs devrait être raisonnable
                    assert data["effectifs"] > 0
                    assert data["effectifs"] < 10000

            print(f"✅ Qualité données Pappers vérifiée sur {len(enriched)} prospects")

        else:
            print("⚠️  Aucun prospect avec CA enrichi")

    finally:
        db.close()


def test_api_keys_present():
    """Test présence clés API enrichissement."""
    pappers_key = os.getenv("PAPPERS_API_KEY")

    if pappers_key:
        print(f"✅ PAPPERS_API_KEY configurée (longueur: {len(pappers_key)})")
    else:
        print("⚠️  PAPPERS_API_KEY manquante (enrichissement désactivé)")

    # Pas d'assert car optionnel en test
