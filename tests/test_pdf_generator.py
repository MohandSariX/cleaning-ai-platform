"""
Tests pour pdf_generator — Génération PDF devis
"""
import pytest
from datetime import date
from app.utils.pdf_generator import generate_devis_pdf


def test_generate_devis_pdf_basic():
    """Test génération PDF devis basique."""
    devis_data = {
        "numero": "DEV-2024-001",
        "date_emission": "2024-01-15",
        "montant_ht": 1000.0,
        "tva_pct": 20.0,
        "montant_ttc": 1200.0,
        "description": "Nettoyage bureaux",
        "lignes": []
    }

    client_data = {
        "company_name": "Test SA",
        "contact_name": "Jean Dupont",
        "address": "123 Rue Test",
        "city": "75001 Paris",
        "email": "test@example.com",
        "phone": "01 23 45 67 89"
    }

    pdf_bytes = generate_devis_pdf(devis_data, client_data)

    # Vérifier que c'est bien un PDF
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b'%PDF'), "Doit commencer par %PDF"

    print(f"✅ PDF devis généré: {len(pdf_bytes)} bytes")


def test_generate_devis_pdf_with_lines():
    """Test PDF avec lignes de devis."""
    devis_data = {
        "numero": "DEV-2024-002",
        "montant_ht": 2500.0,
        "tva_pct": 20.0,
        "montant_ttc": 3000.0,
        "lignes": [
            {"designation": "Nettoyage bureaux", "quantite": 100, "prix_unitaire": 15.0, "total": 1500.0},
            {"designation": "Vitrerie", "quantite": 50, "prix_unitaire": 20.0, "total": 1000.0},
        ]
    }

    client_data = {
        "company_name": "Client Test",
        "email": "client@test.com"
    }

    pdf_bytes = generate_devis_pdf(devis_data, client_data)

    assert len(pdf_bytes) > 3000, "PDF avec lignes devrait être plus grand"
    assert b'%%EOF' in pdf_bytes

    print(f"✅ PDF avec lignes: {len(pdf_bytes)} bytes")


def test_generate_devis_pdf_minimal_data():
    """Test avec données minimales."""
    devis_data = {
        "montant_ht": 500.0,
        "montant_ttc": 600.0
    }

    client_data = {
        "company_name": "Minimal SA"
    }

    pdf_bytes = generate_devis_pdf(devis_data, client_data)

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b'%PDF')

    print("✅ PDF minimal généré")


def test_generate_devis_pdf_structure():
    """Test structure PDF."""
    devis_data = {
        "numero": "DEV-2024-003",
        "montant_ht": 1000.0,
        "montant_ttc": 1200.0
    }

    client_data = {
        "company_name": "Structure Test"
    }

    pdf_bytes = generate_devis_pdf(devis_data, client_data)

    # Vérifications structure PDF
    assert b'/Type /Page' in pdf_bytes
    assert b'ReportLab' in pdf_bytes
    assert b'%%EOF' in pdf_bytes

    print("✅ Structure PDF valide")


def test_generate_devis_pdf_date_formatting():
    """Test formatage dates."""
    devis_data = {
        "numero": "DEV-2024-004",
        "date_emission": "2024-06-15",
        "validite_jours": 30,
        "montant_ht": 800.0,
        "montant_ttc": 960.0
    }

    client_data = {
        "company_name": "Date Test SA"
    }

    pdf_bytes = generate_devis_pdf(devis_data, client_data)

    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b'%PDF')

    print("✅ PDF avec dates généré")


def test_generate_devis_pdf_large_amount():
    """Test avec montants importants."""
    devis_data = {
        "numero": "DEV-2024-005",
        "montant_ht": 50000.0,
        "tva_pct": 20.0,
        "montant_ttc": 60000.0,
        "description": "Gros chantier"
    }

    client_data = {
        "company_name": "BigCorp SA",
        "address": "456 Avenue Grande",
        "city": "92000 Nanterre"
    }

    pdf_bytes = generate_devis_pdf(devis_data, client_data)

    assert len(pdf_bytes) > 0
    assert b'%%EOF' in pdf_bytes

    print(f"✅ PDF gros montant: {len(pdf_bytes)} bytes")


def test_generate_devis_pdf_special_characters():
    """Test avec caractères spéciaux."""
    devis_data = {
        "numero": "DEV-2024-006",
        "montant_ht": 1500.0,
        "montant_ttc": 1800.0,
        "description": "Nettoyage après-chantier & vitrerie"
    }

    client_data = {
        "company_name": "L'Entreprise Française",
        "contact_name": "François Léger",
        "address": "Rue de l'Église"
    }

    pdf_bytes = generate_devis_pdf(devis_data, client_data)

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0

    print("✅ PDF avec caractères spéciaux généré")


def test_generate_devis_pdf_multiple_calls():
    """Test génération multiple stable."""
    devis_data = {
        "numero": "DEV-2024-007",
        "montant_ht": 1000.0,
        "montant_ttc": 1200.0
    }

    client_data = {
        "company_name": "Multi Test"
    }

    pdf1 = generate_devis_pdf(devis_data, client_data)
    pdf2 = generate_devis_pdf(devis_data, client_data)

    # Les deux devraient avoir une taille similaire (peut varier légèrement avec dates)
    assert abs(len(pdf1) - len(pdf2)) < 500

    print("✅ Génération multiple stable")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
