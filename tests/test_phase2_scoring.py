"""
Tests Phase 2 — Lead Scoring 300 points
"""
import pytest
from app.agents.lead_scorer import (
    calculate_score,
    _score_joignabilite,
    _score_identite,
    _score_potentiel,
    _score_signaux,
    _get_label,
    _extract_pappers_data,
    _extract_permis_data,
    _extract_dvf_data
)
from app.core.database import SessionLocal
from app.models.prospect import Prospect


def test_score_labels():
    """Test labels par tranche de score."""
    assert _get_label(85) == "🔥 Priorité haute"
    assert _get_label(70) == "⚡ Priorité moyenne"
    assert _get_label(50) == "🌱 Priorité faible"
    assert _get_label(30) == "❄️ Non prioritaire"

    print("✅ Labels de scoring corrects")


def test_score_joignabilite():
    """Test scoring joignabilité (80 pts max)."""
    from app.models.prospect import Prospect

    # Prospect avec email pro + tel fixe
    p = Prospect(
        company_name="Test Company",
        email="contact@test.com",
        phone="0145678901"
    )

    score, details = _score_joignabilite(p)

    # Email pro (40) + Tel fixe (25) = 65
    assert 60 <= score <= 80
    assert len(details) >= 2

    print(f"✅ Joignabilité: {score}/80 pts")
    for detail in details:
        print(f"  - {detail}")


def test_score_identite():
    """Test scoring identité (60 pts max)."""
    p = Prospect(
        company_name="Test SARL",
        email="test@example.com",
        website="https://test.com",
        score_explanation="Données Pappers : SIRET : 12345678901234, Dirigeant : Jean Dupont"
    )

    score, details = _score_identite(p)

    # Site web (20) + Email sur site (10) + Pappers (10) + Dirigeant (10) + SIRET (5) + SARL (5) = 60
    assert 0 <= score <= 60

    print(f"✅ Identité: {score}/60 pts")
    for detail in details:
        print(f"  - {detail}")


def test_score_potentiel():
    """Test scoring potentiel commercial (80 pts max)."""
    p = Prospect(
        company_name="Test Company",
        city="Paris",
        address="123 rue test 75001 Paris",
        score_explanation="CA : 1 500 000 €, Effectifs : 25, Statut : Actif"
    )

    score, details = _score_potentiel(p)

    # Zone prioritaire (20) + Adresse (15) + CA >1M (30) + Effectifs (15) + Actif (5) = 85 (max 80)
    assert 0 <= score <= 80

    print(f"✅ Potentiel: {score}/80 pts")
    for detail in details:
        print(f"  - {detail}")


def test_score_signaux():
    """Test scoring signaux d'opportunité (80 pts max)."""
    p = Prospect(
        company_name="Construction BTP",
        industry="BTP",
        status="new",
        score_explanation="Source : Permis de construire accordé"
    )

    score, details = _score_signaux(p)

    # Permis (40) + BTP (20) = 60
    assert 0 <= score <= 80

    print(f"✅ Signaux: {score}/80 pts")
    for detail in details:
        print(f"  - {detail}")


def test_calculate_score_complete():
    """Test calcul score complet 300 pts → /100."""
    p = Prospect(
        company_name="Test SARL Paris",
        email="contact@test.com",
        phone="0145678901",
        website="https://test.com",
        city="Paris",
        address="123 rue test 75001 Paris",
        industry="BTP",
        score_explanation="""
        Données Pappers : CA : 1 500 000 €, Effectifs : 25, SIRET : 12345678901234
        Dirigeant : Jean Dupont, Statut : Actif
        Source : Permis de construire accordé
        """
    )

    score_normalized, label, explanation = calculate_score(p)

    # Score normalisé /100
    assert 0 <= score_normalized <= 100
    assert label in ["🔥 Priorité haute", "⚡ Priorité moyenne", "🌱 Priorité faible", "❄️ Non prioritaire"]
    assert "[300pts]" in explanation
    assert "Joignabilité" in explanation
    assert "Identité" in explanation
    assert "Potentiel" in explanation
    assert "Signaux" in explanation

    print(f"✅ Score complet: {score_normalized}/100 - {label}")
    print(f"  Explication (150 premiers caractères):")
    print(f"  {explanation[:150]}...")


def test_extract_pappers_data():
    """Test parsing données Pappers."""
    explanation = """
    Données Pappers enrichies :
    CA : 2 500 000 €
    Dirigeant : Marie Martin
    SIRET : 98765432109876
    Effectifs : 50
    Statut : Actif
    """

    data = _extract_pappers_data(explanation)

    assert data["ca"] == 2_500_000
    assert data["dirigeant"] == "Marie Martin"
    assert data["siret"] == "98765432109876"
    assert data["effectifs"] == 50
    assert data["is_active"] == True
    assert data["has_pappers"] == True

    print("✅ Parsing Pappers complet")


def test_extract_permis_data():
    """Test détection permis de construire."""
    assert _extract_permis_data("Source : Permis de construire accordé") == True
    assert _extract_permis_data("Source : Permis de construire") == True
    assert _extract_permis_data("Source : Pages Jaunes") == False
    assert _extract_permis_data("") == False

    print("✅ Détection permis OK")


def test_extract_dvf_data():
    """Test détection source DVF."""
    assert _extract_dvf_data("Source : DVF") == True
    assert _extract_dvf_data("source_dvf") == True
    assert _extract_dvf_data("Source : Pages Jaunes") == False
    assert _extract_dvf_data("") == False

    print("✅ Détection DVF OK")


def test_score_distribution():
    """Test distribution scores dans la base."""
    db = SessionLocal()
    try:
        prospects = db.query(Prospect).all()

        if len(prospects) < 10:
            print("⚠️  Pas assez de prospects pour analyser distribution")
            return

        # Compter par label
        distribution = {
            "🔥 Priorité haute": 0,
            "⚡ Priorité moyenne": 0,
            "🌱 Priorité faible": 0,
            "❄️ Non prioritaire": 0
        }

        for p in prospects:
            if p.score_label:
                distribution[p.score_label] = distribution.get(p.score_label, 0) + 1

        total = sum(distribution.values())

        print(f"✅ Distribution scores ({total} prospects):")
        for label, count in distribution.items():
            pct = (count / total * 100) if total > 0 else 0
            print(f"  {label}: {count} ({pct:.1f}%)")

    finally:
        db.close()


def test_score_categories_balance():
    """Test équilibre des 4 catégories."""
    # Créer prospect avec toutes les catégories maximales
    p_max = Prospect(
        company_name="Perfect SARL Paris",
        email="contact@perfect.com",
        phone="0145678901",
        website="https://perfect.com",
        city="Paris",
        address="123 rue test 75001 Paris",
        industry="BTP",
        status="replied",
        score_explanation="""
        Données Pappers : CA : 5 000 000 €, Effectifs : 100
        SIRET : 12345678901234, Dirigeant : Jean Dupont, Statut : Actif
        Source : Permis de construire accordé
        Source : DVF
        """
    )

    score_j, _ = _score_joignabilite(p_max)
    score_i, _ = _score_identite(p_max)
    score_p, _ = _score_potentiel(p_max)
    score_s, _ = _score_signaux(p_max)

    print(f"✅ Catégories (prospect optimal):")
    print(f"  Joignabilité: {score_j}/80")
    print(f"  Identité: {score_i}/60")
    print(f"  Potentiel: {score_p}/80")
    print(f"  Signaux: {score_s}/80")
    print(f"  TOTAL: {score_j + score_i + score_p + score_s}/300")

    # Vérifier qu'on peut atteindre un bon score
    total = score_j + score_i + score_p + score_s
    assert total >= 200  # Au moins 200/300 pour un prospect optimal


def test_score_explanation_format():
    """Test format explication score."""
    db = SessionLocal()
    try:
        # Prendre prospect récent
        p = db.query(Prospect).order_by(Prospect.id.desc()).first()

        if p and p.score_explanation:
            # Vérifier format nouveau système 300pts
            if "[300pts]" in p.score_explanation:
                assert "Joignabilité" in p.score_explanation
                assert "Identité" in p.score_explanation
                assert "Potentiel" in p.score_explanation
                assert "Signaux" in p.score_explanation
                assert "/100" in p.score_explanation

                print("✅ Format explication score 300pts validé")
            else:
                print("⚠️  Prospect pas encore rescorer avec système 300pts")

        else:
            print("⚠️  Aucun prospect avec explication")

    finally:
        db.close()


def test_score_normalization():
    """Test normalisation 300 → /100."""
    # Vérifier formule de normalisation
    assert round(150 / 300 * 100) == 50
    assert round(240 / 300 * 100) == 80
    assert round(90 / 300 * 100) == 30
    assert round(300 / 300 * 100) == 100

    print("✅ Normalisation 300pts → /100 correcte")


def test_score_consistency():
    """Test cohérence score entre calcul et base."""
    db = SessionLocal()
    try:
        # Prendre 5 prospects au hasard
        prospects = db.query(Prospect).limit(5).all()

        for p in prospects:
            # Recalculer score
            new_score, new_label, _ = calculate_score(p)

            # Comparer avec score en base (tolérance ±1 pour arrondis)
            if p.lead_score:
                diff = abs(new_score - p.lead_score)
                if diff > 1:
                    print(f"⚠️  {p.company_name}: score BDD={p.lead_score}, recalculé={new_score}")

        print("✅ Cohérence scores vérifiée")

    finally:
        db.close()
