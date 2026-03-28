# Proprexis — Roadmap & Vision Complète v2
*Mise à jour : Mars 2026*

---

## 🏢 Contexte & Objectif

**Proprexis** est une entreprise de nettoyage professionnel en cours de création, fondée par **Mohand Sari**.

### Statut juridique
SAS — à créer avant ouverture de l'activité

### Zone d'intervention
Île-de-France — départements prioritaires : 94, 93, 92, 77, 75, 91

### Clientèle cible
- Entreprises BTP / Fin de chantier
- Promoteurs immobiliers
- Agences immobilières
- Syndics de copropriété
- Architectes
- Bureaux / locaux professionnels
- Hôtels, restaurants, commerces

### Vision
**Mohand réalise les chantiers et encaisse les paiements. Claude gère tout le reste.**

Un système entièrement autonome piloté par une IA associée qui prend des décisions dans un cadre défini, notifie sur Telegram et rend compte de ses actions en temps réel.

### Banque professionnelle
**Qonto** — API disponible pour intégration complète (solde, virements, rapprochement)

---

## 👥 Les deux associés

### Mohand — Patron physique
- Réalise les chantiers
- Encaisse les paiements
- Prend les décisions hors cadre
- Valide les actions importantes
- Reçoit les briefings de Claude chaque matin

### Claude — Associée IA
- Pilote tous les agents
- Prospecte, qualifie, envoie les devis
- Gère la trésorerie et la comptabilité
- Surveille la santé de l'entreprise
- Prend des décisions dans le cadre défini
- Rend compte à Mohand via Telegram
- Ne dort jamais, ne prend pas de vacances

---

## 🤖 Architecture actuelle — Ce qui tourne

### Stack technique
- **Backend** : Python 3.11, FastAPI, PostgreSQL, SQLAlchemy
- **Frontend** : Next.js 14, Tailwind CSS
- **IA locale** : Ollama / phi3:mini (dev) → Mistral 7B (prod, 32Go RAM)
- **IA cloud** : Claude API — claude-sonnet (associée IA)
- **Notifications** : Telegram Bot
- **Email** : Gmail API (contact.proprexis@gmail.com)
- **Banque** : Qonto API
- **PDF** : ReportLab
- **Scheduler** : APScheduler

### Agents actifs aujourd'hui
| Agent | Fréquence | Rôle |
|-------|-----------|------|
| Scraper Pages Jaunes | Chaque nuit 23h | Scrape le département du jour |
| Lead Scorer | Après scraping | Score chaque prospect /100 |
| Email Outreach | Toutes les 10min (9h-18h) | Envoie les emails de prospection |
| Gmail Check | Toutes les 15min | Lit les réponses reçues |
| Qualification IA | À chaque réponse | Dialogue, pose les questions, envoie le devis |
| Watchdog | Toutes les heures | Factures en retard, relances, chantiers du jour |
| Pappers Enricher | Chaque jour 6h | Enrichit avec CA, dirigeant, SIRET |
| Email Finder | Chaque jour 7h | Cherche les emails manquants |
| Permis Construire | 1er du mois 5h | Scrape les nouveaux chantiers IDF |
| Rapport Telegram | Chaque jour 7h | Briefing matinal complet |

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
- Fichier devis_rules.json éditable depuis le dashboard
- Grille tarifaire : fin de chantier, bureaux, copropriété, vitrerie
- Calcul au réel (tarif m² × superficie)
- Contrats ponctuel / hebdo / mensuel / trimestriel / annuel
- Simulateur de devis dans les paramètres

### 1.4 Infos légales complètes ✅
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

## 🔄 PHASE 2 — Enrichissement (EN COURS)

### 2.1 Google Maps ⏸️
Reporté — valeur ajoutée limitée vs complexité

### 2.2 Pappers.fr ✅
- API gratuite (400 req/mois)
- Dirigeant, SIRET, CA, effectifs, date création
- Bonus score +5 à +15 points selon CA
- Tourne chaque matin à 6h

### 2.3 Societe.com ❌
Abandonné — doublon Pappers

### 2.4 Permis de construire SITADEL ✅
- CSV mensuel téléchargé automatiquement le 1er du mois
- Filtre départements IDF + codes APE pertinents
- 696 prospects créés sur premier run
- Signal fort : chantier dans 6-18 mois

### 2.5 DVF — Transactions immobilières 🔜
- API data.gouv gratuite
- Transaction récente = nouveau propriétaire = besoin nettoyage

### 2.6 Score enrichi 300 points 🔜
- Croiser toutes les sources
- Score = probabilité réelle de conversion

### 2.7 Email Finder ✅
- Scraping BeautifulSoup page contact
- Déduction format depuis Pappers
- Vérification domaine

---

## 🤖 PHASE 3 — Claude, l'Associée IA

### Vision
Claude est branchée sur toutes les APIs de l'entreprise. Elle a une mémoire persistante, une personnalité définie, et une connaissance totale de Proprexis. Tu lui parles naturellement sur Telegram comme à une vraie associée.

### Stack technique
- **Claude API** (claude-sonnet-4) — raisonnement nuancé
- **Mémoire PostgreSQL** — tout ce qui a été dit, décidé, planifié
- **Interface** : Telegram (conversation) + Dashboard (tableau de bord)
- **Accès complet** : toutes les APIs CRM + Qonto

### Ce que Claude fait seule — Prospection
```
SI pipeline < 20 prospects chauds → intensifie le scraping
SI taux_reponse < 5% sur 7 jours → change les templates
SI CA_prevu < objectif → élargit la zone géographique
SI prospect score > 85 et pas contacté depuis 3j → relance prioritaire
SI prospect répond → qualifie, génère le devis, l'envoie
SI devis accepté → crée le chantier, envoie la confirmation
```

### Ce que Claude fait seule — Finance
```
SI facture impayée > 30j → envoie relance email automatique
SI facture impayée > 60j → génère mise en demeure PDF
SI facture impayée > 90j → alerte Mohand avec dossier complet
SI virement reçu sur Qonto → rapproche avec facture, marque payée
SI solde Qonto < seuil_alerte → alerte Mohand immédiatement
SI CA_mensuel atteint 80% seuil TVA → alerte et prépare transition
SI fin de mois → prépare récapitulatif comptable pour expert-comptable
```

### Ce que Claude fait seule — Opérationnel
```
SI chantier terminé → génère facture, envoie au client
SI chantier terminé → envoie email satisfaction J+2
SI satisfaction positive → demande avis Google J+5
SI satisfaction négative → alerte Mohand + propose geste commercial
SI contrat récurrent expire dans 30j → envoie proposition renouvellement
SI nouveau chantier signé → optimise le planning de la semaine
SI matériel à réapprovisionner → alerte Mohand avec liste
```

### Ce que Claude fait seule — Veille
```
Chaque semaine → scrape appels d'offres publics < 40 000€ IDF
Chaque semaine → vérifie avis Google, répond automatiquement
Chaque mois → benchmark tarifaire concurrents
Chaque mois → ajuste devis_rules.json si nécessaire
Chaque trimestre → analyse saisonnalité et adapte les zones de scraping
```

### Ce que Claude te demande (intervention Mohand)
- Décisions hors cadre défini
- Négociations importantes (> 5 000€)
- Situations nouvelles non anticipées
- Validation des ajustements tarifaires importants
- Signature des documents légaux

### Briefing matinal quotidien (7h Telegram)
```
🌅 Bonjour Mohand — Rapport Proprexis

📊 Hier :
- 12 emails envoyés, 2 réponses
- 1 devis envoyé (1 920€ TTC)
- 47 nouveaux prospects scrappés

💰 Trésorerie :
- Solde Qonto : X €
- Attendu ce mois : X €
- Prévision mois prochain : X €

🎯 Mes décisions d'hier :
- J'ai relancé 3 prospects à J+7
- J'ai changé le template BTP (taux réponse trop faible)
- J'ai mis en retard la facture FAC-2026-003

📋 Ce que j'attends de toi :
- Décision sur le prospect [X] qui négocie
- Validation du nouveau tarif vitrerie
```

### Rapport hebdomadaire (lundi 8h)
- CA semaine vs objectif
- Pipeline complet avec probabilités
- Top 5 prospects à convertir
- Analyse de ce qui a marché / pas marché
- Plan d'action semaine suivante

---

## 🟡 PHASE 4 — Gestion chantiers autonome

### 4.1 Création chantier automatique
- Signature → chantier créé + Google Calendar sync
- Email confirmation client avec créneau exact
- Feuille d'intervention générée automatiquement

### 4.2 Planification intelligente
- Optimisation trajets (regrouper par zone)
- Contraintes : pas avant 8h, pas le dimanche
- Rappel Telegram 2h avant avec adresse + nom client + accès

### 4.3 Facturation automatique complète
- Chantier terminé → facture PDF générée et envoyée
- Contrats récurrents → facture le 1er du mois
- Relances J+30, J+45, J+60
- Mise en demeure PDF à J+60
- Intégration Stripe → bouton "Payer en ligne"
- Rapprochement automatique Qonto

### 4.4 Agent satisfaction
- J+2 → email satisfaction automatique
- Réponse positive → demande avis Google J+5
- Réponse négative → alerte Mohand + geste commercial
- Pas de réponse → relance J+5

### 4.5 Gestion contrats récurrents
- Passages planifiés automatiquement sur l'année
- Rappel renouvellement 30j avant expiration
- Proposition reconduction automatique

---

## 💼 PHASE 4B — Comptabilité & Finance SAS

### 4B.1 Intégration Qonto API
- Lecture solde en temps réel
- Récupération de tous les mouvements
- Rapprochement automatique factures / virements
- Alerte si paiement reçu non identifié

### 4B.2 Suivi TVA SAS
- Calcul TVA collectée (factures émises)
- Calcul TVA déductible (achats, charges)
- Solde TVA à payer chaque mois
- Préparation déclaration CA3 pour validation Mohand
- Alerte si anomalie détectée

### 4B.3 Préparation comptable mensuelle
- Regroupement automatique de tous les documents
- Factures émises + factures reçues + relevés Qonto
- Export propre pour l'expert-comptable
- Rapport mensuel : CA, charges, résultat estimé

### 4B.4 Prévision trésorerie
- Projection à 30, 60, 90 jours
- Croise : devis signés + factures en attente + charges fixes
- Alerte si trésorerie prévisionnelle négative
- Recommandation : accélérer les encaissements ou réduire les charges

### 4B.5 Tableau de bord financier
- CA réel vs objectif en temps réel
- Marge par type de chantier
- Délai moyen de paiement clients
- Charges fixes vs variables
- Seuil de rentabilité mensuel

### 4B.6 Dividendes et rémunération
- Calcul du résultat disponible pour dividendes
- Optimisation fiscale : salaire président vs dividendes
- Alerte si résultat insuffisant pour se payer

---

## 🟢 PHASE 5 — Croissance & Réputation

### 5.1 Site vitrine proprexis.fr
- Design pro, formulaire devis → CRM automatique
- Chat Claude 24h/24 pour qualifier les visiteurs
- Pages SEO par ville générées automatiquement

### 5.2 Agent SEO
- Contenu par ville et secteur
- Objectif : prospects entrants sans prospection

### 5.3 Agent réputation Google
- Surveille les avis en temps réel
- Répond automatiquement par IA
- Alerte si note < 4.5
- Demande d'avis ciblée aux meilleurs clients

### 5.4 Appels d'offres publics
- Scrape Marchés Publics chaque semaine
- Filtre : nettoyage + IDF + < 40 000€
- Dossier préparé automatiquement
- Alerte Mohand avec date limite

### 5.5 Google My Business automatisé
- Chaque chantier terminé → photo publiée + description
- Mise à jour horaires, services automatique
- Remontée SEO local progressive

### 5.6 Agent veille marché
- Surveille prix concurrents Pages Jaunes / Google
- Ajuste devis_rules.json si nécessaire
- Détecte nouveaux concurrents dans la zone

### 5.7 Partenariats automatiques
- Séquence dédiée : agences immo, syndics, promoteurs
- Contrat cadre avec tarifs préférentiels
- Suivi relation partenaire

---

## 🔵 PHASE 6 — Intelligence business

### 6.1 Tableau de bord exécutif
- CA réel vs prévisionnel temps réel
- Pipeline complet avec probabilités
- Rapport Telegram chaque lundi matin

### 6.2 Agent prévision CA
- Prédit le CA du mois prochain
- Si pipeline faible → intensifie prospection automatiquement
- Prévision trésorerie 3 mois

### 6.3 Agent expansion automatique
- CA stable 3 mois → propose d'élargir la zone
- Analyse départements limitrophes
- Lance prospection nouvelles zones

### 6.4 Agent optimisation tarifaire
- Analyse devis acceptés vs refusés
- Identifie prix optimal par secteur
- Met à jour devis_rules.json automatiquement

### 6.5 Agent recrutement
- Charge > capacité → génère annonce Indeed/LinkedIn
- Filtre candidatures automatiquement
- Planifie entretiens dans l'agenda

### 6.6 Analyse saisonnalité
- BTP ralentit en hiver, accélère au printemps
- Claude adapte les zones et les types de cibles selon la saison
- Anticipation 6 semaines à l'avance

---

## ⚫ PHASE 7 — Autonomie totale

### 7.1 Auto-diagnostic
- Vérifie chaque nuit que tous les agents tournent
- Détecte anomalies (scraper bloqué, Gmail quota, Ollama down)
- Tente correction automatique
- Alerte Mohand seulement si ne peut pas corriger seul

### 7.2 Auto-amélioration
- Compare performances semaine par semaine
- Identifie ce qui fonctionne, arrête ce qui ne marche pas
- Ajuste paramètres sans intervention

### 7.3 Bilan annuel automatique
- Prépare tous les éléments pour l'expert-comptable
- Rapport annuel complet : CA, charges, résultat, dividendes
- Propositions pour l'année suivante

### 7.4 Multi-entreprises
- Même système pour une 2ème activité ou un associé
- Dashboard unifié, agents séparés

---

## 📋 Checklist avant ouverture

- [ ] Finir Phase 2 (DVF + Score enrichi)
- [ ] Construire Claude l'associée IA (Phase 3)
- [ ] Créer la SAS Proprexis (Legalstart ~300€)
- [ ] Ouvrir compte Qonto professionnel
- [ ] Remplir devis_rules.json avec SIREN, SIRET, TVA, IBAN Qonto
- [ ] Prendre un expert-comptable
- [ ] Créer Google My Business
- [ ] Acheter domaine proprexis.fr
- [ ] Souscrire assurance RC Pro
- [ ] Lancer la prospection automatique

---

## 📊 Vision finale du flux complet

```
SOURCES PROSPECTS
Pages Jaunes + Permis construire + DVF
+ Appels d'offres + Site vitrine + Bouche à oreille
              ↓
    Score enrichi (Pappers + signaux)
              ↓
  Email IA personnalisé (templates Phase 1
  → génération IA Phase 3)
              ↓
  Qualification IA — dialogue multi-échanges
              ↓
  Devis calculé depuis devis_rules.json
              ↓
  Signature → Chantier + Calendar + Confirmation
              ↓
  Mohand réalise le chantier
              ↓
  Facture auto → Stripe → Rapprochement Qonto
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
| SAS au lieu d'auto-entrepreneur | Meilleure structure pour croître |
| Qonto comme banque pro | API disponible pour intégration totale |
| Claude API pour l'associée IA | Meilleur raisonnement, indispensable pour ce rôle |
| Mistral local en dev, Mistral 7B en prod | Qualité vs coût selon l'usage |
| Pas de Google Maps | Trop complexe, valeur limitée |
| Pas de Societe.com | Doublon Pappers |
| Pas de service email payant | Gratuit tant que possible |
| Permis construire = pipeline froid | Pas d'email trouvable facilement |
| Associé IA après Phase 2 | Besoin de données réelles pour être utile |
| Ouvrir après fin du dev | Système parfait dès le 1er client |

---

*Document vivant — mis à jour à chaque session de développement*
*Claude est l'associée IA de Proprexis — elle connaît ce document par cœur*