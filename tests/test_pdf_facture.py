"""
Tests pour pdf_facture — Génération PDF factures
"""
import pytest
from datetime import date
from app.utils.pdf_facture import generate_facture_pdf, _get_rib


def test_get_rib():
    """Test récupération RIB."""
    rib = _get_rib()

    assert isinstance(rib, dict)
    assert "iban" in rib
    assert "bic" in rib

    print(f"✅ RIB récupéré: {rib['iban'][:10]}...")


def test_generate_facture_pdf_basic():
    """Test génération PDF facture basique."""
    facture_data = {
        "numero": "FACT-2024-001",
        "date_emission": "2024-01-15",
        "date_echeance": "2024-02-15",
        "montant_ht": 1000.0,
        "tva_pct": 20.0,
        "montant_ttc": 1200.0,
        "description": "Prestation nettoyage",
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

    pdf_bytes = generate_facture_pdf(facture_data, client_data)

    # Vérifier que c'est bien un PDF
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b'%PDF'), "Doit commencer par %PDF"

    print(f"✅ PDF facture généré: {len(pdf_bytes)} bytes")


def test_generate_facture_pdf_with_lines():
    """Test PDF avec lignes de facture."""
    facture_data = {
        "numero": "FACT-2024-002",
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

    pdf_bytes = generate_facture_pdf(facture_data, client_data)

    assert len(pdf_bytes) > 3000
    assert b'%%EOF' in pdf_bytes

    print(f"✅ PDF facture avec lignes: {len(pdf_bytes)} bytes")


def test_generate_facture_pdf_minimal():
    """Test avec données minimales."""
    facture_data = {
        "numero": "FACT-2024-003",
        "montant_ht": 500.0,
        "montant_ttc": 600.0
    }

    client_data = {
        "company_name": "Minimal SA"
    }

    pdf_bytes = generate_facture_pdf(facture_data, client_data)

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b'%PDF')

    print("✅ PDF facture minimal généré")


def test_generate_facture_pdf_structure():
    """Test structure PDF."""
    facture_data = {
        "numero": "FACT-2024-004",
        "montant_ht": 1000.0,
        "montant_ttc": 1200.0
    }

    client_data = {
        "company_name": "Structure Test"
    }

    pdf_bytes = generate_facture_pdf(facture_data, client_data)

    # Vérifications structure PDF
    assert b'/Type /Page' in pdf_bytes
    assert b'ReportLab' in pdf_bytes
    assert b'%%EOF' in pdf_bytes

    print("✅ Structure PDF facture valide")


def test_generate_facture_pdf_with_dates():
    """Test avec dates d'échéance."""
    facture_data = {
        "numero": "FACT-2024-005",
        "date_emission": "2024-06-15",
        "date_echeance": "2024-07-15",
        "montant_ht": 800.0,
        "montant_ttc": 960.0
    }

    client_data = {
        "company_name": "Date Test SA"
    }

    pdf_bytes = generate_facture_pdf(facture_data, client_data)

    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b'%PDF')

    print("✅ PDF facture avec dates généré")


def test_generate_facture_pdf_paid():
    """Test facture payée."""
    facture_data = {
        "numero": "FACT-2024-006",
        "montant_ht": 1500.0,
        "montant_ttc": 1800.0,
        "status": "payee",
        "date_paiement": "2024-06-20"
    }

    client_data = {
        "company_name": "Paid Test SA"
    }

    pdf_bytes = generate_facture_pdf(facture_data, client_data)

    assert len(pdf_bytes) > 0
    assert b'%%EOF' in pdf_bytes

    print("✅ PDF facture payée généré")


def test_generate_facture_pdf_special_characters():
    """Test avec caractères spéciaux."""
    facture_data = {
        "numero": "FACT-2024-007",
        "montant_ht": 1500.0,
        "montant_ttc": 1800.0,
        "description": "Prestation après-chantier & finitions"
    }

    client_data = {
        "company_name": "L'Entreprise Française",
        "contact_name": "François Léger"
    }

    pdf_bytes = generate_facture_pdf(facture_data, client_data)

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0

    print("✅ PDF facture avec caractères spéciaux")


def test_generate_facture_pdf_multiple_calls():
    """Test génération multiple stable."""
    facture_data = {
        "numero": "FACT-2024-008",
        "montant_ht": 1000.0,
        "montant_ttc": 1200.0
    }

    client_data = {
        "company_name": "Multi Test"
    }

    pdf1 = generate_facture_pdf(facture_data, client_data)
    pdf2 = generate_facture_pdf(facture_data, client_data)

    # Les deux devraient avoir une taille similaire
    assert abs(len(pdf1) - len(pdf2)) < 500

    print("✅ Génération facture multiple stable")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
