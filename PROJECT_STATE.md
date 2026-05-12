# PROJECT_STATE.md

## Projet

Proprexis — système CRM/IA autonome pour entreprise de nettoyage professionnel en Île-de-France.

## Fondateur

Mohand Sari.

## Statut business

Société pas encore créée.  
Le développement informatique est en cours avant création SAS.

## Vision

Mohand réalise les chantiers et encaisse les paiements.  
Claude gère tout le reste :

- Prospection
- Qualification
- Devis
- Relances
- Monitoring
- Escalations
- Rapports Telegram
- Optimisation continue

## Zone d’intervention future

Île-de-France, avec priorité :

- 94
- 93
- 92
- 77
- 75
- 91

## Clientèle cible

- Entreprises BTP / fin de chantier
- Promoteurs immobiliers
- Agences immobilières
- Syndics de copropriété
- Architectes
- Bureaux / locaux professionnels
- Hôtels
- Restaurants
- Commerces

---

# Stack actuelle

## Backend

- Python 3.11
- FastAPI
- PostgreSQL
- SQLAlchemy
- Groq API
- Ollama / phi3:mini
- Gmail API
- Telegram Bot
- ReportLab
- APScheduler

## Frontend

- Next.js 16.2.6 (Turbopack)
- Tailwind CSS
- Dashboard temps réel
- Thème clair/sombre persistant

## IA

- Groq API : `llama-3.3-70b-versatile`
- IA locale : Ollama / `phi3:mini`
- Mémoire PostgreSQL
- Function calling avec outils CRM

---

# Phases complétées

## Phase 1 — Fondations

Statut : complétée.

Inclus :
- Emails automatiques
- PostgreSQL
- Conversations persistantes
- Moteur de devis
- Infos légales dynamiques
- Token Gmail robuste
- UI fondation

## Phase 2 — Enrichissement données

Statut : complétée.

Inclus :
- Pappers
- Permis de construire SITADEL
- DVF
- Score enrichi 300 points
- Email Finder

## Phase 3 — Claude associée IA

Statut : complétée.

Inclus :
- Groq API
- Mémoire PostgreSQL
- Telegram
- CRM tools
- Autonomie et escalations
- Briefings et rapports
- Tests

## Phase 4 — Dashboard monitoring

Statut : complétée.

Inclus :
- Produits en base
- APIs dashboard
- KPIs
- Pipeline
- Graphiques
- Planning
- Design moderne

## Phase 5 — Chantiers autonomes, escalations, optimisations

Statut : complétée.

Inclus :
- Modèle Escalation
- Agent chantier automatique
- API escalations
- Dashboard escalations
- Configuration autonomie
- Optimisations IA
- Tests Phase 5
- Documentation Phase 5

## Phase 6 — Devis avancés & templates

Statut : complétée.

Inclus :
- Analytics devis
- Templates personnalisables
- Personnalisation tenant
- Signature électronique
- Export PDF devis
- Tests Phase 6
- Migration base de données

---

# Phase actuelle

## Phase 7 — Tests & Optimisations

Statut : en cours.

Objectif :
Stabiliser l’application avant création de la société et lancement réel.

**Progress** :
- ✅ Audit complet réalisé (structure, tests, git)
- ✅ Tests stabilisés : 407 passing, 2 skipped, 0 failing
- ✅ Coverage : 61% (2058/5263 lignes non couvertes)
- ⏳ En cours : Atteindre 80% coverage

---

# Objectif immédiat

Continuer Phase 7 :

1. ✅ Audit complet projet
2. ✅ Stabilisation tests (0 échec)
3. ⏳ Coverage 61% → 80% (544 lignes à couvrir)
4. ⏳ CI/CD GitHub Actions
5. ⏳ Performance & Sécurité
6. ⏳ Documentation technique

---

# Priorités Phase 7

## 1. Tests automatisés

- Tests unitaires tous les agents
- Tests intégration workflows complets
- Tests E2E frontend + backend
- Coverage >80%
- CI/CD GitHub Actions

## 2. Performance & Scalabilité

- Optimisation requêtes PostgreSQL
- Indexes
- EXPLAIN
- Cache Redis si utile
- Pagination sur listes longues
- Lazy loading frontend
- Compression assets

## 3. UX/UI Polish

- Loading states
- Error handling user-friendly
- Animations fluides
- Responsive mobile/tablet
- Accessibilité WCAG 2.1
- PWA

## 4. Sécurité renforcée

- Rate limiting
- Validation stricte Pydantic
- Sanitization XSS/SQL injection
- HTTPS production
- Secrets management
- Auth JWT
- CORS strict

## 5. Monitoring & Observabilité

- Logs structurés JSON
- Health checks `/health` et `/ready`
- Alertes Telegram
- Dashboard uptime / latence / erreurs
- Metrics Prometheus/Grafana optionnel

## 6. Documentation technique

- README installation/config
- API docs OpenAPI/Swagger
- Architecture
- Runbook maintenance/déploiement
- Changelog

---

# Ne pas faire maintenant

Ces phases nécessitent la création officielle de la société :

- Phase 9 — Création SAS + facturation légale réelle
- Phase 10 — Comptabilité & TVA SAS
- Phase 11 — Appels d’offres publics réels
- Phase 12 — Expansion business réelle
- Phase 13 — Autonomie totale production

Ne pas intégrer en réel sans validation explicite :

- Qonto production
- TVA réelle
- Facturation légale définitive
- SIRET réel
- TVA intracommunautaire réelle
- RC Pro réelle
- Google My Business publié
- Site vitrine public

---

# Commandes utiles

```bash
pytest -v
pytest tests/test_phase5_*.py -v
pytest tests/test_phase6_devis_avances.py -v
pytest --cov=. --cov-report=term-missing
```

Frontend, à adapter selon le projet réel :

```bash
npm run lint
npm run build
npm run test
```

---

# Règle de reprise

À chaque début de session, Claude doit lire ce fichier avant de proposer un plan.

Si le code réel contredit ce fichier :
1. Signaler l’incohérence
2. Vérifier dans le code
3. Mettre à jour `PROJECT_STATE.md`
4. Mettre à jour `tasks/todo.md`
