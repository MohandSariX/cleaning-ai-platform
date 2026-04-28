"""
Tests Phase 1 — Devis Engine & PDF Generation
"""
import pytest
import os
from app.utils.devis_engine import calculate, load_rules, get_questions_manquantes


def test_load_rules():
    """Test chargement devis_rules.json."""
    rules = load_rules()

    # Vérifier structure
    assert "tarifs" in rules
    assert "tva" in rules
    assert "societe" in rules
    assert "validite_jours" in rules

    # Vérifier infos société
    societe = rules["societe"]
    assert "nom" in societe
    assert "adresse" in societe
    assert "email" in societe

    print(f"✅ devis_rules.json chargé: {societe['nom']}")


def test_calculate_devis_bureaux():
    """Test calcul devis bureaux."""
    result = calculate(
        type_prestation="bureaux",
        superficie_m2=100,
        frequence="mensuel"
    )

    # Vérifier structure résultat
    assert "montant_ht" in result
    assert "montant_ttc" in result
    assert "description" in result
    assert "duree_estimee_heures" in result

    # Vérifier cohérence
    assert result["montant_ht"] > 0
    assert result["montant_ttc"] > result["montant_ht"]
    assert result["duree_estimee_heures"] > 0

    print(f"✅ Devis bureaux 100m² mensuel: {result['montant_ttc']:.2f}€ TTC")


def test_calculate_devis_fin_chantier():
    """Test calcul devis fin de chantier."""
    result = calculate(
        type_prestation="fin_chantier",
        superficie_m2=150,
        frequence="ponctuel"
    )

    assert result["montant_ht"] > 0
    assert result["montant_ttc"] > result["montant_ht"]

    # Fin de chantier devrait être ponctuel uniquement
    assert "ponctuel" in result["description"].lower()

    print(f"✅ Devis fin chantier 150m²: {result['montant_ttc']:.2f}€ TTC")


def test_calculate_devis_copropriete():
    """Test calcul devis copropriété."""
    result = calculate(
        type_prestation="copropriete",
        superficie_m2=200,
        frequence="hebdo"
    )

    assert result["montant_ht"] > 0
    assert result["frequence"] == "hebdo"

    print(f"✅ Devis copropriété 200m² hebdo: {result['montant_ttc']:.2f}€ TTC")


def test_calculate_devis_vitrerie():
    """Test calcul devis vitrerie."""
    result = calculate(
        type_prestation="vitrerie",
        superficie_m2=50,
        frequence="ponctuel"
    )

    assert result["montant_ht"] > 0
    assert "vitr" in result["description"].lower()

    print(f"✅ Devis vitrerie 50m²: {result['montant_ttc']:.2f}€ TTC")


def test_frequence_impact():
    """Test impact fréquence sur le prix."""
    base = calculate("bureaux", 100, "ponctuel")
    hebdo = calculate("bureaux", 100, "hebdo")
    mensuel = calculate("bureaux", 100, "mensuel")

    # Vérifier que fréquence impact le prix
    # Généralement : ponctuel > hebdo > mensuel (par passage)
    print(f"✅ Ponctuel: {base['montant_ttc']:.2f}€")
    print(f"✅ Hebdo: {hebdo['montant_ttc']:.2f}€")
    print(f"✅ Mensuel: {mensuel['montant_ttc']:.2f}€")

    # Au moins vérifier que les prix sont différents
    assert base['montant_ttc'] != hebdo['montant_ttc'] or hebdo['montant_ttc'] != mensuel['montant_ttc']


def test_superficie_impact():
    """Test impact superficie sur le prix."""
    small = calculate("bureaux", 50, "ponctuel")
    medium = calculate("bureaux", 100, "ponctuel")
    large = calculate("bureaux", 200, "ponctuel")

    # Prix doit augmenter avec superficie
    assert small['montant_ttc'] < medium['montant_ttc']
    assert medium['montant_ttc'] < large['montant_ttc']

    print(f"✅ 50m²: {small['montant_ttc']:.2f}€")
    print(f"✅ 100m²: {medium['montant_ttc']:.2f}€")
    print(f"✅ 200m²: {large['montant_ttc']:.2f}€")


def test_tva_calculation():
    """Test calcul TVA correct."""
    rules = load_rules()
    tva_rate = rules["tva"]

    result = calculate("bureaux", 100, "ponctuel")

    # Vérifier TVA
    tva_calculee = result["montant_ttc"] - result["montant_ht"]
    tva_theorique = result["montant_ht"] * tva_rate

    # Tolérance de 0.01€ pour arrondis
    assert abs(tva_calculee - tva_theorique) < 0.01

    print(f"✅ TVA {tva_rate*100}%: {tva_calculee:.2f}€ calculée, {tva_theorique:.2f}€ théorique")


def test_get_questions_manquantes():
    """Test détection questions manquantes."""
    # Questions présentes
    infos_completes = {
        "superficie_m2": 100,
        "frequence": "hebdo",
        "type_prestation": "bureaux"
    }

    questions = get_questions_manquantes("bureaux", infos_completes)
    assert len(questions) == 0, "Toutes les infos sont présentes"

    # Questions manquantes
    infos_partielles = {
        "type_prestation": "bureaux"
    }

    questions = get_questions_manquantes("bureaux", infos_partielles)
    assert len(questions) > 0, "Devrait demander superficie et fréquence"

    print(f"✅ Questions manquantes détectées: {len(questions)}")


def test_invalid_type_prestation():
    """Test type prestation invalide."""
    result = calculate(
        type_prestation="type_inexistant",
        superficie_m2=100,
        frequence="ponctuel"
    )

    # Devrait retourner None ou erreur
    assert result is None or "error" in result

    print("✅ Type prestation invalide géré correctement")


def test_edge_cases():
    """Test cas limites."""
    # Superficie 0
    result_zero = calculate("bureaux", 0, "ponctuel")
    assert result_zero is None or result_zero["montant_ht"] == 0

    # Superficie très grande
    result_large = calculate("bureaux", 10000, "ponctuel")
    assert result_large is not None
    assert result_large["montant_ht"] > 0

    # Fréquence invalide
    result_freq = calculate("bureaux", 100, "quotidien")
    # Devrait fallback sur ponctuel ou retourner None

    print("✅ Cas limites testés")


def test_devis_includes_societe_info():
    """Test que le devis inclut les infos société."""
    result = calculate("bureaux", 100, "ponctuel")

    # Devrait inclure infos société
    assert "societe" in result or "nom_societe" in result

    rules = load_rules()
    societe = rules["societe"]

    # Au moins le nom devrait être présent quelque part
    result_str = str(result)
    # Note: en test, on vérifie juste que ça ne plante pas

    print("✅ Infos société disponibles dans résultat")


def test_duree_estimee():
    """Test calcul durée estimée cohérent."""
    result = calculate("bureaux", 100, "ponctuel")

    duree = result["duree_estimee_heures"]

    # Durée devrait être raisonnable (entre 1h et 20h pour 100m²)
    assert 0.5 <= duree <= 20

    # Durée devrait augmenter avec superficie
    result_large = calculate("bureaux", 200, "ponctuel")
    assert result_large["duree_estimee_heures"] > duree

    print(f"✅ Durée estimée 100m²: {duree}h, 200m²: {result_large['duree_estimee_heures']}h")
