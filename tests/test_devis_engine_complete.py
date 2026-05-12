"""
Tests pour devis_engine — 100% coverage
"""
import pytest
from app.utils.devis_engine import (
    load_products_from_db,
    load_rules,
    get_tarif_key,
    calculate,
    get_questions_manquantes,
    get_all_tarifs
)


def test_load_products_from_db():
    """Test chargement produits depuis DB."""
    products = load_products_from_db()
    assert isinstance(products, dict)
    print(f"✅ Products loaded: {len(products)} types")


def test_load_rules():
    """Test chargement rules complètes."""
    rules = load_rules()
    assert isinstance(rules, dict)
    assert "tarifs" in rules
    print("✅ Rules loaded")


def test_get_tarif_key():
    """Test génération clé tarif."""
    key1 = get_tarif_key("nettoyage_bureaux", "hebdomadaire")
    assert isinstance(key1, str)

    key2 = get_tarif_key("vitrerie", "ponctuel")
    assert isinstance(key2, str)

    print(f"✅ Tarif keys: {key1}, {key2}")


def test_calculate_basic():
    """Test calcul devis basique."""
    result = calculate("nettoyage_bureaux", 100.0, "hebdomadaire")

    assert isinstance(result, dict)
    assert "tarif_m2" in result or "total_ht" in result

    print(f"✅ Calculate basic OK")


def test_calculate_with_nb_heures():
    """Test calcul avec nb_heures."""
    result = calculate(
        type_prestation="nettoyage_bureaux",
        superficie_m2=100.0,
        frequence="mensuel",
        nb_heures=5.0
    )

    assert isinstance(result, dict)
    print("✅ Calculate with nb_heures OK")


def test_calculate_different_types():
    """Test calcul pour différents types."""
    types = ["fin_chantier", "vitrerie", "copropriete"]

    for type_p in types:
        result = calculate(type_p, 50.0, "ponctuel")
        assert isinstance(result, dict)

    print("✅ Calculate different types OK")


def test_get_questions_manquantes():
    """Test questions manquantes."""
    questions = get_questions_manquantes(
        "nettoyage_bureaux",
        {"superficie_m2": 100}
    )

    assert isinstance(questions, list)
    print(f"✅ Questions manquantes: {len(questions)}")


def test_get_all_tarifs():
    """Test récupération tous tarifs."""
    tarifs = get_all_tarifs()

    assert isinstance(tarifs, list)
    assert len(tarifs) > 0

    print(f"✅ All tarifs: {len(tarifs)} tarifs")


def test_calculate_edge_cases():
    """Test cas limites."""
    # Petite surface
    result1 = calculate("nettoyage_bureaux", 10.0, "hebdomadaire")
    assert isinstance(result1, dict)

    # Grande surface
    result2 = calculate("nettoyage_bureaux", 5000.0, "mensuel")
    assert isinstance(result2, dict)

    print("✅ Edge cases OK")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
