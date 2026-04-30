# CONTEXT.md — Proprexis CRM
*Ce fichier est le brief complet du projet pour Claude Code ou toute nouvelle session IA.*
*Dernière mise à jour : Mars 2026*

---

## 🎯 Projet en une phrase

Système CRM autonome pour une entreprise de nettoyage professionnel (Proprexis, IDF) — les agents IA prospectent, qualifient, envoient les devis et gèrent la facturation. Le fondateur (Mohand) réalise les chantiers et encaisse.

---

## 📁 Structure du projet

```
cleaning-ai-platform/
├── main.py                          ← FastAPI app + lifespan scheduler
├── devis_rules.json                 ← Grille tarifaire éditable (NE PAS coder en dur)
├── credentials.json                 ← Gmail OAuth (ne pas commiter)
├── token.json                       ← Gmail token (ne pas commiter)
├── regenerate_token.py              ← Script régénération token Gmail
├── .env                             ← PAPPERS_API_KEY, ANTHROPIC_API_KEY
│
├── app/
│   ├── core/
│   │   └── database.py              ← SessionLocal, Base, engine PostgreSQL
│   │
│   ├── models/                      ← SQLAlchemy models
│   │   ├── prospect.py              ← Prospects scrappés et scorés
│   │   ├── client.py                ← Clients signés (depuis prospects)
│   │   ├── devis.py                 ← Devis générés
│   │   ├── chantier.py              ← Chantiers planifiés
│   │   ├── facture.py               ← Factures émises
│   │   ├── email_log.py             ← Historique tous les emails envoyés
│   │   ├── conversation.py          ← Conversations qualification en base
│   │   ├── activity_log.py          ← Journal d'activité tous les agents
│   │   └── ai_memory.py             ← AIMemory, AIDecision, ConversationHistory (Claude)
│   │
│   ├── api/                         ← FastAPI routers (prefix="/api" dans main.py)
│   │   ├── api_prospects.py         ← GET/PATCH prospects + emails + conversation
│   │   ├── api_clients.py           ← CRUD clients
│   │   ├── api_devis.py             ← CRUD devis + PDF
│   │   ├── api_chantier.py          ← CRUD chantiers
│   │   ├── api_factures.py          ← CRUD factures + PDF
│   │   ├── api_scraping.py          ← POST scrape/start, GET scrape/status, POST scoring/run
│   │   ├── api_scheduler.py         ← GET scheduler/status, POST scheduler/run-now
│   │   ├── api_watchdog.py          ← GET watchdog/rapport, POST watchdog/refresh
│   │   │                              POST watchdog/test-telegram, test-gmail
│   │   │                              GET watchdog/token-health
│   │   ├── api_outreach.py          ← GET outreach/stats, POST send-now, send-test
│   │   │                              POST run-relances
│   │   ├── api_devis_rules.py       ← GET/PATCH devis-rules, POST simulate
│   │   ├── api_pappers.py           ← POST pappers/enrich/{id}, batch, search
│   │   ├── api_activity.py          ← GET activity/logs, summary, health, stats
│   │   │                              GET activity/claude/* (tools, decisions, escalations)
│   │   ├── api_permis.py            ← POST permis/scrape, scrape-sync
│   │   ├── api_email_finder.py      ← POST email-finder/prospect/{id}, batch-sync
│   │   ├── api_dvf.py               ← POST dvf/scrape, scrape-sync
│   │   ├── api_claude.py            ← POST webhook/telegram (Groq API conversation)
│   │   ├── api_escalations.py       ← Escalations (liste, stats, décision, config autonomie)
│   │   ├── api_optimizations.py     ← Optimisations IA (suggestions, performance, learnings)
│   │   ├── api_dashboard.py         ← Dashboard stats + pipeline chart
│   │   ├── api_products.py          ← CRUD produits multi-tenant
│   │   └── api_tenants.py           ← Config tenant owner
│   │
│   ├── agents/                      ← Agents autonomes
│   │   ├── lead_scraper.py          ← Orchestrateur scraping Pages Jaunes
│   │   ├── lead_scorer.py           ← Scoring prospects 300pts → /100
│   │   ├── scraper_pagesjaunes.py   ← Playwright scraper Pages Jaunes
│   │   ├── email_outreach_agent.py  ← Envoi emails prospection (50/j, 9h-18h)
│   │   ├── email_templates.py       ← Templates par secteur + relances
│   │   ├── gmail_agent.py           ← Gmail API : check_inbox, send_email
│   │   │                              get_gmail_service (refresh auto)
│   │   │                              check_token_health
│   │   ├── qualification_agent.py   ← Dialogue IA qualification + devis
│   │   │                              process_qualification(prospect, message, service, sujet)
│   │   ├── conversation_store.py    ← Persistance conversations PostgreSQL
│   │   ├── telegram_notifier.py     ← send_message(text) → Telegram
│   │   ├── watchdog.py              ← Surveillance factures retard, relances, chantiers
│   │   ├── activity_logger.py       ← log_*() fonctions pour tous les agents
│   │   ├── pappers_agent.py         ← Enrichissement Pappers API
│   │   ├── permis_construire_agent.py ← Scraping CSV SITADEL data.gouv
│   │   ├── email_finder_agent.py    ← Scraping BeautifulSoup + déduction email
│   │   ├── dvf_agent.py             ← Scraping DVF (transactions immo IDF)
│   │   ├── telegram_polling.py      ← Telegram long polling (getUpdates)
│   │   ├── claude_memory.py         ← Mémoire persistante Claude (PostgreSQL)
│   │   ├── claude_tools.py          ← 6 tools CRM pour function calling
│   │   ├── claude_autonomy.py       ← Règles autonomie + escalation
│   │   ├── claude_assistant.py      ← Briefings + rapports + stats
│   │   ├── claude_optimizer.py      ← Optimisation continue + A/B testing
│   │   └── chantier_auto.py         ← Gestion autonome chantiers + escalations
│   │
│   ├── utils/
│   │   ├── pdf_generator.py         ← ReportLab PDF devis
│   │   ├── pdf_facture.py           ← ReportLab PDF facture
│   │   ├── cgv_annexe.py            ← ReportLab PDF CGV (annexe devis)
│   │   └── devis_engine.py          ← Moteur calcul devis depuis devis_rules.json
│   │
│   └── scheduler.py                 ← APScheduler BackgroundScheduler
│                                      8 jobs : scraping, watchdog, gmail, outreach,
│                                      relances, pappers, permis, email_finder
│
└── frontend/
    └── src/
        ├── app/
        │   ├── layout.tsx            ← Sidebar nav + ThemeToggle
        │   ├── page.tsx              ← Dashboard principal
        │   ├── prospects/[id]/page.tsx ← Fiche prospect + conversation IA
        │   ├── clients/page.tsx
        │   ├── devis/page.tsx
        │   ├── chantiers/page.tsx
        │   ├── planning/page.tsx
        │   ├── facturation/page.tsx
        │   ├── activite/page.tsx     ← Journal d'activité temps réel
        │   ├── parametres/page.tsx   ← Infos société + tarifs + simulateur
        │   └── globals.css           ← Variables CSS thème dark/light
        │
        └── components/
            ├── SchedulerPanel.tsx    ← Panel scheduler nightly
            ├── RapportPanel.tsx      ← Rapport du jour (watchdog)
            ├── OutreachPanel.tsx     ← Stats prospection + boutons
            ├── GmailStatusPanel.tsx  ← Statut token Gmail
            ├── ThemeToggle.tsx       ← Toggle jour/nuit
            └── EmailHistoryPanel.tsx ← Historique emails par prospect
```

---

## 🗄️ Base de données PostgreSQL

### Tables principales
```sql
prospects            -- Prospects scrappés (lead_score, status, email, industry...)
clients              -- Clients convertis (depuis prospects)
devis                -- Devis générés
chantiers            -- Chantiers planifiés
factures             -- Factures émises
email_logs           -- Tous les emails envoyés (prospection, relance, qualification, devis)
conversations        -- Conversations qualification IA (historique JSON, infos JSON)
activity_logs        -- Journal d'activité complet de tous les agents
ai_memory            -- Mémoire persistante Claude (key/value + context)
ai_decisions         -- Décisions autonomes Claude (type, data, reasoning, escalated)
conversation_history -- Historique conversations Telegram Claude
escalations          -- Escalations (validation humaine pour décisions importantes)
products             -- Produits/services multi-tenant (remplace devis_rules.json)
tenants              -- Configuration multi-tenant
```

### Statuts prospect
```
new → scored → email_generated → contacted → replied → to_followup → signed / lost
```

### Statuts conversation
```
en_cours → devis_envoye → signe / perdu
```

---

## ⚙️ Configuration

### .env
```
PAPPERS_API_KEY=xxx
GROQ_API_KEY=xxx              ← Groq API pour Claude (gratuit, llama-3.3-70b)
TELEGRAM_BOT_TOKEN=xxx        ← Bot Telegram pour interface Claude
TELEGRAM_CHAT_ID=xxx          ← ID chat Mohand pour notifications
```

### devis_rules.json (racine projet)
Contient : tarifs, TVA, validité devis, questions qualification par type, infos société
NE JAMAIS coder les tarifs ou infos société en dur dans le code — toujours lire depuis ce fichier.

### Scheduler — 13 jobs actifs
| Job ID | Déclencheur | Fonction |
|--------|-------------|----------|
| nightly_scrape | Chaque nuit 23h | run_nightly_scrape() |
| watchdog_hourly | Toutes les heures | run_watchdog() |
| gmail_check | Toutes les 15min | check_inbox() |
| outreach_batch | Toutes les 10min | run_outreach_batch() |
| relances | Chaque jour 10h | run_relances() |
| pappers_enrich | Chaque jour 6h | pappers_enrich_batch() |
| permis_construire | 1er du mois 5h | run_permis_scraper() |
| email_finder | Chaque jour 7h | find_emails_batch() |
| dvf_scraper | 1er du mois 4h | run_dvf_scraper() |
| claude_briefing | Chaque jour 8h | send_daily_briefing() |
| claude_report | Lundi 9h | send_weekly_report() |
| claude_optimize | Chaque jour 20h | run_optimization_cycle() |
| chantier_auto_check | Chaque jour 8h30 | run_chantier_auto_check() |

---

## 🤖 Agents — Logique clé

### qualification_agent.py
Fonction principale : `process_qualification(prospect, message, service, sujet="")`
- Utilise Ollama phi3:mini (dev) / Mistral 7B (prod)
- Classifie l'intention via JSON : accuse / interesse / devis / question / negociation / pas_interesse / signature / incertain
- Persiste les conversations dans PostgreSQL via ConversationStore
- Génère les questions manquantes depuis devis_rules.json
- Calcule le devis via devis_engine.py
- Notifie Telegram pour : signature, négociation, question complexe

### gmail_agent.py
- `get_gmail_service()` : refresh token automatique silencieux, alerte Telegram si échec
- `check_token_health()` : vérifie + refresh si expired_refreshable
- `check_inbox()` : lit les non-lus, appelle handle_reply() pour chaque
- `send_email(service, to, subject, body, pdf_path, cgv_path)` : envoie avec PJ optionnelles

### email_outreach_agent.py
- `run_outreach_batch()` : envoie 1 email par appel, respecte fenêtre 9h-18h et quota 50/j
- `/api/outreach/send-test` : bypass fenêtre horaire pour dev
- Anti-doublon : vérifie email_logs avant chaque envoi

### activity_logger.py
Toujours logger les actions importantes via :
```python
from app.agents.activity_logger import log_email_sent, log_email_received,
    log_qualification, log_devis, log_scraping, log_enrichment, log_system, log_error
```

### devis_engine.py
```python
from app.utils.devis_engine import calculate, get_questions_manquantes, load_rules
result = calculate(type_prestation, superficie_m2, frequence)
# Retourne : montant_ht, montant_ttc, description, duree_estimee_heures, societe...
```

---

## 🎨 Frontend — Conventions

### Design system
- Thème dark/light via `data-theme` sur `<html>`
- Variables CSS : `--bg`, `--surface`, `--card`, `--border`, `--text`, `--text-muted`, `--accent`
- Fonts : Syne (titres, fontFamily: 'Syne') + DM Sans (corps)
- Accent : `#3b82f6`

### API calls
```typescript
const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
fetch(`${API}/api/...`)
```

### Composants style inline
Tout en style inline (pas de classes Tailwind sauf utilitaires de base).
Pattern card :
```tsx
<div className="card" style={{ padding: 24 }}>
```

---

## 🚀 Lancement

```bash
# Backend
cd cleaning-ai-platform
uvicorn main:app --reload
# → http://localhost:8000

# Frontend
cd frontend
npm run dev
# → http://localhost:3000

# Ollama (IA locale)
ollama serve  # tourne déjà en arrière-plan si installé

# Tests rapides
curl http://localhost:8000/api/outreach/stats
curl -X POST http://localhost:8000/api/watchdog/test-telegram
curl -X POST http://localhost:8000/api/watchdog/test-gmail
curl -X POST http://localhost:8000/api/outreach/send-test
```

---

## 📊 État actuel du projet

### Phases complètes ✅
- ✅ **Phase 1** : Fondations (emails, persistance, devis engine, infos légales, token Gmail)
- ✅ **Phase 2** : Enrichissement données
  - 2.1-2.2 : Pappers API + Permis construire (SITADEL)
  - 2.4 : Email Finder (scraping + déduction)
  - 2.5 : DVF (transactions immobilières IDF → 52k prospects)
  - 2.6 : **Score enrichi 300 points** (joignabilité 80 + identité 60 + potentiel 80 + signaux 80 → normalisé /100)
  - 2.7 : Activity logging complet
- ✅ **Phase 3** : Claude l'associée IA
  - Groq API (llama-3.3-70b-versatile, gratuit)
  - Mémoire PostgreSQL persistante (ai_memory, ai_decisions, conversation_history)
  - Interface Telegram long polling (local dev)
  - 6 CRM tools (get_prospects, update, send_email, enrich_pappers, generate_quote, get_stats)
  - Autonomie + escalation (50 emails/j, 50€/j, devis <10k€, discount <15%)
  - Briefings quotidiens (8h) + rapports hebdo (lundi 9h)
  - Optimisation continue (20h)
  - **Tests complets** : 28 tests (memory, tools, autonomy, assistant)
- ✅ **Phase 4** : Dashboard monitoring
  - 4.1 : Produits en base (multi-tenant, remplace devis_rules.json)
  - 4.2 : Dashboard monitoring (stats quotidiennes, pipeline, KPIs)
  - 4.3 : Graphiques évolution + Planning visuel
  - 4.4 : Design moderne professionnel (DM Sans, thème clair/sombre)
- ✅ **Phase 5** : Chantiers autonomes + Escalations + Optimisations IA
  - 5.1 : **Chantiers autonomes** (backend)
    - Agent chantier_auto.py (374 lignes)
    - Création auto ou escalation selon seuil (10k€ HT configurable)
    - Modèle Escalation avec IA recommendation + confiance
    - API /api/escalations (6 endpoints)
  - 5.2 : **Dashboard escalations** (frontend)
    - Interface validation humaine 1-clic
    - Auto-resolve countdown
    - Configuration seuils autonomie (/parametres)
  - 5.3 : **Optimisations IA avancées**
    - analyze_lost_prospects() : patterns échecs
    - adjust_scoring_weights() : corrélations conversion
    - track_ab_test_results() : A/B testing automatique
    - API /api/optimizations (8 endpoints)
    - Dashboard /optimizations (stratégie, performance, suggestions)
  - 5.4 : **Tests Phase 5** (45+ tests)
    - test_phase5_escalations.py (12 tests)
    - test_phase5_optimizations.py (18 tests)
    - test_phase5_chantier_auto.py (15 tests)
  - 5.5 : **Documentation complète**
    - PHASE5_API.md (450 lignes)
    - PHASE5_USER_GUIDE.md (600 lignes)
    - PHASE5_ARCHITECTURE.md (650 lignes)
    - docs/README.md (index général)
  - 5.6 : Dashboard v2 → v1 (dashboard moderne par défaut)

### Prochaine phase — DÉVELOPPEMENT (société pas encore créée)
- 🔜 **Phase 6** : Devis avancés & templates personnalisables
- 🔜 **Phase 7** : Tests & optimisations (>80% coverage global)
- 🔜 **Phase 8** : Site vitrine proprexis.fr (préparation)

### Phases PRODUCTION — Nécessitent société ouverte (SIRET + Qonto)
- ⚫ **Phase 9** : Création SAS + Qonto API + Facturation légale
- ⚫ **Phase 10** : Comptabilité SAS + TVA réelle + Expert-comptable
- ⚫ **Phase 11** : Appels d'offres publics (besoin SIRET)
- ⚫ **Phase 12** : Expansion géographique + Intelligence business
- ⚫ **Phase 13** : Autonomie totale + Auto-diagnostic

---

## 🔑 Règles importantes

### Ne jamais faire
- Coder tarifs ou infos société en dur → toujours `devis_rules.json`
- Utiliser `conversations` dict en mémoire → toujours `ConversationStore`
- Oublier d'importer les modèles dans `main.py` (sinon `Base.metadata.create_all` rate)
- Ajouter un job scheduler sans vérifier qu'il n'existe pas déjà en commentaire

### Toujours faire
- Logger toutes les actions importantes via `activity_logger`
- Vérifier la syntaxe Python avant de livrer (`py_compile.compile`)
- Mettre `prefix="/api"` sur chaque router dans `main.py`
- Utiliser `SessionLocal()` avec `try/finally db.close()`

### Conventions nommage
- Fichiers agents : `{nom}_agent.py`
- Fichiers API : `api_{nom}.py`
- Fichiers modèles : `{nom}.py` (singulier)
- Jobs scheduler : id en snake_case sans espaces

---

## 💬 Contexte humain

**Mohand Sari** — Fondateur de Proprexis
- Entreprise pas encore créée (SAS à créer)
- Banque pro : Qonto (API disponible)
- Zone : Champigny-sur-Marne + toute l'IDF
- Objectif : ouvrir l'activité une fois le dev terminé
- Claude (l'IA) sera son associée virtuelle — "la patronne"

**Claude l'associée IA** (à construire Phase 3)
- Nom : Claude
- Rôle : associée virtuelle de Proprexis
- Interface principale : Telegram
- Accès : toutes les APIs CRM + Qonto
- Autonomie : décisions dans un cadre défini par Mohand
- Elle gère chaque agent comme un employé
- Elle rend compte à Mohand quotidiennement

---

*Ce fichier doit être lu en premier par tout agent IA travaillant sur ce projet.*
*Il est la mémoire du projet — tenir à jour à chaque session.*