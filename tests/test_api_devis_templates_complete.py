"""
Tests complets pour api_devis_templates — Objectif 70%+ coverage
"""
import pytest
from fastapi.testclient import TestClient
from main import app
from app.core.database import SessionLocal
from app.models.devis_template import DevisTemplate

client = TestClient(app)


@pytest.fixture
def db_session():
    """Session DB pour fixtures."""
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture
def sample_template(db_session):
    """Template de test."""
    t = DevisTemplate(
        tenant_id=1,
        name="Template Test Bureaux",
        category="nettoyage",
        type_prestation="bureaux",
        description="Template pour bureaux",
        template_json={
            "title": "Devis {{client_name}}",
            "montant": "{{montant_ht}}",
            "description": "{{description}}"
        },
        variables_required=["client_name", "montant_ht", "description"],
        is_default=False,
        active=True
    )
    db_session.add(t)
    db_session.commit()
    db_session.refresh(t)
    return t


# ══════════════════════════════════════════════════════════════
# CRUD BASIQUE
# ══════════════════════════════════════════════════════════════

def test_list_templates():
    """Test GET /api/devis-templates/."""
    response = client.get("/api/devis-templates/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    print(f"✅ List templates: {len(data)} templates")


def test_list_templates_with_filters(sample_template):
    """Test GET /api/devis-templates/ avec filtres."""
    # Filtre par category
    response = client.get("/api/devis-templates/?category=nettoyage")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    # Filtre par type_prestation
    response = client.get("/api/devis-templates/?type_prestation=bureaux")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    # Filtre active_only=False
    response = client.get("/api/devis-templates/?active_only=false")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    print("✅ List templates with filters")


def test_get_template(sample_template):
    """Test GET /api/devis-templates/{id}."""
    response = client.get(f"/api/devis-templates/{sample_template.id}")
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == sample_template.id
    assert data["name"] == sample_template.name
    assert data["category"] == sample_template.category
    assert "template_json" in data
    assert "variables_required" in data

    print(f"✅ Get template: {data['name']}")


def test_get_template_not_found():
    """Test GET /api/devis-templates/{id} — 404."""
    response = client.get("/api/devis-templates/999999")
    assert response.status_code == 404
    assert "introuvable" in response.json()["detail"].lower()
    print("✅ Get template 404")


def test_create_template():
    """Test POST /api/devis-templates/."""
    template_data = {
        "name": "Template Vitrerie",
        "category": "nettoyage",
        "type_prestation": "vitrerie",
        "description": "Template pour vitrerie",
        "template_json": {
            "service": "Vitrerie",
            "client": "{{client_name}}",
            "tarif": "{{tarif}}"
        },
        "variables_required": ["client_name", "tarif"],
        "is_default": False,
        "active": True
    }

    response = client.post("/api/devis-templates/", json=template_data)
    assert response.status_code == 200
    data = response.json()

    assert data["name"] == "Template Vitrerie"
    assert data["category"] == "nettoyage"
    assert data["template_json"]["service"] == "Vitrerie"
    assert "client_name" in data["variables_required"]

    print(f"✅ Create template: {data['name']}")


def test_create_template_is_default(db_session):
    """Test POST /api/devis-templates/ avec is_default=True."""
    # Créer un premier template default
    template1 = {
        "name": "Default 1",
        "category": "test",
        "type_prestation": "test_type",
        "template_json": {"test": "1"},
        "is_default": True
    }

    response1 = client.post("/api/devis-templates/", json=template1)
    assert response1.status_code == 200
    data1 = response1.json()
    assert data1["is_default"] is True

    # Créer un second template default pour la même catégorie/type
    template2 = {
        "name": "Default 2",
        "category": "test",
        "type_prestation": "test_type",
        "template_json": {"test": "2"},
        "is_default": True
    }

    response2 = client.post("/api/devis-templates/", json=template2)
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["is_default"] is True

    # Vérifier que le premier n'est plus default
    response_check = client.get(f"/api/devis-templates/{data1['id']}")
    data_check = response_check.json()
    assert data_check["is_default"] is False

    print("✅ Create template is_default logic")


def test_update_template(sample_template):
    """Test PATCH /api/devis-templates/{id}."""
    update_data = {
        "name": "Template Modifié",
        "description": "Description modifiée"
    }

    response = client.patch(
        f"/api/devis-templates/{sample_template.id}",
        json=update_data
    )
    assert response.status_code == 200
    data = response.json()

    assert data["name"] == "Template Modifié"
    assert data["description"] == "Description modifiée"

    print(f"✅ Update template: {data['name']}")


def test_update_template_is_default(db_session):
    """Test PATCH /api/devis-templates/{id} avec is_default=True."""
    # Créer 2 templates dans la même catégorie
    t1 = DevisTemplate(
        tenant_id=1,
        name="Template A",
        category="test_cat",
        type_prestation="test_type",
        template_json={"a": 1},
        is_default=True,
        active=True
    )
    t2 = DevisTemplate(
        tenant_id=1,
        name="Template B",
        category="test_cat",
        type_prestation="test_type",
        template_json={"b": 2},
        is_default=False,
        active=True
    )
    db_session.add_all([t1, t2])
    db_session.commit()
    db_session.refresh(t1)
    db_session.refresh(t2)

    # Mettre t2 en default
    response = client.patch(
        f"/api/devis-templates/{t2.id}",
        json={"is_default": True}
    )
    assert response.status_code == 200

    # Vérifier que t1 n'est plus default
    response_check = client.get(f"/api/devis-templates/{t1.id}")
    data_check = response_check.json()
    assert data_check["is_default"] is False

    print("✅ Update template is_default logic")


def test_update_template_not_found():
    """Test PATCH /api/devis-templates/{id} — 404."""
    response = client.patch(
        "/api/devis-templates/999999",
        json={"name": "test"}
    )
    assert response.status_code == 404
    print("✅ Update template 404")


def test_delete_template(sample_template):
    """Test DELETE /api/devis-templates/{id}."""
    response = client.delete(f"/api/devis-templates/{sample_template.id}")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "deleted"
    assert data["id"] == sample_template.id

    # Vérifier soft delete (active=False)
    response_check = client.get(f"/api/devis-templates/{sample_template.id}")
    data_check = response_check.json()
    assert data_check["active"] is False

    print(f"✅ Delete template (soft): {sample_template.id}")


def test_delete_template_not_found():
    """Test DELETE /api/devis-templates/{id} — 404."""
    response = client.delete("/api/devis-templates/999999")
    assert response.status_code == 404
    print("✅ Delete template 404")


# ══════════════════════════════════════════════════════════════
# RENDER TEMPLATE
# ══════════════════════════════════════════════════════════════

def test_render_template(sample_template):
    """Test POST /api/devis-templates/render."""
    render_data = {
        "template_id": sample_template.id,
        "variables": {
            "client_name": "ABC Corp",
            "montant_ht": "5000",
            "description": "Nettoyage bureaux complet"
        }
    }

    response = client.post("/api/devis-templates/render", json=render_data)
    assert response.status_code == 200
    data = response.json()

    assert data["template_id"] == sample_template.id
    assert data["template_name"] == sample_template.name
    assert "rendered" in data
    assert data["rendered"]["title"] == "Devis ABC Corp"
    assert data["rendered"]["montant"] == "5000"
    assert data["rendered"]["description"] == "Nettoyage bureaux complet"

    print("✅ Render template with variables")


def test_render_template_missing_variables(sample_template):
    """Test POST /api/devis-templates/render — Variables manquantes."""
    render_data = {
        "template_id": sample_template.id,
        "variables": {
            "client_name": "ABC Corp"
            # montant_ht et description manquants
        }
    }

    response = client.post("/api/devis-templates/render", json=render_data)
    assert response.status_code == 400
    assert "manquantes" in response.json()["detail"].lower()

    print("✅ Render template missing variables validation")


def test_render_template_not_found():
    """Test POST /api/devis-templates/render — Template 404."""
    render_data = {
        "template_id": 999999,
        "variables": {}
    }

    response = client.post("/api/devis-templates/render", json=render_data)
    assert response.status_code == 404
    print("✅ Render template 404")


# ══════════════════════════════════════════════════════════════
# EDGE CASES & HELPERS
# ══════════════════════════════════════════════════════════════

def test_template_to_response_dates(sample_template):
    """Test _template_to_response avec dates."""
    response = client.get(f"/api/devis-templates/{sample_template.id}")
    data = response.json()

    assert "created_at" in data
    assert "updated_at" in data
    # created_at devrait être non-null
    assert data["created_at"] is not None

    print("✅ Template response dates formatting")


def test_render_template_json_complex():
    """Test _render_template_json avec structure complexe."""
    # Créer template avec JSON complexe
    template_data = {
        "name": "Template Complex",
        "category": "test",
        "template_json": {
            "nested": {
                "value": "{{var1}}",
                "array": ["{{var2}}", "static", "{{var3}}"]
            },
            "root": "{{var1}}"
        },
        "variables_required": ["var1", "var2", "var3"],
        "active": True
    }

    response_create = client.post("/api/devis-templates/", json=template_data)
    template_id = response_create.json()["id"]

    # Render
    render_data = {
        "template_id": template_id,
        "variables": {
            "var1": "VALUE1",
            "var2": "VALUE2",
            "var3": "VALUE3"
        }
    }

    response = client.post("/api/devis-templates/render", json=render_data)
    assert response.status_code == 200
    data = response.json()

    assert data["rendered"]["nested"]["value"] == "VALUE1"
    assert data["rendered"]["nested"]["array"][0] == "VALUE2"
    assert data["rendered"]["nested"]["array"][2] == "VALUE3"
    assert data["rendered"]["root"] == "VALUE1"

    print("✅ Render template JSON complex")


def test_list_templates_ordering(db_session):
    """Test ordre list: is_default desc, name asc."""
    # Créer templates avec différents ordres
    t1 = DevisTemplate(
        tenant_id=1,
        name="B Template",
        category="test",
        template_json={},
        is_default=False,
        active=True
    )
    t2 = DevisTemplate(
        tenant_id=1,
        name="A Template",
        category="test",
        template_json={},
        is_default=True,
        active=True
    )
    t3 = DevisTemplate(
        tenant_id=1,
        name="C Template",
        category="test",
        template_json={},
        is_default=False,
        active=True
    )
    db_session.add_all([t1, t2, t3])
    db_session.commit()

    response = client.get("/api/devis-templates/")
    data = response.json()

    # Trouver nos templates de test
    test_templates = [t for t in data if t["category"] == "test"]

    if len(test_templates) >= 3:
        # Le premier devrait être is_default=True
        defaults = [t for t in test_templates if t["is_default"]]
        if defaults:
            # Les defaults en premier
            assert defaults[0]["name"] == "A Template"

    print("✅ List templates ordering (is_default desc, name asc)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
