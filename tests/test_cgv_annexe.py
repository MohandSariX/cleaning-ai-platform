"""
Tests pour cgv_annexe — Générateur PDF CGV
"""
import pytest
from io import BytesIO
from app.utils.cgv_annexe import generate_cgv_pdf


def test_generate_cgv_pdf():
    """Test génération PDF CGV."""
    pdf_bytes = generate_cgv_pdf()

    # Vérifier que c'est bien un PDF
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b'%PDF'), "Doit commencer par %PDF"

    print(f"✅ PDF CGV généré: {len(pdf_bytes)} bytes")


def test_cgv_pdf_contains_header():
    """Test que le PDF contient le header."""
    pdf_bytes = generate_cgv_pdf()

    # Le PDF devrait contenir des références PDF valides
    # Le contenu est compressé donc on vérifie la structure
    assert b'/Page' in pdf_bytes
    assert b'ReportLab' in pdf_bytes

    print("✅ Header PDF valide présent")


def test_cgv_pdf_structure():
    """Test structure du PDF."""
    pdf_bytes = generate_cgv_pdf()

    # Un PDF valide doit avoir EOF
    assert b'%%EOF' in pdf_bytes

    # Doit contenir des références à des pages
    assert b'/Type /Page' in pdf_bytes

    print("✅ Structure PDF valide")


def test_cgv_pdf_is_not_empty():
    """Test que le PDF n'est pas vide."""
    pdf_bytes = generate_cgv_pdf()

    # Un PDF avec contenu doit faire au moins 3KB (le CGV fait ~4.5KB)
    assert len(pdf_bytes) > 3000, f"PDF trop petit: {len(pdf_bytes)} bytes"

    print(f"✅ PDF de taille correcte: {len(pdf_bytes)/1024:.1f} KB")


def test_cgv_pdf_multiple_calls():
    """Test génération multiple."""
    pdf1 = generate_cgv_pdf()
    pdf2 = generate_cgv_pdf()

    # Les deux PDFs doivent être similaires en taille
    assert abs(len(pdf1) - len(pdf2)) < 100, "PDFs devraient avoir la même taille"

    print("✅ Génération multiple stable")


def test_cgv_pdf_can_be_written():
    """Test écriture du PDF."""
    pdf_bytes = generate_cgv_pdf()

    # Simuler écriture dans un buffer
    buffer = BytesIO()
    buffer.write(pdf_bytes)

    assert buffer.tell() > 0, "Buffer devrait contenir des données"

    print("✅ PDF peut être écrit dans un buffer")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
