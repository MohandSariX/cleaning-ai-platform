# 🧪 Tests Proprexis CRM

Suite de tests complète pour toutes les fonctionnalités du CRM (Phases 1, 2, 3).

---

## 📁 Structure

```
tests/
├── __init__.py                   # Package tests
├── conftest.py                   # Configuration pytest (fixtures)
├── run_all_tests.py              # Runner principal
│
├── test_phase1_emails.py         # Phase 1: Email outreach & Gmail
├── test_phase1_devis.py          # Phase 1: Devis engine & PDF
│
├── test_phase2_enrichment.py     # Phase 2: Pappers, Email Finder, DVF
├── test_phase2_scoring.py        # Phase 2: Lead scoring 300pts
├── test_phase2_scraping.py       # Phase 2: Scraping & data quality
│
├── test_claude_memory.py         # Phase 3: Mémoire persistante
├── test_claude_tools.py          # Phase 3: Tools CRM
├── test_claude_autonomy.py       # Phase 3: Décisions autonomes
└── test_claude_assistant.py      # Phase 3: Briefings & optimisation
```

---

## 🚀 Lancement

### Tous les tests

```bash
python3 tests/run_all_tests.py
```

Ou avec pytest directement :

```bash
pytest tests/ -v
```

### Test spécifique

```bash
# Un seul fichier
pytest tests/test_phase1_emails.py -v

# Une seule fonction
pytest tests/test_phase1_emails.py::test_email_templates -v
```

### Avec coverage

```bash
pytest tests/ --cov=app --cov-report=html
```

---

## 📊 Tests Disponibles

### PHASE 1 — Fondations (21 tests)

#### test_phase1_emails.py (8 tests)
- ✅ `test_email_templates` - Templates disponibles
- ✅ `test_can_send_email_quota` - Quota 50/jour
- ✅ `test_get_daily_email_count` - Compteur quotidien
- ✅ `test_email_log_anti_doublon` - Anti-doublon
- ✅ `test_gmail_token_health` - Santé token Gmail
- ✅ `test_email_template_variables` - Variables templates
- ✅ `test_relance_timing` - Timing relances J+3
- ✅ `test_email_log_structure` - Structure email_logs

#### test_phase1_devis.py (13 tests)
- ✅ `test_load_rules` - Chargement devis_rules.json
- ✅ `test_calculate_devis_bureaux` - Calcul bureaux
- ✅ `test_calculate_devis_fin_chantier` - Calcul fin chantier
- ✅ `test_calculate_devis_copropriete` - Calcul copropriété
- ✅ `test_calculate_devis_vitrerie` - Calcul vitrerie
- ✅ `test_frequence_impact` - Impact fréquence
- ✅ `test_superficie_impact` - Impact superficie
- ✅ `test_tva_calculation` - Calcul TVA
- ✅ `test_get_questions_manquantes` - Questions manquantes
- ✅ `test_invalid_type_prestation` - Type invalide
- ✅ `test_edge_cases` - Cas limites
- ✅ `test_devis_includes_societe_info` - Infos société
- ✅ `test_duree_estimee` - Durée estimée

### PHASE 2 — Enrichissement (38 tests)

#### test_phase2_enrichment.py (11 tests)
- ✅ `test_pappers_enrichment_structure` - Structure Pappers
- ✅ `test_pappers_ca_parsing` - Parsing CA
- ✅ `test_email_finder_coverage` - Couverture emails
- ✅ `test_email_finder_format_validation` - Validation format
- ✅ `test_dvf_source_detection` - Détection DVF
- ✅ `test_dvf_prospects_created` - Prospects DVF
- ✅ `test_permis_construire_detection` - Détection permis
- ✅ `test_permis_construire_prospects` - Prospects permis
- ✅ `test_enrichment_score_impact` - Impact sur score
- ✅ `test_multiple_sources_bonus` - Bonus multi-sources
- ✅ `test_enrichment_data_quality` - Qualité données

#### test_phase2_scoring.py (14 tests)
- ✅ `test_score_labels` - Labels /100
- ✅ `test_score_joignabilite` - Joignabilité (80pts)
- ✅ `test_score_identite` - Identité (60pts)
- ✅ `test_score_potentiel` - Potentiel (80pts)
- ✅ `test_score_signaux` - Signaux (80pts)
- ✅ `test_calculate_score_complete` - Score complet 300pts
- ✅ `test_extract_pappers_data` - Parsing Pappers
- ✅ `test_extract_permis_data` - Détection permis
- ✅ `test_extract_dvf_data` - Détection DVF
- ✅ `test_score_distribution` - Distribution scores
- ✅ `test_score_categories_balance` - Équilibre catégories
- ✅ `test_score_explanation_format` - Format explication
- ✅ `test_score_normalization` - Normalisation 300→100
- ✅ `test_score_consistency` - Cohérence calcul

#### test_phase2_scraping.py (13 tests)
- ✅ `test_prospects_database_not_empty` - Base non vide
- ✅ `test_prospects_have_required_fields` - Champs obligatoires
- ✅ `test_prospects_pages_jaunes_source` - Source Pages Jaunes
- ✅ `test_prospects_data_quality` - Qualité données
- ✅ `test_prospects_no_duplicates` - Absence doublons
- ✅ `test_prospects_score_range` - Plage scores valide
- ✅ `test_prospects_status_valid` - Statuts valides
- ✅ `test_prospects_cities_distribution` - Distribution villes
- ✅ `test_prospects_industries` - Distribution industries
- ✅ `test_prospects_created_recently` - Prospects récents
- ✅ `test_dvf_prospects_structure` - Structure DVF
- ✅ `test_permis_prospects_structure` - Structure permis
- ✅ `test_prospects_score_explanation_not_empty` - Explications

### PHASE 3 — Claude l'associée IA (28 tests)

#### test_claude_memory.py (8 tests)
- ✅ `test_store_and_retrieve` - Stockage/récupération mémoire
- ✅ `test_search_by_context` - Recherche par contexte
- ✅ `test_log_decision` - Logging décisions
- ✅ `test_update_decision_outcome` - MAJ résultat
- ✅ `test_conversation_history` - Historique conversations
- ✅ `test_initialize_default_memories` - Init mémoires par défaut

#### test_claude_tools.py (6 tests)
- ✅ `test_get_prospects` - Récupération prospects
- ✅ `test_get_crm_statistics` - Stats CRM
- ✅ `test_update_prospect` - Modification prospect
- ✅ `test_send_prospecting_email` - Envoi email
- ✅ `test_generate_quote` - Génération devis

#### test_claude_autonomy.py (8 tests)
- ✅ `test_can_act_autonomously_email` - Autonomie emails
- ✅ `test_can_act_autonomously_devis` - Autonomie devis
- ✅ `test_can_act_autonomously_negotiation` - Autonomie négociation
- ✅ `test_should_escalate_devis` - Escalation devis
- ✅ `test_should_escalate_negotiation` - Escalation négociation
- ✅ `test_get_daily_counters` - Compteurs quotidiens
- ✅ `test_get_autonomy_status` - Status autonomie

#### test_claude_assistant.py (6 tests)
- ✅ `test_generate_daily_briefing` - Briefing quotidien
- ✅ `test_generate_weekly_report` - Rapport hebdo
- ✅ `test_get_crm_stats` - Stats CRM
- ✅ `test_analyze_email_performance` - Analyse emails
- ✅ `test_suggest_optimizations` - Suggestions optim
- ✅ `test_run_optimization_cycle` - Cycle complet

**Total : 87 tests**
- Phase 1 : 21 tests ✅
- Phase 2 : 38 tests ✅
- Phase 3 : 28 tests ✅

---

## 🔧 Configuration

### Prérequis

```bash
pip install pytest pytest-cov
```

### Variables d'environnement

Les tests utilisent le fichier `.env` du projet.

Nécessaires :
- `GROQ_API_KEY` - API Groq
- Database PostgreSQL configurée

### Fixtures

Définies dans `conftest.py` :

- `db_session` - Session base de données
- `sample_prospect` - Prospect d'exemple
- `groq_api_key` - Clé API Groq

---

## 📈 Coverage

Après exécution avec `--cov`, ouvrir :

```bash
open htmlcov/index.html
```

**Objectif** : >80% coverage

---

## 🐛 Debug

### Afficher les prints

```bash
pytest tests/ -v -s
```

### Arrêter au premier échec

```bash
pytest tests/ -x
```

### Mode verbose maximum

```bash
pytest tests/ -vv --tb=long
```

---

## ✅ CI/CD

Intégration dans GitHub Actions (à venir) :

```yaml
- name: Run tests
  run: python3 tests/run_all_tests.py
```

---

## 📝 Ajouter un test

1. Créer `tests/test_mon_module.py`
2. Importer pytest et le module à tester
3. Écrire les fonctions `test_*`
4. Lancer `pytest tests/test_mon_module.py -v`

Exemple :

```python
import pytest
from app.mon_module import ma_fonction

def test_ma_fonction():
    result = ma_fonction(param1, param2)
    assert result == expected_value, "Message si échec"
```

---

**Les tests garantissent la qualité du code ! 🎯**
