# Proprexis — Roadmap Développement v3
*Mise à jour : Avril 2026*

---

## 🏢 Contexte & Objectif

**Proprexis** est une entreprise de nettoyage professionnel en cours de développement, fondée par **Mohand Sari**.

### Statut actuel
🔧 **Phase de développement informatique** — Société pas encore créée

### Zone d'intervention future
Île-de-France — départements prioritaires : 94, 93, 92, 77, 75, 91

### Clientèle cible
- Entreprises BTP / Fin de chantier
- Promoteurs immobiliers / Agences immobilières
- Syndics de copropriété / Architectes
- Bureaux / locaux professionnels
- Hôtels, restaurants, commerces

### Vision
**Mohand réalise les chantiers et encaisse les paiements. Claude gère tout le reste.**

Un système entièrement autonome piloté par une IA associée qui prend des décisions dans un cadre défini, notifie sur Telegram et rend compte de ses actions en temps réel.

---

## 👥 Les deux associés

### Mohand — Patron physique
- Réalise les chantiers
- Encaisse les paiements
- Prend les décisions hors cadre
- Valide les actions importantes
- Reçoit les briefings de Claude chaque matin

### Claude — Associée IA (Groq API)
- Pilote tous les agents
- Prospecte, qualifie, envoie les devis
- Surveille la santé du système
- Prend des décisions dans le cadre défini
- Rend compte à Mohand via Telegram
- Ne dort jamais, ne prend pas de vacances

---

## 🤖 Stack technique actuelle

### Backend
- **Python 3.11** + FastAPI + PostgreSQL + SQLAlchemy
- **IA** : Groq API (llama-3.3-70b-versatile, gratuit)
- **IA locale** : Ollama / phi3:mini (qualification prospects)
- **Notifications** : Telegram Bot (polling)
- **Email** : Gmail API
- **PDF** : ReportLab
- **Scheduler** : APScheduler (12 jobs)

### Frontend
- **Next.js 14** + Tailwind CSS
- Thème dark/light persistant
- Dashboard temps réel

### Agents actifs (12 jobs schedulés)
| Agent | Fréquence | Rôle |
|-------|-----------|------|
| Scraper Pages Jaunes | Chaque nuit 23h | Scrape prospects par département |
| Lead Scorer | Après scraping | Score 300pts → /100 |
| Email Outreach | Toutes les 10min (9h-18h) | Envoie emails prospection (50/j max) |
| Gmail Check | Toutes les 15min | Lit les réponses reçues |
| Qualification IA | À chaque réponse | Dialogue, devis, confirmation |
| Watchdog | Toutes les heures | Surveillance système |
| Pappers Enricher | Chaque jour 6h | Enrichit CA, dirigeant, SIRET |
| Email Finder | Chaque jour 7h | Cherche emails manquants |
| Permis Construire | 1er du mois 5h | Scrape nouveaux chantiers IDF |
| DVF | 1er du mois 4h | Transactions immobilières IDF |
| Claude Briefing | Chaque jour 8h | Briefing quotidien Telegram |
| Claude Report | Lundi 9h | Rapport hebdomadaire |
| Claude Optimize | Chaque jour 20h | Optimisation continue |

---

# 🟢 DÉVELOPPEMENT — Phases avant ouverture société

> **Ces phases sont développables MAINTENANT sans créer l'entreprise**

---

## ✅ PHASE 1 — Fondations (COMPLÉTÉ)

### 1.1 Envoi emails automatique ✅
- 50 emails/jour max, espacés 10 min, fenêtre 9h-18h
- Templates par secteur (BTP, immo, syndic, architecte, bureaux)
- Anti-doublon strict via table email_logs
- Relances J+3 automatiques
- Mode test séparé du mode prod

### 1.2 Persistance totale PostgreSQL ✅
- Conversations de qualification en base
- Zéro perte au redémarrage
- Historique complet par prospect

### 1.3 Moteur de devis intelligent ✅
- Fichier devis_rules.json éditable depuis dashboard
- Grille tarifaire : fin de chantier, bureaux, copropriété, vitrerie
- Calcul au réel (tarif m² × superficie)
- Contrats : ponctuel / hebdo / mensuel / trimestriel / annuel
- Simulateur de devis dans paramètres

### 1.4 Infos légales dynamiques ✅
- SIRET, IBAN, BIC, TVA depuis devis_rules.json
- PDF devis et facture lisent les infos dynamiquement
- CGV en annexe PDF automatique

### 1.5 Token Gmail robuste ✅
- Refresh automatique silencieux
- Alerte Telegram si refresh échoue
- Script regenerate_token.py à la racine

### UI Phase 1 ✅
- Dashboard : statut Gmail + panel Outreach + rapport du jour
- Paramètres : infos société éditables + grille tarifaire + simulateur
- Fiche prospect : conversation IA + historique emails
- Page Activité : journal temps réel de toutes les actions
- Thème jour/nuit persistant

---

## ✅ PHASE 2 — Enrichissement données (COMPLÉTÉ)

### 2.2 Pappers.fr ✅
- API gratuite (400 req/mois)
- Dirigeant, SIRET, CA, effectifs, date création
- Bonus score +5 à +15 points selon CA
- Tourne chaque matin à 6h

### 2.4 Permis de construire SITADEL ✅
- CSV mensuel téléchargé le 1er du mois
- Filtre départements IDF + codes APE pertinents
- Signal fort : chantier dans 6-18 mois

### 2.5 DVF — Transactions immobilières ✅
- API data.gouv gratuite
- Transaction récente = nouveau propriétaire
- 52 376 prospects IDF créés

### 2.6 Score enrichi 300 points ✅
- **4 catégories** :
  - Joignabilité (80pts) : emails, téléphones
  - Identité (60pts) : site web, Pappers, SIRET
  - Potentiel (80pts) : zone, CA, effectifs
  - Signaux (80pts) : permis, DVF, industrie
- **Normalisation** : 300pts → /100
- **Endpoint** : POST `/api/scoring/run`

### 2.7 Email Finder ✅
- Scraping BeautifulSoup page contact
- Déduction format depuis Pappers
- Vérification domaine

---

## ✅ PHASE 3 — Claude l'associée IA (COMPLÉTÉ)

### Architecture
- **Groq API** (llama-3.3-70b-versatile) — gratuit
- **Mémoire PostgreSQL** persistante (ai_memory, ai_decisions, conversation_history)
- **Interface Telegram** long polling (dev local)
- **6 CRM tools** pour function calling :
  - `get_prospects` — Récupère prospects avec filtres
  - `update_prospect` — Modifie statut/notes
  - `send_prospecting_email` — Envoie email
  - `enrich_prospect_pappers` — Enrichit via Pappers
  - `generate_quote` — Génère devis
  - `get_crm_statistics` — Stats CRM

### Autonomie & Escalation
- **Emails** : 50/jour max, 9h-18h
- **Enrichissement** : 50€/jour budget Pappers
- **Devis** : <10k€ autonome, >10k€ → escalation Mohand
- **Négociation** : <15% discount autonome

### Briefings & Rapports
- **Quotidien** (8h) : Stats, décisions, alertes, plan du jour
- **Hebdomadaire** (lundi 9h) : KPIs, évolution, recommandations
- **Optimisation** (20h) : A/B testing, analyse performance emails

### Tests complets ✅
- **28 tests** répartis sur 4 fichiers
- `test_claude_memory.py` (8 tests)
- `test_claude_tools.py` (6 tests)
- `test_claude_autonomy.py` (8 tests)
- `test_claude_assistant.py` (6 tests)

---

## ✅ PHASE 4 — Dashboard Monitoring (COMPLÉTÉ)

### 4.1 Produits en base (migration)
- ✅ Migration devis_rules.json → PostgreSQL
- ✅ Table `products` multi-tenant
- ✅ 10 produits migrés : bureaux, fin_chantier, copropriete, vitrerie...
- ✅ API CRUD : `/api/products` (list, get, create, update, delete)
- ✅ API société : `/api/tenants/owner/config`

### 4.2 Dashboard monitoring
- ✅ Page dashboard moderne : Monitoring read-only (5-10min/jour)
- ✅ KPIs quotidiens : emails envoyés, devis générés, montant TTC, réponses
- ✅ Pipeline 5 étapes : Nouveaux → Contactés → Répondus → Devis → Gagnés
- ✅ Top prospects score >80
- ✅ Timeline activité temps réel
- ✅ API `/api/dashboard/stats`, `/api/dashboard/pipeline-chart`

### 4.3 Graphiques & Planning
- ✅ Composant `PipelineChart.tsx` : évolution 7 jours (Recharts)
- ✅ Page `/planning` : visualisation chantiers par statut
- ✅ Données temps réel depuis ActivityLog

### 4.4 Design moderne professionnel
- ✅ Thème clair : Fond #f0f2f5, cartes blanches avec ombres
- ✅ Sidebar : Bleu marine #0f1e3d, texte blanc
- ✅ Accent : Orange #f5a623 (états actifs)
- ✅ Typographie standardisée : DM Sans partout, Syne uniquement logo
- ✅ Formatage français : `toLocaleString('fr-FR')`, espace avant €
- ✅ Cartes sans bordures (box-shadow uniquement)
- ✅ Design cohérent sur toute l'application frontend

---

## ✅ PHASE 5 — Chantiers Autonomes + Escalations + Optimisations (COMPLÉTÉ)

### 5.1 Chantiers autonomes (backend)
- ✅ **Modèle Escalation** : Validation humaine avec IA recommendation
- ✅ **Agent chantier_auto.py** (374 lignes) :
  - `process_accepted_devis()` : Auto ou escalade selon seuil
  - `auto_create_chantier_from_devis()` : Planification J+7
  - `check_devis_need_escalation()` : Validation 10k€ HT (configurable)
  - `run_chantier_auto_check()` : Job quotidien 8h30
- ✅ **Seuils configurables** : devis_auto_threshold_ht, discount_auto_max_pct
- ✅ **API /api/escalations** : 6 endpoints (liste, stats, décision, config)

### 5.2 Dashboard escalations + Config autonomie (frontend)
- ✅ **Page /escalations** :
  - 4 stats cards cliquables (pending/approved/rejected/auto_resolved)
  - EscalationCard : Approve/Reject 1-clic, IA recommendation
  - Auto-resolve countdown, note décision
  - Vue read-only décisions passées
- ✅ **Page /parametres section "Autonomie Claude"** :
  - Seuil devis auto (€ HT) : Input modifiable
  - Remise max auto (%) : Input modifiable
  - 3 toggles : planning auto, notifications, escalade conflits
  - Save orange (accent color)

### 5.3 Optimisations IA avancées
- ✅ **Enhanced claude_optimizer.py** :
  - `analyze_lost_prospects()` : Patterns échecs (industrie, score)
  - `adjust_scoring_weights()` : Corrélations email/web/phone
  - `track_ab_test_results()` : Suivi variants + winner
  - `run_optimization_cycle()` : 4 analyses + auto-apply high-priority
- ✅ **API /api/optimizations** : 8 endpoints
  - GET /suggestions, /email-performance, /lost-prospects
  - GET /scoring-adjustments, /ab-test, /learnings, /strategy
  - POST /run-cycle
- ✅ **Page /optimizations** :
  - Stratégie actuelle (top industrie/ville, A/B test)
  - Performance emails (7j, taux réponse color-coded)
  - Prospects perdus (30j, patterns)
  - Suggestions prioritaires (high/medium/low)
  - Bouton "Lancer cycle" avec loading

### 5.4 Tests Phase 5 (45+ tests)
- ✅ **test_phase5_escalations.py** (12 tests) :
  - Config autonomie (get_autonomy_config)
  - Vérification seuils devis (sous/au-dessus)
  - Vérification remises (auto/escalation)
  - Création escalations avec confiance IA
  - Auto-resolve timing
  - Seuils configurables
- ✅ **test_phase5_optimizations.py** (18 tests) :
  - Performance emails (7j, taux réponse, meilleur jour)
  - Lost prospects (total, score moyen, industries)
  - Scoring adjustments (corrélations conversion)
  - A/B testing (variants, winner)
  - Cycle optimisation complet
  - Recommendations
- ✅ **test_phase5_chantier_auto.py** (15 tests) :
  - Process devis accepté (auto vs escalation)
  - Création chantier autonome
  - Planning automatique (date début, récurrence)
  - Détection conflits planning
  - Notifications client
  - Workflow complet

**Lancer** : `pytest tests/test_phase5_*.py -v`

### 5.5 Documentation complète
- ✅ **PHASE5_API.md** (450 lignes) :
  - Endpoints Escalations (6 endpoints)
  - Endpoints Optimizations (8 endpoints)
  - Configuration seuils
  - Exemples requêtes/réponses JSON
- ✅ **PHASE5_USER_GUIDE.md** (600 lignes) :
  - Interface Escalations (workflow complet)
  - Dashboard Optimisations (4 sections)
  - Configuration autonomie (paramètres)
  - Bonnes pratiques
  - Troubleshooting
- ✅ **PHASE5_ARCHITECTURE.md** (650 lignes) :
  - Structure fichiers
  - Flux décision autonome
  - Modèle de données
  - Système de confiance IA
  - Métriques & monitoring
- ✅ **docs/README.md** : Index général documentation

### 5.6 Dashboard v2 → v1
- ✅ Dashboard moderne remplace ancien dashboard
- ✅ 4 stats cards, pipeline, graphique, top prospects, timeline

**Jobs scheduler** : 13 total (+1 chantier_auto_check 8h30)

---

## ✅ PHASE 6 — Devis avancés & Templates (COMPLÉTÉ)

[Contenu déjà mis à jour ci-dessus]

---


---

## 🔷 PHASE 3.5 — Multi-tenant (FONDATIONS) [Obsolète - intégré Phase 4]

> **Préparer le système pour supporter plusieurs utilisateurs/entreprises**

### 3.5.1 Modèle Tenant
- **Table `tenants`** : id, name, email, plan, status, created_at
  - Plans : `owner` | `starter` | `pro` | `enterprise`
  - Status : `active` | `suspended` | `blocked`
- **Table `tenant_config`** : Configuration par tenant
  - gmail credentials, telegram tokens, zones_json
  - max_emails_per_day, credentials_encrypted
- **Table `tenant_subscription`** : Abonnements & facturation
  - plan, price_monthly, next_billing_date, status

### 3.5.2 Migration tenant_id
- Ajouter colonne `tenant_id` (nullable, FK) sur :
  - prospects, clients, email_logs, conversations
  - activity_logs, devis, factures, chantiers
- Créer tenant "owner" par défaut :
  - name="Proprexis", email="contact.proprexis@gmail.com"
  - plan="owner", status="active"

### 3.5.3 Tests
- `test_tenant.py` : CRUD tenant, config, subscription
- Vérifier isolation des données par tenant

---

## 🔶 PHASE 3.6 — Produits en base (REFACTORING) [Obsolète - intégré Phase 4.1]

> **Remplacer devis_rules.json par une table PostgreSQL**

### 3.6.1 Modèle Product
- **Table `products`** : Catalogue produits/services
  - id, tenant_id, name, description, category
  - unit, unit_price_ht, tva_rate, minimum_ht, active
  - Categories : `prestation` | `forfait` | `materiel`
  - Units : `m2` | `heure` | `forfait` | `mois` | `unite`

### 3.6.2 Lignes de devis/factures
- **Table `devis_lines`** : Lignes détaillées par devis
  - id, devis_id, product_id, description, quantity
  - unit_price_ht, tva_rate, total_ht
- **Table `facture_lines`** : Lignes détaillées par facture
  - Même structure que devis_lines

### 3.6.3 Migration données
- Script one-shot : migrer devis_rules.json → table products
- Supprimer devis_rules.json définitivement
- Adapter `devis_engine.py` pour lire depuis Product
  - Garder interface : `calculate(type, superficie, frequence)`

### 3.6.4 API Produits
- **POST /api/products** : Créer produit
- **GET /api/products** : Liste produits (filtres)
- **PATCH /api/products/{id}** : Modifier produit
- **DELETE /api/products/{id}** : Désactiver (soft delete)

### 3.6.5 Tests
- `test_product.py` : CRUD produits, DevisLine, FactureLine
- `test_devis_engine.py` : calculate() depuis base
- `test_api_products.py` : Endpoints API

---

## ✅ PHASE 6 — Devis avancés & Templates (COMPLÉTÉ)

### 6.1 Analytics devis avancés
- ✅ **GET /api/devis/analytics/overview** : Stats globales N derniers jours
  - Total, envoyés, acceptés, refusés
  - CA total, CA accepté, CA pipeline
  - Taux envoi, acceptation, refus
  - Montant moyen, montant moyen accepté
- ✅ **GET /api/devis/analytics/by-type** : Analytics par type prestation
  - Groupement par service_type
  - Taux acceptation par type
  - CA par type
- ✅ **GET /api/devis/analytics/by-montant** : Analytics par tranche montant
  - 5 tranches : <1k, 1k-3k, 3k-5k, 5k-10k, >10k
  - Taux acceptation par tranche
- ✅ **GET /api/devis/analytics/evolution** : Évolution quotidienne
  - Créés, envoyés, acceptés, CA par jour
- ✅ **GET /api/devis/analytics/top-clients** : Top clients par CA
- ✅ **Page /devis/analytics** frontend :
  - 4 stats cards, graphiques Recharts
  - Sélecteur période (7j/30j/90j)

### 6.2 Templates devis personnalisables
- ✅ **Table devis_templates** : PostgreSQL
  - name, category, type_prestation
  - template_json (JSONB), variables_required
  - is_default, tenant_id (multi-tenant)
- ✅ **API /api/devis-templates** :
  - GET / : Liste templates
  - GET /{id} : Détail template
  - POST / : Créer template
  - PATCH /{id} : Modifier template
  - DELETE /{id} : Supprimer template
  - POST /render : Rendu avec variables
- ✅ **Système variables** : {{variable}} dans JSON
- ✅ **Page /devis/templates** frontend : CRUD complet

### 6.3 Personnalisation tenant
- ✅ **Colonnes tenant_config** :
  - logo_url (URL logo uploadé)
  - cgv_text (CGV personnalisées)
  - conditions_paiement (Comptant, 30j, 60j, 90j)
  - remise_max_pct (15.0% par défaut)
- ✅ **API /api/tenants/owner/config** : GET/PATCH config

### 6.4 Signature électronique
- ✅ **Colonnes devis** :
  - signature_data (TEXT Base64 canvas)
  - signed_at (TIMESTAMP)
  - signed_by (VARCHAR nom signataire)
- ✅ **POST /api/devis/{id}/sign** : Signature devis
  - Accepte signature_data + signed_by
  - Change status → "accepte"
- ✅ **Page /devis/sign/[id]** frontend :
  - HTML5 Canvas signature (touch + mouse)
  - Export Base64
  - Validation + confirmation

### 6.5 Export PDF devis
- ✅ **GET /api/devis/{id}/pdf** : Télécharger PDF
  - Génération ReportLab
  - Signature incluse si signée
  - StreamingResponse

### 6.6 Tests Phase 6
- ✅ **test_phase6_devis_avances.py** (10 tests) :
  - Analytics (overview, by-type, by-montant, top-clients)
  - Templates (création, default, variables, render)
  - Signature (fields)
  - Tenant config (personalisation)
- ✅ **9/10 tests passent** (1 échec isolation données test)

### 6.7 Migration base de données
- ✅ **migrations/add_phase6_columns.py** :
  - ALTER TABLE devis (signature_data, signed_at, signed_by)
  - ALTER TABLE tenant_config (logo_url, cgv_text, conditions_paiement, remise_max_pct)
  - CREATE TABLE devis_templates
  - CREATE INDEX (tenant_id, category, type_prestation)

---

## 🟠 PHASE 7 — Tests & Optimisations (À DÉVELOPPER)

### 7.1 Tests automatisés complets
- [ ] **Tests unitaires** : tous les agents
- [ ] **Tests intégration** : workflows complets
- [ ] **Tests E2E** : frontend + backend
- [ ] **Coverage** : >80% sur tout le code
- [ ] **CI/CD** : GitHub Actions

### 7.2 Performance & Scalabilité
- [ ] **Optimisation requêtes** PostgreSQL (indexes, EXPLAIN)
- [ ] **Cache** Redis pour données fréquentes
- [ ] **Pagination** sur toutes les listes longues
- [ ] **Lazy loading** composants frontend
- [ ] **Compression** assets (images, CSS, JS)

### 7.3 UX/UI Polish
- [ ] **Loading states** partout
- [ ] **Error handling** user-friendly
- [ ] **Animations** fluides (transitions, hover)
- [ ] **Responsive** mobile/tablet complet
- [ ] **Accessibilité** WCAG 2.1 (contraste, navigation clavier)
- [ ] **PWA** : manifest, service worker, offline mode

### 7.4 Sécurité renforcée
- [ ] **Rate limiting** sur toutes les APIs
- [ ] **Validation** stricte inputs (Pydantic)
- [ ] **Sanitization** XSS/SQL injection
- [ ] **HTTPS** enforced en production
- [ ] **Secrets** management sécurisé (.env chiffré)
- [ ] **Auth** : JWT tokens pour API
- [ ] **CORS** configuration stricte

### 7.5 Monitoring & Observabilité
- [ ] **Logs structurés** tous les agents (JSON)
- [ ] **Health checks** endpoints (/health, /ready)
- [ ] **Alertes** Telegram si erreur critique
- [ ] **Dashboard monitoring** : uptime, latence, erreurs
- [ ] **Metrics** : Prometheus/Grafana (optionnel)

### 7.6 Documentation technique
- [ ] **README** complet installation/config
- [ ] **API docs** : OpenAPI/Swagger auto-générée
- [ ] **Architecture** : diagrammes, flux décision
- [ ] **Runbook** : procédures maintenance/déploiement
- [ ] **Changelog** : historique versions

---

## 🔵 PHASE 8 — Site vitrine (PRÉPARATION)

### 8.1 Site proprexis.fr
- [ ] **Design pro** Next.js 14 + Tailwind
- [ ] **Pages** : accueil, services, zones, contact, devis instantané
- [ ] **Formulaire devis** → CRM automatique (création prospect)
- [ ] **Chat Claude 24h/24** : qualification visiteurs en direct
- [ ] **Témoignages** clients (après premiers chantiers)
- [ ] **Portfolio** : photos chantiers (banque d'images pro)

### 8.2 SEO on-page
- [ ] **Pages par ville** générées automatiquement (94, 93, 92, 77, 75, 91)
- [ ] **Pages par service** : fin de chantier, bureaux, copropriété, vitrerie
- [ ] **Contenu optimisé** : mots-clés "nettoyage professionnel IDF"
- [ ] **Meta tags** dynamiques (title, description, OG)
- [ ] **Sitemap** XML auto-généré
- [ ] **Schema.org** structured data (LocalBusiness, Service)
- [ ] **Performance** : Lighthouse score >90

### 8.3 Préparation Google My Business
- [ ] **Fiche GMB** préparée (à publier après création SAS)
- [ ] **Photos** professionnelles chantiers
- [ ] **Description** optimisée SEO local
- [ ] **Catégories** : nettoyage professionnel, fin de chantier, bureaux
- [ ] **Zone service** : départements IDF
- [ ] **Horaires** : Claude disponible 24h/24

### 8.4 Analytics & Tracking
- [ ] **Google Analytics 4** : suivi visiteurs, conversions
- [ ] **Google Search Console** : suivi SEO, indexation
- [ ] **Heatmaps** (Hotjar) : optimisation UX
- [ ] **Formulaires** trackés → ActivityLog CRM

---

# 🔴 PRODUCTION — Phases nécessitant société ouverte

> **Ces phases NE PEUVENT PAS être développées avant création SAS**

---

## ⚫ PHASE 9 — Création société + Facturation légale

### 9.1 Création SAS Proprexis
- [ ] **Legalstart** ou équivalent (~300€)
- [ ] Obtenir **SIRET** + **SIREN**
- [ ] **Immatriculation** INSEE
- [ ] **TVA** : demande numéro intracommunautaire
- [ ] **Assurance RC Pro** obligatoire

### 9.2 Compte bancaire Qonto
- [ ] **Ouvrir compte** pro Qonto
- [ ] **IBAN** + **BIC** obtenus
- [ ] **Carte bancaire** pro
- [ ] **API Qonto** : obtenir clés production

### 9.3 Facturation légale réelle
- [ ] **Remplir devis_rules.json** avec vraies infos (SIRET, IBAN, TVA)
- [ ] **Numérotation légale** factures (FAC-2026-001)
- [ ] **Mentions obligatoires** sur factures
- [ ] **Archivage légal** 10 ans

### 9.4 Intégration Qonto API (RÉELLE)
- [ ] **Lecture solde** temps réel
- [ ] **Récupération mouvements** quotidiens
- [ ] **Rapprochement automatique** factures/virements
- [ ] **Alertes** paiements reçus/anomalies

---

## ⚫ PHASE 10 — Comptabilité & TVA SAS

### 10.1 Expert-comptable
- [ ] Trouver **expert-comptable** SAS
- [ ] **Export automatique** mensuel pour EC
- [ ] **Préparation documents** : factures émises/reçues + Qonto

### 10.2 TVA réelle
- [ ] **Calcul TVA collectée** (factures émises)
- [ ] **Calcul TVA déductible** (achats, charges)
- [ ] **Solde TVA** à payer chaque mois
- [ ] **Déclaration CA3** automatique (validation Mohand)
- [ ] **Alerte seuil TVA** : passage franchise → régime réel

### 10.3 Prévision trésorerie réelle
- [ ] **Projection 30/60/90 jours** avec données Qonto
- [ ] **Croisement** : devis signés + factures attente + charges fixes
- [ ] **Alerte trésorerie négative** prévisionnelle
- [ ] **Recommandations** : accélérer encaissements ou réduire charges

### 10.4 Tableau de bord financier
- [ ] **CA réel vs objectif** temps réel
- [ ] **Marge par chantier**
- [ ] **Délai moyen paiement** clients
- [ ] **Charges fixes/variables**
- [ ] **Seuil rentabilité** mensuel

### 10.5 Dividendes & Rémunération
- [ ] **Calcul résultat** disponible pour dividendes
- [ ] **Optimisation fiscale** : salaire président vs dividendes
- [ ] **Alerte** si résultat insuffisant

---

## ⚫ PHASE 11 — Appels d'offres publics

### 11.1 Scraping marchés publics
- [ ] **Scraper** marchés-publics.gouv.fr
- [ ] **Filtres** : nettoyage + IDF + <40k€ (seuil sans publicité)
- [ ] **Alerte Telegram** nouveaux marchés
- [ ] **Deadline tracking** date limite dépôt

### 11.2 Préparation dossiers
- [ ] **Templates dossiers** : DC1, DC2, ATTRI
- [ ] **Génération automatique** depuis infos société
- [ ] **Upload documents** : Kbis, RC Pro, relevé Qonto
- [ ] **Soumission** : préparation complète, validation Mohand

### 11.3 Suivi marchés
- [ ] **Pipeline marchés** : soumis → attente → gagné/perdu
- [ ] **Taux de succès** par type de marché
- [ ] **Analyse** : pourquoi gagné/perdu

---

## ⚫ PHASE 12 — Expansion & Intelligence business

### 12.1 Agent prévision CA
- [ ] **Prédit CA** mois prochain
- [ ] **Pipeline faible** → intensifie prospection auto
- [ ] **Prévision trésorerie** 3 mois avec Qonto

### 12.2 Agent expansion automatique
- [ ] **CA stable 3 mois** → propose élargir zone
- [ ] **Analyse départements** limitrophes
- [ ] **Lance prospection** nouvelles zones automatiquement

### 12.3 Agent optimisation tarifaire
- [ ] **Analyse devis** acceptés vs refusés
- [ ] **Prix optimal** par secteur
- [ ] **Ajuste devis_rules.json** automatiquement

### 12.4 Agent recrutement
- [ ] **Charge > capacité** → génère annonce Indeed/LinkedIn
- [ ] **Filtre candidatures** automatiquement
- [ ] **Planifie entretiens** dans agenda

### 12.5 Agent veille marché
- [ ] **Surveille prix** concurrents Pages Jaunes/Google
- [ ] **Détecte nouveaux** concurrents zone
- [ ] **Benchmark tarifaire** mensuel

### 12.6 Analyse saisonnalité
- [ ] **BTP ralentit hiver**, accélère printemps
- [ ] **Claude adapte** zones et types cibles selon saison
- [ ] **Anticipation** 6 semaines à l'avance

---

## ⚫ PHASE 13 — Autonomie totale

### 13.1 Auto-diagnostic
- [ ] **Vérifie chaque nuit** : tous les agents tournent
- [ ] **Détecte anomalies** : scraper bloqué, Gmail quota, API down
- [ ] **Correction automatique** si possible
- [ ] **Alerte Mohand** seulement si échec correction

### 13.2 Auto-amélioration
- [ ] **Compare performances** semaine par semaine
- [ ] **Identifie** ce qui fonctionne, arrête ce qui échoue
- [ ] **Ajuste paramètres** sans intervention

### 13.3 Bilan annuel automatique
- [ ] **Prépare éléments** pour expert-comptable
- [ ] **Rapport annuel** : CA, charges, résultat, dividendes
- [ ] **Propositions** pour l'année suivante

### 13.4 Multi-entreprises
- [ ] **Même système** pour 2ème activité ou associé
- [ ] **Dashboard unifié**, agents séparés
- [ ] **Isolation données** par entreprise

---

## 📋 Checklist avant ouverture société

### Développement à terminer
- [x] **Phase 4** : Dashboard monitoring ✅
- [x] **Phase 5** : Chantiers autonomes + Escalations + Optimisations ✅
- [x] **Phase 6** : Devis avancés & templates ✅
- [ ] **Phase 7** : Tests & optimisations (>80% coverage)
- [ ] **Phase 8** : Site vitrine prêt (pas encore publié)

### Création société
- [ ] **Créer SAS** Proprexis (Legalstart ~300€)
- [ ] **Ouvrir Qonto** professionnel
- [ ] **Obtenir SIRET**, SIREN, TVA
- [ ] **Remplir devis_rules.json** avec vraies infos
- [ ] **Prendre expert-comptable**
- [ ] **Souscrire RC Pro** obligatoire

### Lancement
- [ ] **Publier site** proprexis.fr
- [ ] **Créer GMB** (Google My Business)
- [ ] **Lancer prospection** automatique
- [ ] **Premier client** : test complet du flux

---

## 📊 Vision finale du flux complet

```
SOURCES PROSPECTS
Pages Jaunes + Permis construire + DVF
+ Appels d'offres + Site vitrine + Bouche à oreille
              ↓
    Score enrichi 300pts (Pappers + signaux)
              ↓
  Email IA personnalisé (templates + génération IA)
              ↓
  Qualification IA — dialogue multi-échanges
              ↓
  Devis calculé depuis devis_rules.json
              ↓
  Signature → Chantier + Calendar + Confirmation
              ↓
  Mohand réalise le chantier
              ↓
  Facture auto → Qonto → Rapprochement
              ↓
  Satisfaction → Avis Google → SEO → Entrants
              ↓
  TVA → Comptabilité → Expert-comptable
              ↓
  Rapport lundi → Pipeline → Prévision → Expansion

        CLAUDE surveille et pilote tout
               ↕ Telegram
             MOHAND
      (chantiers + encaissement
       + décisions hors cadre)
```

---

## 🔑 Décisions clés prises

| Décision | Raison |
|----------|--------|
| **Développement AVANT création société** | Système parfait dès le 1er client |
| SAS au lieu d'auto-entrepreneur | Meilleure structure pour croître |
| Qonto comme banque pro | API disponible pour intégration totale |
| Groq API (gratuit) pour Claude | llama-3.3-70b excellent et gratuit |
| Ollama phi3:mini pour qualification | Coût zéro en dev |
| Telegram polling (pas webhook) | Fonctionne en local sans HTTPS |
| Pas de Google Maps | Trop complexe, valeur limitée |
| Pas de Societe.com | Doublon Pappers |
| Score 300pts normalisé /100 | Précision max, compatibilité schéma |
| Tests complets (28 tests) | Qualité garantie avant prod |
| **Phases 9-13 APRÈS création SAS** | Impossible sans SIRET/Qonto |

---

*Document vivant — mis à jour à chaque session de développement*
*Claude est l'associée IA de Proprexis — elle connaît ce document par cœur*
