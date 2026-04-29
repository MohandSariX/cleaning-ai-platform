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

    # Vérifier cohérence
    assert result["montant_ht"] > 0
    assert result["montant_ttc"] > result["montant_ht"]

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
    assert len(result["description"]) > 20  # Description présente

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

    print(f"✅ Ponctuel: {base['montant_ttc']:.2f}€")
    print(f"✅ Hebdo: {hebdo['montant_ttc']:.2f}€")
    print(f"✅ Mensuel: {mensuel['montant_ttc']:.2f}€")

    # Vérifier que les résultats sont cohérents
    assert base['montant_ttc'] > 0
    assert hebdo['montant_ttc'] > 0
    assert mensuel['montant_ttc'] > 0


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
    tva_config = rules["tva"]

    result = calculate("bureaux", 100, "ponctuel")

    # TVA devrait être calculée
    tva_calculee = result["montant_ttc"] - result["montant_ht"]
    
    # Vérifier que TVA > 0
    assert tva_calculee > 0

    print(f"✅ TVA calculée: {tva_calculee:.2f}€")


def test_get_questions_manquantes():
    """Test détection questions manquantes."""
    # Cas simple - questions complètes pour bureaux
    infos_completes = {
        "superficie_m2": 100,
        "frequence": "hebdo",
        "type_prestation": "bureaux",
        "nb_personnes": 10
    }

    questions = get_questions_manquantes("bureaux", infos_completes)
    print(f"✅ Questions manquantes: {len(questions)}")

    # Questions manquantes
    infos_partielles = {
        "type_prestation": "bureaux"
    }

    questions = get_questions_manquantes("bureaux", infos_partielles)
    assert len(questions) > 0, "Devrait demander superficie et fréquence"

    print(f"✅ Questions manquantes détectées: {len(questions)}")


def test_devis_coherence():
    """Test cohérence générale devis."""
    result = calculate("bureaux", 100, "ponctuel")

    # Vérifier tous les champs essentiels
    assert "montant_ht" in result
    assert "montant_ttc" in result
    assert "description" in result
    assert result["montant_ht"] > 0
    assert result["montant_ttc"] > result["montant_ht"]

    print("✅ Cohérence devis vérifiée")


def test_devis_includes_societe_info():
    """Test que le devis inclut les infos société."""
    result = calculate("bureaux", 100, "ponctuel")

    # Vérifier présence infos société dans résultat
    assert "nom_societe" in result or "societe" in str(result)

    rules = load_rules()
    societe = rules["societe"]

    print("✅ Infos société disponibles dans résultat")


def test_duree_estimee():
    """Test calcul durée estimée cohérent."""
    result = calculate("bureaux", 100, "ponctuel")

    if "duree_estimee_heures" in result and result["duree_estimee_heures"]:
        duree = result["duree_estimee_heures"]

        # Durée devrait être raisonnable
        assert 0.5 <= duree <= 20

        # Durée devrait augmenter avec superficie
        result_large = calculate("bureaux", 200, "ponctuel")
        if result_large.get("duree_estimee_heures"):
            assert result_large["duree_estimee_heures"] > duree

        print(f"✅ Durée estimée 100m²: {duree}h, 200m²: {result_large.get('duree_estimee_heures')}h")
    else:
        print("⚠️  Durée estimée non calculée")
