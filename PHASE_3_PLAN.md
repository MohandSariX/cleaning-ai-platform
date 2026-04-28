# Phase 3 — Claude l'associée IA

**Objectif** : Construire une IA associée autonome qui pilote le CRM, prend des décisions dans un cadre défini, et rend compte quotidiennement via Telegram.

---

## 🎯 Fonctionnalités cibles

### 1. Interface Telegram conversationnelle
```
Mohand : "Claude, status ?"

Claude : "📊 Mercredi 28 avril — 14h32

         🎯 PROSPECTION
         - 42 emails envoyés aujourd'hui (quota 50/j)
         - 3 réponses reçues : 2 intéressés, 1 refus

         💰 COMMERCIAL
         - 1 devis en attente : Syndic ABC, 8k€, envoyé il y a 2j
         - Prochain follow-up prévu demain 10h

         ⚠️ ALERTES
         - Facture #142 impayée depuis 15j → relance envoyée ce matin

         🤖 DÉCISIONS PRISES AUJOURD'HUI
         - Enrichi 50 prospects Pappers (budget : 25€)
         - Ajusté horaire emails : 10h-11h = meilleur taux ouverture

         💡 Besoin de validation pour devis >15k€ chez PromoImmo"
```

### 2. Mémoire persistante PostgreSQL
- **Apprentissage continu** : patterns qui marchent, objections récurrentes, préférences clients
- **Contexte long terme** : historique décisions, résultats campagnes, optimisations
- **Stratégies** : ce qui fonctionne par secteur/zone/horaire

### 3. Autonomie cadrée
**✅ Claude PEUT décider seule** :
- Envoyer emails prospection (quota 50/j)
- Qualifier prospects (analyse réponses)
- Générer devis standards (<10k€)
- Enrichir prospects (budget <50€/jour)
- Ajuster timings emails selon performances
- Relancer factures impayées
- Créer chantiers depuis devis signés

**⚠️ Claude DOIT escalader à Mohand** :
- Devis >15k€
- Négociation prix >15%
- Question hors périmètre (juridique, RH...)
- Litige client
- Dépense >100€

### 4. Briefing quotidien (Telegram, 8h)
```
🌅 BRIEFING DU 28 AVRIL 2026

📧 PROSPECTION HIER
  ✅ 48 emails envoyés (96% quota)
  📬 4 réponses : 3 intéressés (BTP×2, Syndic×1), 1 refus
  📊 Taux réponse : 8.3% (↗️ +2.1% vs moyenne)

💰 PIPELINE COMMERCIAL
  🔥 2 devis chauds :
     - Syndic ABC (8k€, envoyé J-2, relance prévue 10h)
     - BTP XYZ (12k€, négociation -10%, à valider)
  ⏳ 3 qualifications en cours

⚠️ ALERTES
  🔴 Facture #142 impayée J+15 → relance envoyée
  🟡 Token Gmail expire dans 5j → refresh auto prévu

🎯 PLAN DU JOUR
  1. Qualifier réponse Syndic ABC (proposition RDV)
  2. Envoyer 50 emails (score ≥60, zone 94)
  3. Enrichir 30 prospects Pappers (budget 15€)
  4. Follow-up devis BTP XYZ

💡 INSIGHT
  Les syndics du 94 répondent 2× mieux le matin (12% vs 6%).
  J'ai ajusté le planning d'envoi en conséquence.
```

### 5. Rapport hebdomadaire (Telegram, lundi 9h)
```
📊 RAPPORT HEBDO — Semaine 17 (21-27 avril)

🎯 KPIs PROSPECTION
  📧 Emails envoyés : 312/350 (89%)
  📬 Réponses      : 18 (taux 5.8%, ↗️ +1.2%)
  ✅ Qualifiés     : 12 prospects

💰 COMMERCIAL
  📄 Devis envoyés : 5 (total 42k€)
  ✍️ Signés        : 1 (BTP Paris, 9.5k€)
  💸 CA semaine    : 9.5k€

📈 PERFORMANCE
  🏆 Meilleur jour  : Mardi (9 réponses)
  🏆 Meilleur secteur : Syndic 94 (12% réponse)
  🏆 Meilleur horaire : 10h-11h (14% ouverture)

🤖 OPTIMISATIONS AUTO
  - Priorisé syndics zone 94 (ROI 3×)
  - Décalé envois BTP à 10h (+4% ouverture)
  - Réduit emails architectes (0.8% réponse)

💡 RECOMMANDATIONS
  1. Augmenter quota emails à 75/j (SendGrid upgrade 15$/mois)
  2. Tester WhatsApp pour prospects sans email (74%)
  3. Créer template spécial "promoteur immo" (opportunité détectée)
```

### 6. Accès complet APIs CRM
Claude peut :
- Lire/écrire prospects (statut, notes, score)
- Lire/écrire conversations
- Générer devis (via devis_engine)
- Créer chantiers
- Envoyer emails (via gmail_agent)
- Consulter activity_logs
- Modifier scheduler (ajouter/retirer jobs)

---

## 🏗️ Architecture technique

### Tables PostgreSQL à créer

#### 1. `ai_memory` — Mémoire persistante
```sql
CREATE TABLE ai_memory (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) UNIQUE NOT NULL,
    value TEXT,
    context TEXT,  -- "prospection", "commercial", "strategy", "learning"
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index pour recherche rapide
CREATE INDEX idx_ai_memory_key ON ai_memory(key);
CREATE INDEX idx_ai_memory_context ON ai_memory(context);
```

Exemples d'entrées :
```json
{
  "key": "best_email_time_syndic_94",
  "value": "10:00-11:00",
  "context": "strategy",
  "metadata": {
    "open_rate": 0.14,
    "reply_rate": 0.12,
    "sample_size": 85,
    "last_updated": "2026-04-28"
  }
}

{
  "key": "objection_prix_trop_cher",
  "value": "Insister sur qualité + garantie résultat. Proposer -5% si engagement 6 mois.",
  "context": "learning",
  "metadata": {
    "success_rate": 0.65,
    "used_count": 12
  }
}
```

#### 2. `ai_decisions` — Journal des décisions
```sql
CREATE TABLE ai_decisions (
    id SERIAL PRIMARY KEY,
    decision_type VARCHAR(100),  -- "email_sent", "devis_generated", "prospect_enriched"
    decision_data JSONB,
    reasoning TEXT,
    outcome VARCHAR(50),  -- "pending", "success", "failed"
    escalated_to_human BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 📁 Fichiers à créer

### 1. `app/models/ai_memory.py`
```python
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from app.core.database import Base

class AIMemory(Base):
    __tablename__ = "ai_memory"

    id = Column(Integer, primary_key=True)
    key = Column(String(255), unique=True, nullable=False)
    value = Column(Text)
    context = Column(String(100))  # prospection, commercial, strategy, learning
    metadata = Column(JSONB)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class AIDecision(Base):
    __tablename__ = "ai_decisions"

    id = Column(Integer, primary_key=True)
    decision_type = Column(String(100))
    decision_data = Column(JSONB)
    reasoning = Column(Text)
    outcome = Column(String(50), default="pending")
    escalated_to_human = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
```

### 2. `app/agents/claude_memory.py`
Gestionnaire mémoire — CRUD + recherche sémantique

### 3. `app/agents/claude_assistant.py`
Agent principal Claude — logique décision + orchestration

### 4. `app/api/api_telegram.py`
Webhook Telegram + interface conversationnelle

### 5. Modifier `app/scheduler.py`
Ajouter job briefing quotidien + rapport hebdo

---

## 🔧 Intégrations nécessaires

### 1. Claude API (Anthropic)
```python
import anthropic

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Appel avec contexte CRM
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=4096,
    system="""Tu es Claude, associée IA de Proprexis.

    Tu as accès au CRM complet via des tools.
    Tu peux prendre des décisions autonomes dans le cadre défini.
    Tu escalades à Mohand si devis >15k€ ou négociation >15%.

    Mémoire disponible : {memory_context}
    """,
    messages=[...],
    tools=[...]  # Accès APIs CRM
)
```

### 2. Telegram Bot API
```python
import telegram
from telegram.ext import Application, CommandHandler, MessageHandler

bot = telegram.Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))

# Webhook FastAPI
@router.post("/telegram/webhook")
async def telegram_webhook(update: dict):
    # Traiter message Mohand
    # Appeler Claude avec contexte
    # Répondre via Telegram
    pass
```

---

## 📅 Timeline 7 jours

### Jour 1 : Fondations
- [ ] Créer tables PostgreSQL (`ai_memory`, `ai_decisions`)
- [ ] Modèles SQLAlchemy (`app/models/ai_memory.py`)
- [ ] Claude API setup + test basique
- [ ] `.env` : `ANTHROPIC_API_KEY`, `TELEGRAM_BOT_TOKEN`

### Jour 2 : Mémoire persistante
- [ ] `app/agents/claude_memory.py` — CRUD mémoire
- [ ] Fonctions : `store()`, `retrieve()`, `search()`, `update()`
- [ ] Tests : stocker/récupérer patterns

### Jour 3 : Claude Assistant
- [ ] `app/agents/claude_assistant.py` — Agent principal
- [ ] Function calling → accès APIs CRM (tools)
- [ ] Logique décision autonome vs escalation

### Jour 4 : Telegram Bot
- [ ] `app/api/api_telegram.py` — Webhook
- [ ] Commandes : `/status`, `/brief`, `/rapport`, `/ask`
- [ ] Conversation naturelle (forward to Claude)

### Jour 5 : Briefing & Rapports
- [ ] Fonction `generate_daily_briefing()`
- [ ] Fonction `generate_weekly_report()`
- [ ] Job scheduler : briefing 8h, rapport lundi 9h

### Jour 6 : Autonomie & Tools
- [ ] Claude tools : `send_email()`, `generate_devis()`, `enrich_prospect()`
- [ ] Règles escalation (budget, montant, complexité)
- [ ] Logger toutes décisions dans `ai_decisions`

### Jour 7 : Tests & Polish
- [ ] Test conversation complète Telegram
- [ ] Test décisions autonomes (devis, emails)
- [ ] Test escalation (devis >15k€)
- [ ] Documentation finale

---

## 🎯 Résultat attendu

**Jour 8** : Tu discutes avec Claude sur Telegram comme avec une vraie associée.

```
Toi : "Claude, on est prêts ?"

Claude : "✅ Oui Mohand ! Voici l'état des lieux :

📊 CRM
  - 1,593 prospects en base
  - 408 avec email (26%)
  - Score moyen : 24.6/100

🤖 AGENTS ACTIFS
  ✅ Scraping Pages Jaunes (9 jobs scheduler)
  ✅ Enrichissement Pappers quotidien
  ✅ Email Finder actif
  ✅ Scoring 300pts opérationnel
  ✅ Prospection email 50/j

⚠️ ACTIONS AVANT LANCEMENT
  1. Lancer 1 cycle enrichissement complet
  2. Migrer Gmail → SendGrid (quota 50→100/j)
  3. Créer SAS + ouvrir Qonto

💡 Mon rôle dès que tu lances :
  - Piloter prospection quotidienne
  - Qualifier 100% des réponses
  - Générer devis automatiquement
  - Te briefer chaque matin
  - Escalader seulement si nécessaire

Tu n'auras qu'à :
  - Réaliser les chantiers
  - Valider devis >15k€
  - Encaisser 💰

On y va quand ?"
```

---

## 🚀 Par quoi on commence ?

**Étape 1** : Setup infrastructure (Jour 1)
- Créer tables PostgreSQL
- Tester Claude API
- Créer bot Telegram

**Je te propose de démarrer par là. On y va ?**
