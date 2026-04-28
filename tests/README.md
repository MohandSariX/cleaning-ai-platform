# 🧪 Tests Proprexis CRM

Suite de tests complète pour toutes les fonctionnalités du CRM.

---

## 📁 Structure

```
tests/
├── __init__.py                   # Package tests
├── conftest.py                   # Configuration pytest (fixtures)
├── run_all_tests.py              # Runner principal
├── test_claude_memory.py         # Tests mémoire persistante
├── test_claude_tools.py          # Tests tools CRM
├── test_claude_autonomy.py       # Tests décisions autonomes
└── test_claude_assistant.py      # Tests briefings & optimisation
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
pytest tests/test_claude_memory.py -v

# Une seule fonction
pytest tests/test_claude_memory.py::test_store_and_retrieve -v
```

### Avec coverage

```bash
pytest tests/ --cov=app --cov-report=html
```

---

## 📊 Tests Disponibles

### test_claude_memory.py (8 tests)
- ✅ `test_store_and_retrieve` - Stockage/récupération mémoire
- ✅ `test_search_by_context` - Recherche par contexte
- ✅ `test_log_decision` - Logging décisions
- ✅ `test_update_decision_outcome` - MAJ résultat
- ✅ `test_conversation_history` - Historique conversations
- ✅ `test_initialize_default_memories` - Init mémoires par défaut

### test_claude_tools.py (6 tests)
- ✅ `test_get_prospects` - Récupération prospects
- ✅ `test_get_crm_statistics` - Stats CRM
- ✅ `test_update_prospect` - Modification prospect
- ✅ `test_send_prospecting_email` - Envoi email
- ✅ `test_generate_quote` - Génération devis

### test_claude_autonomy.py (8 tests)
- ✅ `test_can_act_autonomously_email` - Autonomie emails
- ✅ `test_can_act_autonomously_devis` - Autonomie devis
- ✅ `test_can_act_autonomously_negotiation` - Autonomie négociation
- ✅ `test_should_escalate_devis` - Escalation devis
- ✅ `test_should_escalate_negotiation` - Escalation négociation
- ✅ `test_get_daily_counters` - Compteurs quotidiens
- ✅ `test_get_autonomy_status` - Status autonomie

### test_claude_assistant.py (6 tests)
- ✅ `test_generate_daily_briefing` - Briefing quotidien
- ✅ `test_generate_weekly_report` - Rapport hebdo
- ✅ `test_get_crm_stats` - Stats CRM
- ✅ `test_analyze_email_performance` - Analyse emails
- ✅ `test_suggest_optimizations` - Suggestions optim
- ✅ `test_run_optimization_cycle` - Cycle complet

**Total : 28 tests**

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
