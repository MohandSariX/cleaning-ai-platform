"""
Tests complémentaires pour lead_scorer — Couvrir les branches manquantes
"""
import pytest
from app.agents.lead_scorer import (
    _extract_pappers_data,
    _extract_permis_data,
    _extract_dvf_data,
    _score_joignabilite,
    _score_identite,
    _score_potentiel,
    _score_signaux,
    _get_label,
    calculate_score
)


class MockProspect:
    """Mock prospect pour tests."""
    def __init__(self, **kwargs):
        self.email = kwargs.get("email")
        self.phone = kwargs.get("phone")
        self.website = kwargs.get("website")
        self.company_name = kwargs.get("company_name")
        self.address = kwargs.get("address")
        self.city = kwargs.get("city")
        self.industry = kwargs.get("industry")
        self.status = kwargs.get("status", "new")
        self.score_explanation = kwargs.get("score_explanation", "")


def test_extract_pappers_data_empty():
    """Test extraction Pappers avec explanation vide."""
    data = _extract_pappers_data("")
    assert data == {}

    data = _extract_pappers_data(None)
    assert data == {}

    print("✅ Extraction Pappers vide OK")


def test_extract_pappers_data_ca_with_spaces():
    """Test extraction CA avec espaces et points."""
    explanation = "CA : 1 234 567 €"
    data = _extract_pappers_data(explanation)
    assert data["ca"] == 1234567

    explanation2 = "CA: 1.234.567 €"
    data2 = _extract_pappers_data(explanation2)
    assert data2["ca"] == 1234567

    print("✅ Extraction CA avec espaces OK")


def test_extract_pappers_data_invalid_ca():
    """Test extraction CA invalide."""
    explanation = "CA : invalid €"
    data = _extract_pappers_data(explanation)
    assert data.get("ca") is None

    print("✅ CA invalide géré OK")


def test_extract_pappers_data_effectifs_invalid():
    """Test extraction effectifs invalide."""
    explanation = "Effectifs : abc"
    data = _extract_pappers_data(explanation)
    assert data.get("effectifs") is None

    print("✅ Effectifs invalide géré OK")


def test_extract_pappers_data_is_active():
    """Test détection entreprise active."""
    explanation = "Statut : Actif, entreprise en activité"
    data = _extract_pappers_data(explanation)
    assert data["is_active"] == True

    explanation2 = "Statut : inactif"
    data2 = _extract_pappers_data(explanation2)
    assert data2["is_active"] == False

    print("✅ Détection actif OK")


def test_extract_permis_data_variations():
    """Test extraction permis de construire avec variations."""
    assert _extract_permis_data("Source : Permis de construire") == True
    assert _extract_permis_data("Permis de construire accordé") == True
    assert _extract_permis_data("") == False
    assert _extract_permis_data(None) == False
    assert _extract_permis_data("Pas de permis") == False

    print("✅ Extraction permis OK")


def test_extract_dvf_data_variations():
    """Test extraction DVF avec variations."""
    assert _extract_dvf_data("Source : DVF") == True
    assert _extract_dvf_data("source_dvf présent") == True
    assert _extract_dvf_data("") == False
    assert _extract_dvf_data(None) == False
    assert _extract_dvf_data("Pas de DVF") == False

    print("✅ Extraction DVF OK")


def test_score_joignabilite_pro_email():
    """Test score joignabilité avec email pro."""
    prospect = MockProspect(
        email="contact@entreprise.com",
        phone="0145678901"
    )
    score, details = _score_joignabilite(prospect)

    # Email pro: +40, Téléphone fixe: +25
    assert score == 65
    assert any("Email professionnel" in d for d in details)
    assert any("Téléphone fixe" in d for d in details)

    print(f"✅ Joignabilité email pro: {score}/80")


def test_score_joignabilite_personal_email():
    """Test score joignabilité avec email personnel."""
    prospect = MockProspect(
        email="jean.dupont@gmail.com",
        phone="0678901234"
    )
    score, details = _score_joignabilite(prospect)

    # Email perso: +15, Mobile: +15
    assert score == 30
    assert any("Email personnel" in d for d in details)
    assert any("mobile" in d for d in details)

    print(f"✅ Joignabilité email perso: {score}/80")


def test_score_joignabilite_entreprise_email():
    """Test score joignabilité avec email entreprise."""
    prospect = MockProspect(
        email="jean.dupont@moneentreprise.fr"
    )
    score, details = _score_joignabilite(prospect)

    # Email entreprise: +30
    assert score == 30
    assert any("Email entreprise" in d for d in details)

    print(f"✅ Joignabilité email entreprise: {score}/80")


def test_score_joignabilite_no_contact():
    """Test score joignabilité sans contact."""
    prospect = MockProspect()
    score, details = _score_joignabilite(prospect)

    assert score == 0
    assert any("Pas d'email" in d for d in details)
    assert any("Pas de téléphone" in d for d in details)

    print("✅ Joignabilité sans contact: 0/80")


def test_score_joignabilite_phone_other():
    """Test score téléphone autre type."""
    prospect = MockProspect(phone="0899123456")
    score, details = _score_joignabilite(prospect)

    assert score == 10
    assert any("Téléphone détecté" in d for d in details)

    print("✅ Téléphone autre type: +10")


def test_score_identite_social_media_only():
    """Test score identité avec seulement réseaux sociaux."""
    prospect = MockProspect(
        website="facebook.com/entreprise",
        score_explanation=""
    )
    score, details = _score_identite(prospect)

    assert score == 0
    assert any("réseau social" in d for d in details)

    print("✅ Identité réseaux sociaux seulement: 0/60")


def test_score_identite_website_with_email():
    """Test score identité avec site et email."""
    prospect = MockProspect(
        website="https://entreprise.com",
        email="contact@entreprise.com",
        score_explanation=""
    )
    score, details = _score_identite(prospect)

    # Site: +20, Email sur site: +10
    assert score == 30

    print(f"✅ Identité site+email: {score}/60")


def test_score_identite_no_website():
    """Test score identité sans site."""
    prospect = MockProspect(score_explanation="")
    score, details = _score_identite(prospect)

    assert any("Pas de site web" in d for d in details)

    print("✅ Identité sans site géré OK")


def test_score_identite_with_pappers():
    """Test score identité avec données Pappers complètes."""
    prospect = MockProspect(
        website="https://entreprise.com",
        email="contact@entreprise.com",
        company_name="Test SARL",
        score_explanation="Pappers enrichi, Dirigeant : Jean Dupont, SIRET : 12345678901234"
    )
    score, details = _score_identite(prospect)

    # Site: +20, Email: +10, Pappers: +10, Dirigeant: +10, SIRET: +5, Forme juridique: +5
    assert score == 60  # Max

    print(f"✅ Identité complète: {score}/60")


def test_score_potentiel_zone_target():
    """Test score potentiel avec zone ciblée."""
    prospect = MockProspect(
        city="Saint-Maur-des-Fossés",
        address="12 Rue de Paris 94100",
        score_explanation=""
    )
    score, details = _score_potentiel(prospect)

    # Zone prioritaire: +20, Adresse complète: +15
    assert score == 35
    assert any("Zone prioritaire" in d for d in details)

    print(f"✅ Potentiel zone target: {score}/80")


def test_score_potentiel_address_partial():
    """Test score potentiel avec adresse partielle."""
    prospect = MockProspect(
        address="Rue du Test",  # Pas de code postal, courte, pas de zone prioritaire
        score_explanation=""
    )
    score, details = _score_potentiel(prospect)

    # Adresse partielle: +7
    assert score == 7
    assert any("Adresse partielle" in d for d in details)

    print(f"✅ Potentiel adresse partielle: {score}/80")


def test_score_potentiel_no_address():
    """Test score potentiel sans adresse."""
    prospect = MockProspect(score_explanation="")
    score, details = _score_potentiel(prospect)

    assert any("Pas d'adresse" in d for d in details)

    print("✅ Potentiel sans adresse OK")


def test_score_potentiel_ca_tiers():
    """Test score potentiel avec CA par tranches."""
    # CA > 1M
    prospect1 = MockProspect(score_explanation="CA : 1500000 €")
    score1, details1 = _score_potentiel(prospect1)
    assert score1 == 30
    assert any("CA > 1M€" in d for d in details1)

    # CA > 500k
    prospect2 = MockProspect(score_explanation="CA : 750000 €")
    score2, details2 = _score_potentiel(prospect2)
    assert score2 == 20
    assert any("CA > 500k€" in d for d in details2)

    # CA > 100k
    prospect3 = MockProspect(score_explanation="CA : 250000 €")
    score3, details3 = _score_potentiel(prospect3)
    assert score3 == 10
    assert any("CA > 100k€" in d for d in details3)

    print("✅ Potentiel CA par tranches OK")


def test_score_potentiel_effectifs_tiers():
    """Test score potentiel avec effectifs par tranches."""
    # Effectifs >= 10
    prospect1 = MockProspect(score_explanation="Effectifs : 15")
    score1, details1 = _score_potentiel(prospect1)
    assert score1 == 15
    assert any("Effectifs ≥ 10" in d for d in details1)

    # Effectifs 5-9
    prospect2 = MockProspect(score_explanation="Effectifs : 7")
    score2, details2 = _score_potentiel(prospect2)
    assert score2 == 8
    assert any("Effectifs 5-9" in d for d in details2)

    print("✅ Potentiel effectifs par tranches OK")


def test_score_potentiel_no_data():
    """Test score potentiel sans données."""
    prospect = MockProspect(score_explanation="")
    score, details = _score_potentiel(prospect)

    assert any("Pas de CA trouvé" in d for d in details)
    assert any("Pas d'effectifs" in d for d in details)
    assert any("Hors zone prioritaire" in d for d in details)

    print("✅ Potentiel sans données OK")


def test_score_signaux_permis():
    """Test score signaux avec permis de construire."""
    prospect = MockProspect(
        score_explanation="Source : Permis de construire accordé"
    )
    score, details = _score_signaux(prospect)

    assert score == 40
    assert any("Permis de construire" in d for d in details)

    print(f"✅ Signaux permis: {score}/80")


def test_score_signaux_industries():
    """Test score signaux avec différentes industries."""
    # High priority
    prospect1 = MockProspect(industry="BTP construction")
    score1, details1 = _score_signaux(prospect1)
    assert score1 == 20
    assert any("BTP/Construction" in d for d in details1)

    # Medium priority
    prospect2 = MockProspect(industry="Syndic de copropriété")
    score2, details2 = _score_signaux(prospect2)
    assert score2 == 15
    assert any("Syndic/Hôtel" in d for d in details2)

    # Low priority
    prospect3 = MockProspect(industry="Bureau d'études")
    score3, details3 = _score_signaux(prospect3)
    assert score3 == 10
    assert any("Bureau/Commerce" in d for d in details3)

    print("✅ Signaux industries OK")


def test_score_signaux_replied():
    """Test score signaux avec email répondu."""
    prospect = MockProspect(status="replied")
    score, details = _score_signaux(prospect)

    assert score == 30
    assert any("Email répondu" in d for d in details)

    print(f"✅ Signaux replied: {score}/80")


def test_score_signaux_dvf():
    """Test score signaux avec source DVF."""
    prospect = MockProspect(score_explanation="Source : DVF transaction récente")
    score, details = _score_signaux(prospect)

    assert score == 20
    assert any("DVF" in d for d in details)

    print(f"✅ Signaux DVF: {score}/80")


def test_score_signaux_no_signals():
    """Test score signaux sans signaux."""
    prospect = MockProspect()
    score, details = _score_signaux(prospect)

    assert score == 0
    assert any("Pas de permis" in d for d in details)
    assert any("Industrie non ciblée" in d for d in details)

    print("✅ Signaux vides: 0/80")


def test_get_label_tiers():
    """Test labels par tranches."""
    assert _get_label(95) == "🔥 Priorité haute"
    assert _get_label(80) == "🔥 Priorité haute"
    assert _get_label(75) == "⚡ Priorité moyenne"
    assert _get_label(60) == "⚡ Priorité moyenne"
    assert _get_label(55) == "🌱 Priorité faible"
    assert _get_label(40) == "🌱 Priorité faible"
    assert _get_label(35) == "❄️ Non prioritaire"
    assert _get_label(0) == "❄️ Non prioritaire"

    print("✅ Labels par tranches OK")


def test_calculate_score_full():
    """Test calculate_score avec prospect complet."""
    prospect = MockProspect(
        email="contact@entreprise.com",
        phone="0145678901",
        website="https://entreprise.com",
        company_name="Test SARL",
        address="12 Rue de Paris 94100 Saint-Maur",
        city="Saint-Maur-des-Fossés",
        industry="BTP",
        status="replied",
        score_explanation="Pappers, Dirigeant : Jean Dupont, SIRET : 12345678901234, CA : 1500000 €, Effectifs : 15, actif, Source : Permis de construire accordé"
    )

    score, label, explanation = calculate_score(prospect)

    # Score max possible proche
    assert score >= 80
    assert label == "🔥 Priorité haute"
    assert "[300pts]" in explanation
    assert "Score brut:" in explanation

    print(f"✅ Calculate score complet: {score}/100 - {label}")


def test_calculate_score_minimal():
    """Test calculate_score avec prospect minimal."""
    prospect = MockProspect()

    score, label, explanation = calculate_score(prospect)

    assert score < 20
    assert label == "❄️ Non prioritaire"
    assert "JOIGNABILITÉ:" in explanation
    assert "IDENTITÉ:" in explanation
    assert "POTENTIEL:" in explanation
    assert "SIGNAUX:" in explanation

    print(f"✅ Calculate score minimal: {score}/100 - {label}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
