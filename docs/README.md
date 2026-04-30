# Documentation Proprexis CRM

Documentation technique et guides utilisateur.

---

## 📚 Index Documentation

### Phase 5 — Autonomie & Optimisations

- **[PHASE5_API.md](./PHASE5_API.md)** — Documentation API complète
  - Endpoints Escalations
  - Endpoints Optimisations
  - Endpoints Chantiers Auto
  - Exemples requêtes/réponses

- **[PHASE5_USER_GUIDE.md](./PHASE5_USER_GUIDE.md)** — Guide utilisateur
  - Interface Escalations
  - Dashboard Optimisations
  - Configuration autonomie
  - Bonnes pratiques
  - Troubleshooting

- **[PHASE5_ARCHITECTURE.md](./PHASE5_ARCHITECTURE.md)** — Architecture technique
  - Structure fichiers
  - Flux de décision
  - Modèles de données
  - Système de confiance IA
  - Optimisations & Learning
  - Métriques & Monitoring

---

## 🚀 Quick Start

### 1. Installation

```bash
# Backend
cd cleaning-ai-platform
pip install -r requirements.txt

# Frontend
cd proprexis-frontend
npm install
```

### 2. Configuration

```bash
# Copier .env.example
cp .env.example .env

# Configurer variables
GROQ_API_KEY=your_key
TELEGRAM_BOT_TOKEN=your_token
DATABASE_URL=postgresql://...
```

### 3. Lancer

```bash
# Backend (port 8000)
uvicorn main:app --reload

# Frontend (port 3000)
cd proprexis-frontend && npm run dev
```

### 4. Tests

```bash
# Tous les tests
pytest tests/ -v

# Tests Phase 5
pytest tests/test_phase5_*.py -v

# Avec coverage
pytest --cov=app --cov-report=html
```

---

## 📖 Guides par Rôle

### Pour Utilisateurs

1. **Premier pas** → [PHASE5_USER_GUIDE.md](./PHASE5_USER_GUIDE.md)
2. **Dashboard** → Interface `/` — Stats quotidiennes
3. **Escalations** → Interface `/escalations` — Valider décisions
4. **Optimisations** → Interface `/optimizations` — Learnings IA
5. **Configuration** → Interface `/parametres` — Ajuster seuils

### Pour Développeurs

1. **Architecture** → [PHASE5_ARCHITECTURE.md](./PHASE5_ARCHITECTURE.md)
2. **API** → [PHASE5_API.md](./PHASE5_API.md)
3. **Tests** → `tests/test_phase5_*.py`
4. **Code** → `app/agents/chantier_auto.py`, `app/agents/claude_optimizer.py`

---

## 🏗️ Architecture Globale

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (Next.js)                │
│  Dashboard | Escalations | Optimizations | Config  │
└────────────────────┬────────────────────────────────┘
                     │ HTTP/REST
┌────────────────────▼────────────────────────────────┐
│                 Backend (FastAPI)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │   API    │  │  Agents  │  │   Scheduler      │  │
│  │ Routers  │  │ Auto+IA  │  │   (APScheduler)  │  │
│  └──────────┘  └──────────┘  └──────────────────┘  │
└────────────────────┬────────────────────────────────┘
                     │ SQLAlchemy
┌────────────────────▼────────────────────────────────┐
│              PostgreSQL Database                    │
│  prospects | clients | devis | chantiers |          │
│  escalations | ai_memory | activity_log  |          │
└─────────────────────────────────────────────────────┘
```

---

## 🔑 Concepts Clés

### Autonomie

Claude prend des décisions automatiquement dans des **seuils configurables**:
- Devis <10k€ → Création chantier auto
- Devis ≥10k€ → Escalation pour validation

### Escalations

Décisions importantes nécessitant **validation humaine**:
- Claude recommande (Approve/Reject)
- Score de confiance 0-100%
- Auto-resolve si pas de décision sous X heures

### Optimisations

Claude apprend en continu:
- Performance emails (taux réponse)
- Prospects perdus (patterns)
- Scoring (corrélations conversion)
- A/B testing automatique

### Learnings

Mémoire persistante dans `ai_memory`:
- Meilleurs jours/heures emails
- Industries qui convertissent
- Poids scoring optimaux
- Stratégies gagnantes

---

## 📊 Phases Projet

- ✅ **Phase 1** — Fondations (emails, devis, chantiers)
- ✅ **Phase 2** — Enrichissement (scraping, APIs, scoring 300pts)
- ✅ **Phase 3** — Claude l'associée (autonomie, mémoire, Telegram)
- ✅ **Phase 4** — Dashboard monitoring (stats, KPIs, design moderne)
- ✅ **Phase 5** — Chantiers auto + Escalations + Optimisations IA
- ✅ **Phase 6** — Tests + Documentation (actuelle)
- 🔜 **Phase 7** — Déploiement production
- 🔜 **Phase 9+** — Facturation, comptabilité (nécessite société)

---

## 🧪 Tests

### Structure

```
tests/
├── conftest.py                     # Fixtures pytest
├── test_phase1_*.py                # Tests fondations
├── test_phase2_*.py                # Tests enrichissement
├── test_claude_*.py                # Tests IA Phase 3
├── test_phase5_escalations.py      # Tests escalations (12 tests)
├── test_phase5_optimizations.py    # Tests optimisations (18 tests)
└── test_phase5_chantier_auto.py    # Tests chantiers auto (15 tests)
```

### Coverage Cible

- `app/agents/` → 80%+
- `app/api/` → 70%+
- `app/models/` → 90%+

---

## 🔐 Sécurité

### Garde-fous

- **Seuils max absolus** : 50k€ devis, 30% remise
- **Rate limiting** : 50 chantiers/jour max
- **Validation inputs** : Tous paramètres validés
- **Rollback** : Tous changements loggés

### Secrets

Ne **jamais** commiter:
- `.env` (keys API, tokens)
- `*.pyc`, `__pycache__/`
- `.DS_Store`
- `node_modules/`

---

## 📞 Support

- **Bugs** : Créer issue GitHub
- **Questions** : Voir guides utilisateur
- **Améliorations** : Pull request welcome

---

## 📝 Changelog

### v5.0 (Phase 5+6) - 2026-04-30

- ✨ Chantiers autonomes avec escalation intelligente
- ✨ Dashboard escalations avec décisions 1-clic
- ✨ Optimisations IA avancées (lost prospects, scoring, A/B test)
- ✨ Configuration seuils autonomie via UI
- 🧪 45+ tests Phase 5
- 📚 Documentation complète (API + User Guide + Architecture)

### v4.0 (Phase 4) - 2026-04-28

- ✨ Dashboard monitoring moderne
- ✨ Produits en base (multi-tenant)
- ✨ Design professionnel DM Sans
- 📊 Graphiques pipeline évolution

### v3.0 (Phase 3) - 2026-04-25

- 🤖 Claude autonome avec Groq API
- 💬 Telegram bot + polling
- 🧠 Mémoire persistante PostgreSQL
- 📈 Briefings quotidiens + rapports hebdo

---

**Dernière mise à jour**: 2026-04-30
**Version**: v5.0 + Phase 6
