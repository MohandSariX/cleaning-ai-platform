"""
Tests complets pour qualification_agent.py
Objectif: 41% → 80%+ coverage (~90 lignes)
"""
import pytest
from unittest.mock import patch, MagicMock, mock_open
import json


# ══════════════════════════════════════════════════════════════
# _call_ollama function
# ══════════════════════════════════════════════════════════════

@patch('app.agents.qualification_agent.requests.post')
def test_call_ollama_success(mock_post):
    """Test _call_ollama() successful call."""
    from app.agents.qualification_agent import _call_ollama

    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "Test response from Ollama"}
    mock_post.return_value = mock_response

    result = _call_ollama("Test prompt")

    assert result == "Test response from Ollama"
    mock_post.assert_called_once()
    print("✅ _call_ollama success")


@patch('app.agents.qualification_agent.requests.post')
def test_call_ollama_error(mock_post):
    """Test _call_ollama() error handling."""
    from app.agents.qualification_agent import _call_ollama

    mock_post.side_effect = Exception("Connection error")

    result = _call_ollama("Test prompt")

    assert result == ""
    print("✅ _call_ollama error")


# ══════════════════════════════════════════════════════════════
# classify_message_ia function
# ══════════════════════════════════════════════════════════════

@patch('app.agents.qualification_agent._call_ollama')
def test_classify_message_ia_accuse(mock_ollama):
    """Test classify_message_ia() accusé reception."""
    from app.agents.qualification_agent import classify_message_ia

    mock_ollama.return_value = '{"categorie": "accuse"}'

    result = classify_message_ia("Bien reçu, merci", "Re: Devis")

    assert result == "accuse"
    print("✅ classify_message_ia accuse")


@patch('app.agents.qualification_agent._call_ollama')
def test_classify_message_ia_signature(mock_ollama):
    """Test classify_message_ia() signature."""
    from app.agents.qualification_agent import classify_message_ia

    mock_ollama.return_value = '{"categorie": "interesse"}'

    # But message has strong signature keywords
    result = classify_message_ia("On y va, je suis d'accord !", "Re: Devis")

    assert result == "signature"
    print("✅ classify_message_ia signature")


@patch('app.agents.qualification_agent._call_ollama')
def test_classify_message_ia_devis(mock_ollama):
    """Test classify_message_ia() demande devis."""
    from app.agents.qualification_agent import classify_message_ia

    mock_ollama.return_value = '{"categorie": "devis"}'

    result = classify_message_ia("Je voudrais un devis pour 200m²", "Demande")

    assert result == "devis"
    print("✅ classify_message_ia devis")


@patch('app.agents.qualification_agent._call_ollama')
def test_classify_message_ia_pas_interesse(mock_ollama):
    """Test classify_message_ia() pas intéressé."""
    from app.agents.qualification_agent import classify_message_ia

    mock_ollama.return_value = '{"categorie": "pas_interesse"}'

    result = classify_message_ia("Non merci, ne pas recontacter", "Re:")

    assert result == "pas_interesse"
    print("✅ classify_message_ia pas_interesse")


@patch('app.agents.qualification_agent._call_ollama')
def test_classify_message_ia_negociation(mock_ollama):
    """Test classify_message_ia() négociation."""
    from app.agents.qualification_agent import classify_message_ia

    mock_ollama.return_value = '{"categorie": "negociation"}'

    result = classify_message_ia("C'est trop cher, vous pouvez faire un geste ?", "Re: Devis")

    assert result == "negociation"
    print("✅ classify_message_ia negociation")


@patch('app.agents.qualification_agent._call_ollama')
def test_classify_message_ia_invalid_json(mock_ollama):
    """Test classify_message_ia() with invalid JSON response."""
    from app.agents.qualification_agent import classify_message_ia

    mock_ollama.return_value = "invalid json response"

    result = classify_message_ia("Test message", "Test")

    assert result == "incertain"
    print("✅ classify_message_ia invalid json")


@patch('app.agents.qualification_agent._call_ollama')
def test_classify_message_ia_with_historique(mock_ollama):
    """Test classify_message_ia() with historique."""
    from app.agents.qualification_agent import classify_message_ia

    mock_ollama.return_value = '{"categorie": "accuse"}'

    historique = ["Message 1", "Message 2", "Devis envoyé"]
    result = classify_message_ia("Merci", "Re:", historique=historique)

    assert result == "accuse"
    print("✅ classify_message_ia with historique")


# ══════════════════════════════════════════════════════════════
# extract_infos_from_message function
# ══════════════════════════════════════════════════════════════

@patch('app.agents.qualification_agent._call_ollama')
def test_extract_infos_from_message_complete(mock_ollama):
    """Test extract_infos_from_message() complete extraction."""
    from app.agents.qualification_agent import extract_infos_from_message

    mock_ollama.return_value = json.dumps({
        "type_prestation": "bureaux",
        "superficie_m2": 150,
        "frequence": "hebdo",
        "ville": "Paris",
        "intention": "demande_devis"
    })

    prospect_context = {
        "company_name": "Test Corp",
        "industry": "Services",
        "city": "Paris"
    }

    result = extract_infos_from_message("J'ai 150m² de bureaux à nettoyer chaque semaine", prospect_context)

    assert result["type_prestation"] == "bureaux"
    assert result["superficie_m2"] == 150
    assert result["frequence"] == "hebdo"
    print(f"✅ extract_infos_from_message complete: {result}")


@patch('app.agents.qualification_agent._call_ollama')
def test_extract_infos_from_message_partial(mock_ollama):
    """Test extract_infos_from_message() partial extraction."""
    from app.agents.qualification_agent import extract_infos_from_message

    mock_ollama.return_value = json.dumps({
        "type_prestation": "copropriete",
        "superficie_m2": None,
        "frequence": None,
        "ville": "Créteil",
        "intention": "interesse"
    })

    prospect_context = {"company_name": "Syndic", "city": "Créteil"}

    result = extract_infos_from_message("Je suis intéressé pour une copropriété", prospect_context)

    assert result["type_prestation"] == "copropriete"
    assert result["superficie_m2"] is None
    print(f"✅ extract_infos_from_message partial: {result}")


@patch('app.agents.qualification_agent._call_ollama')
def test_extract_infos_from_message_invalid_json(mock_ollama):
    """Test extract_infos_from_message() with invalid JSON."""
    from app.agents.qualification_agent import extract_infos_from_message

    mock_ollama.return_value = "invalid json"

    prospect_context = {"company_name": "Test", "city": "Paris"}

    result = extract_infos_from_message("Message quelconque", prospect_context)

    # Should return default values
    assert result["intention"] == "incertain"
    assert result["ville"] == "Paris"
    print(f"✅ extract_infos_from_message invalid json: {result}")


# ══════════════════════════════════════════════════════════════
# generate_qualification_email function
# ══════════════════════════════════════════════════════════════

@patch('app.agents.qualification_agent._call_ollama')
@patch('app.agents.qualification_agent.get_questions_manquantes')
def test_generate_qualification_email_with_questions(mock_questions, mock_ollama):
    """Test generate_qualification_email() with missing questions."""
    from app.agents.qualification_agent import generate_qualification_email

    mock_questions.return_value = ["Quelle est la superficie ?", "Quelle fréquence souhaitez-vous ?"]
    mock_ollama.return_value = "Merci de votre retour. Pourriez-vous nous préciser la superficie et la fréquence ? Nous vous enverrons un devis sous 24h."

    prospect_context = {"company_name": "Test Corp", "city": "Paris", "industry": "Services"}
    infos_connues = {"type_prestation": "bureaux"}
    historique = ["Message 1"]

    result = generate_qualification_email(prospect_context, infos_connues, historique)

    assert result is not None
    assert "Bonjour" in result
    assert "Proprexis" in result
    print("✅ generate_qualification_email with questions")


@patch('app.agents.qualification_agent.get_questions_manquantes')
def test_generate_qualification_email_no_questions(mock_questions):
    """Test generate_qualification_email() when no questions needed."""
    from app.agents.qualification_agent import generate_qualification_email

    mock_questions.return_value = []  # No missing questions

    prospect_context = {"company_name": "Test Corp", "city": "Paris"}
    infos_connues = {
        "type_prestation": "bureaux",
        "superficie_m2": 150,
        "frequence": "hebdo"
    }
    historique = []

    result = generate_qualification_email(prospect_context, infos_connues, historique)

    assert result is None
    print("✅ generate_qualification_email no questions")


@patch('app.agents.qualification_agent._call_ollama')
@patch('app.agents.qualification_agent.get_questions_manquantes')
def test_generate_qualification_email_ollama_empty(mock_questions, mock_ollama):
    """Test generate_qualification_email() when Ollama returns empty."""
    from app.agents.qualification_agent import generate_qualification_email

    mock_questions.return_value = ["Quelle superficie ?"]
    mock_ollama.return_value = ""  # Empty response

    prospect_context = {"company_name": "Test", "city": "Paris"}
    infos_connues = {"type_prestation": "bureaux"}
    historique = []

    result = generate_qualification_email(prospect_context, infos_connues, historique)

    # Should use fallback
    assert result is not None
    assert "Bonjour" in result
    assert "quelle superficie" in result.lower()
    print("✅ generate_qualification_email ollama empty")


# ══════════════════════════════════════════════════════════════
# calculate_devis function
# ══════════════════════════════════════════════════════════════

@patch('app.agents.qualification_agent.engine_calculate')
def test_calculate_devis_bureaux(mock_engine):
    """Test calculate_devis() for bureaux."""
    from app.agents.qualification_agent import calculate_devis

    mock_engine.return_value = {
        "type_prestation": "bureaux",
        "description": "Nettoyage bureaux",
        "montant_ht": 320.0,
        "montant_ttc": 384.0
    }

    infos = {
        "type_prestation": "bureaux",
        "superficie_m2": 100,
        "frequence": "hebdo"
    }

    result = calculate_devis(infos)

    assert result["type_prestation"] == "bureaux"
    assert result["montant_ht"] == 320.0
    mock_engine.assert_called_once_with("bureaux", 100, "hebdo")
    print("✅ calculate_devis bureaux")


@patch('app.agents.qualification_agent.engine_calculate')
def test_calculate_devis_defaults(mock_engine):
    """Test calculate_devis() with missing values."""
    from app.agents.qualification_agent import calculate_devis

    mock_engine.return_value = {
        "type_prestation": "bureaux",
        "montant_ht": 320.0,
        "montant_ttc": 384.0
    }

    infos = {}  # No values

    result = calculate_devis(infos)

    # Should use defaults: bureaux, 100m², ponctuel
    mock_engine.assert_called_once_with("bureaux", 100, "ponctuel")
    print("✅ calculate_devis defaults")


# ══════════════════════════════════════════════════════════════
# needs_human_intervention function
# ══════════════════════════════════════════════════════════════

def test_needs_human_intervention_negociation():
    """Test needs_human_intervention() for price negotiation."""
    from app.agents.qualification_agent import needs_human_intervention

    message = "C'est trop cher, vous ne pouvez pas faire un geste ?"
    infos = {"superficie_m2": 100}
    nb_echanges = 2

    needs, raison = needs_human_intervention(message, infos, nb_echanges)

    assert needs is True
    assert "négociation" in raison.lower()
    print("✅ needs_human_intervention négociation")


def test_needs_human_intervention_grand_chantier():
    """Test needs_human_intervention() for large project."""
    from app.agents.qualification_agent import needs_human_intervention

    message = "J'ai besoin d'un nettoyage pour mes locaux"
    infos = {"superficie_m2": 2500}  # > 2000
    nb_echanges = 1

    needs, raison = needs_human_intervention(message, infos, nb_echanges)

    assert needs is True
    assert "2500" in raison
    print("✅ needs_human_intervention grand chantier")


def test_needs_human_intervention_too_many_exchanges():
    """Test needs_human_intervention() for too many exchanges."""
    from app.agents.qualification_agent import needs_human_intervention

    message = "Je veux plus d'infos"
    infos = {"superficie_m2": 100}
    nb_echanges = 4  # >= 4

    needs, raison = needs_human_intervention(message, infos, nb_echanges)

    assert needs is True
    assert "4 échanges" in raison
    print("✅ needs_human_intervention too many exchanges")


def test_needs_human_intervention_normal():
    """Test needs_human_intervention() normal case."""
    from app.agents.qualification_agent import needs_human_intervention

    message = "Je voudrais un devis pour 150m²"
    infos = {"superficie_m2": 150}
    nb_echanges = 1

    needs, raison = needs_human_intervention(message, infos, nb_echanges)

    assert needs is False
    assert raison is None
    print("✅ needs_human_intervention normal")


# ══════════════════════════════════════════════════════════════
# process_qualification function (complex, limited tests)
# ══════════════════════════════════════════════════════════════

@patch('app.agents.qualification_agent.store')
@patch('app.agents.qualification_agent.classify_message_ia')
def test_process_qualification_signature(mock_classify, mock_store):
    """Test process_qualification() signature path."""
    from app.agents.qualification_agent import process_qualification
    from app.models.prospect import Prospect

    mock_prospect = MagicMock(spec=Prospect)
    mock_prospect.id = 1
    mock_prospect.email = "test@test.com"
    mock_prospect.company_name = "Test Corp"
    mock_prospect.city = "Paris"

    mock_store.get_or_create.return_value = {
        "infos": {},
        "nb_echanges": 0,
        "historique": []
    }
    mock_store.is_devis_envoye.return_value = False
    mock_classify.return_value = "signature"

    mock_service = MagicMock()

    result = process_qualification(mock_prospect, "On y va !", mock_service)

    assert result == "signed"
    mock_store.mark_signe.assert_called_once_with("test@test.com")
    print("✅ process_qualification signature")


@patch('app.agents.qualification_agent.store')
@patch('app.agents.qualification_agent.classify_message_ia')
def test_process_qualification_accuse(mock_classify, mock_store):
    """Test process_qualification() accusé reception."""
    from app.agents.qualification_agent import process_qualification
    from app.models.prospect import Prospect

    mock_prospect = MagicMock(spec=Prospect)
    mock_prospect.id = 1
    mock_prospect.email = "test@test.com"
    mock_prospect.company_name = "Test Corp"
    mock_prospect.city = "Paris"

    mock_store.get_or_create.return_value = {
        "infos": {},
        "nb_echanges": 0,
        "historique": []
    }
    mock_store.is_devis_envoye.return_value = True  # Devis already sent
    mock_classify.return_value = "accuse"

    mock_service = MagicMock()

    result = process_qualification(mock_prospect, "Bien reçu", mock_service)

    assert result == "acknowledgement_ignored"
    print("✅ process_qualification accuse")


@patch('app.agents.qualification_agent.SessionLocal')
@patch('app.agents.qualification_agent.store')
@patch('app.agents.qualification_agent.classify_message_ia')
def test_process_qualification_pas_interesse(mock_classify, mock_store, mock_session):
    """Test process_qualification() pas intéressé."""
    from app.agents.qualification_agent import process_qualification
    from app.models.prospect import Prospect

    mock_prospect = MagicMock(spec=Prospect)
    mock_prospect.id = 1
    mock_prospect.email = "test@test.com"
    mock_prospect.company_name = "Test Corp"
    mock_prospect.city = "Paris"

    mock_db_prospect = MagicMock(spec=Prospect)
    mock_db = MagicMock()
    mock_db.query().filter().first.return_value = mock_db_prospect
    mock_session.return_value = mock_db

    mock_store.get_or_create.return_value = {
        "infos": {},
        "nb_echanges": 0,
        "historique": []
    }
    mock_store.is_devis_envoye.return_value = False
    mock_classify.return_value = "pas_interesse"

    mock_service = MagicMock()

    result = process_qualification(mock_prospect, "Non merci", mock_service)

    assert result == "lost"
    assert mock_db_prospect.status == "lost"
    mock_store.mark_perdu.assert_called_once_with("test@test.com")
    print("✅ process_qualification pas_interesse")


@patch('app.agents.qualification_agent.store')
@patch('app.agents.qualification_agent.classify_message_ia')
def test_process_qualification_negociation(mock_classify, mock_store):
    """Test process_qualification() négociation."""
    from app.agents.qualification_agent import process_qualification
    from app.models.prospect import Prospect

    mock_prospect = MagicMock(spec=Prospect)
    mock_prospect.id = 1
    mock_prospect.email = "test@test.com"
    mock_prospect.company_name = "Test Corp"
    mock_prospect.city = "Paris"

    mock_store.get_or_create.return_value = {
        "infos": {},
        "nb_echanges": 0,
        "historique": []
    }
    mock_store.is_devis_envoye.return_value = False
    mock_classify.return_value = "negociation"

    mock_service = MagicMock()

    result = process_qualification(mock_prospect, "Trop cher", mock_service)

    assert result == "human_required"
    print("✅ process_qualification negociation")


# ══════════════════════════════════════════════════════════════
# Constants validation
# ══════════════════════════════════════════════════════════════

def test_qualification_agent_constants():
    """Test qualification_agent constants."""
    from app.agents.qualification_agent import OLLAMA_URL, CRM_URL

    assert isinstance(OLLAMA_URL, str)
    assert "localhost" in OLLAMA_URL
    assert "11434" in OLLAMA_URL

    assert isinstance(CRM_URL, str)
    assert "localhost" in CRM_URL

    print("✅ Qualification agent constants")


# ══════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════

def test_qualification_agent_summary():
    """Résumé des tests qualification_agent."""
    print(f"\n✅ Qualification agent: 27 tests exécutés")
    print(f"   Coverage attendu: 41% → 80%+ (~90 lignes)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
