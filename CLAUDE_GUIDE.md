# 🤖 GUIDE CLAUDE L'ASSOCIÉE IA

Guide complet d'utilisation de Claude, l'associée IA de Proprexis.

---

## 🎯 Qu'est-ce que Claude ?

Claude est ton associée virtuelle qui gère **100% de la prospection et du commercial** pendant que tu te concentres sur les chantiers.

### Ce que Claude fait automatiquement :

✅ **Prospection**
- Scraping nightly (Pages Jaunes, 9 depts IDF)
- Enrichissement multi-sources (Pappers, Permis, Email Finder)
- Scoring 300 points des prospects
- Envoi emails prospection (quota 50/jour)

✅ **Qualification**
- Analyse toutes les réponses emails
- Pose les bonnes questions
- Collecte infos pour devis

✅ **Commercial**
- Génère devis automatiquement (<10k€)
- Négocie prix (jusqu'à -15%)
- Suit le pipeline complet

✅ **Reporting**
- Briefing quotidien (8h) sur Telegram
- Rapport hebdomadaire (lundi 9h)
- Alertes temps réel

✅ **Optimisation**
- A/B testing emails
- Analyse patterns succès
- Ajuste stratégie automatiquement

---

## 💬 Comment parler à Claude

### Sur Telegram

Envoie un message au bot Telegram. Claude répond instantanément.

**Exemples de questions** :

```
"Claude, status ?"
"Combien de prospects cette semaine ?"
"Montre-moi les 10 meilleurs prospects"
"Envoie 20 emails aux prospects du 94"
"Quel est le taux de réponse ?"
"Génère un devis pour le prospect #123"
"Enrichis les 50 meilleurs prospects"
```

### Commandes spéciales

- `/status` — État du CRM en temps réel
- `/brief` — Briefing quotidien complet
- `/help` — Liste des commandes

---

## 🎛️ Ce que Claude peut faire SEULE

### ✅ Actions Autonomes

| Action | Limite | Condition |
|--------|--------|-----------|
| Envoyer emails prospection | 50/jour | Prospect a email + status new/scored |
| Enrichir prospect (Pappers) | 50€/jour | Score ≥40 |
| Générer devis | <10k€ | Toutes infos collectées |
| Négocier prix | -15% max | Client demande remise |
| Créer chantier | ∞ | Devis signé |
| Envoyer facture | ∞ | Chantier terminé |

### ⚠️ Actions nécessitant VALIDATION

Claude t'envoie un message Telegram pour valider :

- **Devis >15k€** (priorité haute)
- **Remise >15%** (priorité moyenne)
- **Budget quotidien dépassé** (priorité basse)
- **Question hors périmètre** (juridique, RH, litige)
- **Client mécontent** détecté (priorité urgente)
- **Situation ambiguë** (par précaution)

**Format validation** :
```
Mohand, tu reçois sur Telegram :

🔴 VALIDATION REQUISE

Action : generate_devis
Raison : Devis >15k€
Priorité : HIGH

Contexte :
  • Prospect : Syndic ABC
  • Montant : 18,000€

Décision #42

Réponds :
  ✅ "valide #42" pour approuver
  ❌ "refuse #42" pour refuser
  💬 Ou pose des questions
```

---

## 📊 Quotas & Limites

### Quotas Quotidiens

```
📧 Emails prospection : 50/jour (Gmail)
💰 Budget enrichissement : 50€/jour (Pappers API)
📝 Devis autonomes : <10k€
🎯 Remise autonome : <15%
```

### Consulter les quotas

```
curl http://localhost:8000/api/claude/autonomy
```

Ou demande à Claude : "Quel est le quota email restant ?"

---

## 🔧 Configuration

### Variables .env

```bash
# IA (Groq gratuit)
GROQ_API_KEY=gsk_xxxxx

# Telegram
TELEGRAM_BOT_TOKEN=xxxxx
TELEGRAM_CHAT_ID=xxxxx

# Pappers (enrichissement)
PAPPERS_API_KEY=xxxxx
```

### Mémoire Claude

Claude stocke automatiquement :
- **Stratégies** : ce qui fonctionne (industries, horaires, templates)
- **Learnings** : patterns de conversion
- **Décisions** : historique complet
- **Conversations** : tous les échanges Telegram

**Localisation** : PostgreSQL tables `ai_memory`, `ai_decisions`, `conversation_history`

---

## 📅 Jobs Automatiques (Scheduler)

| Job | Heure | Fréquence | Action |
|-----|-------|-----------|--------|
| Scraping nightly | 23h | Quotidien | Scrape Pages Jaunes (dept du jour) |
| Watchdog | Toutes les heures | Quotidien | Surveille factures, relances |
| Gmail check | Toutes les 15min | Quotidien | Vérifie réponses emails |
| Outreach batch | Toutes les 10min | Quotidien | Envoie emails prospection (9h-18h) |
| Relances | 10h | Quotidien | Relance prospects >3j sans réponse |
| Pappers enrich | 6h | Quotidien | Enrichit prospects prioritaires |
| Permis construire | 5h | 1er du mois | Scrape permis data.gouv |
| DVF scrape | 4h | 1er du mois | (actif mais non utilisé) |
| Email finder | 7h | Quotidien | Trouve emails manquants |
| **Briefing Claude** | **8h** | **Quotidien** | **Envoie briefing Telegram** |
| **Rapport Claude** | **9h lundi** | **Hebdo** | **Envoie rapport Telegram** |
| **Optimization** | **20h** | **Quotidien** | **A/B test & learnings** |

---

## 🧪 Tests

### Test Briefing

```bash
python3 << 'EOF'
from app.agents.claude_assistant import generate_daily_briefing
print(generate_daily_briefing())
EOF
```

### Test Tools

```bash
python3 << 'EOF'
from app.agents.claude_tools import get_prospects, get_crm_statistics

# Top 10 prospects
prospects = get_prospects({"min_score": 50, "has_email": True}, limit=10)
print(f"Found {len(prospects)} prospects")

# Stats
stats = get_crm_statistics("week")
print(f"Stats: {stats}")
EOF
```

### Test Autonomie

```bash
python3 << 'EOF'
from app.agents.claude_autonomy import can_act_autonomously, get_autonomy_status

# Vérifier si peut envoyer email
can_act, reason = can_act_autonomously("email_prospection", {"daily_sent": 30})
print(f"Can send email: {can_act} — {reason}")

# Status complet
status = get_autonomy_status()
print(f"Quota emails: {status['emails']['remaining']}/{status['emails']['quota_daily']}")
EOF
```

---

## 🚀 Lancement Production

### 1. Vérifications pré-lancement

```bash
# Tester toutes les variables .env
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

required = ['GROQ_API_KEY', 'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID', 'PAPPERS_API_KEY']
for var in required:
    val = os.getenv(var)
    print(f'✅ {var}: {val[:20] if val else 'MANQUANTE'}...')
"

# Tester PostgreSQL
python3 -c "from app.core.database import SessionLocal; db = SessionLocal(); print('✅ PostgreSQL OK'); db.close()"

# Tester Groq API
curl -X POST http://localhost:8000/api/claude/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Tu es prête ?"}'

# Tester Telegram
curl -X POST http://localhost:8000/api/claude/memory/init
```

### 2. Lancer le serveur

```bash
./start.sh
```

Ou manuellement :
```bash
export $(cat .env | grep -v '^#' | xargs)
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 3. Vérifier les logs

```
INFO:proprexis.scheduler:✅ Scheduler Proprexis démarré
INFO:proprexis.telegram_polling:🚀 Telegram polling démarré
INFO:     Application startup complete.
```

### 4. Envoyer 1er message Telegram

```
"Claude, tu es prête ?"
```

Tu devrais recevoir une réponse avec les stats du CRM.

---

## 📈 Monitoring

### Endpoints utiles

```bash
# Status Claude
curl http://localhost:8000/api/claude/status

# Autonomie (quotas)
curl http://localhost:8000/api/claude/autonomy

# Stats CRM
curl http://localhost:8000/api/scheduler/status

# Activity logs
curl http://localhost:8000/api/activity/summary
```

### Telegram

Tous les matins à 8h, tu reçois le briefing automatique.

Tous les lundis à 9h, tu reçois le rapport hebdomadaire.

Toute la journée, Claude t'envoie des alertes si nécessaire.

---

## 🐛 Troubleshooting

### Claude ne répond pas

1. Vérifier que le serveur tourne : `curl http://localhost:8000`
2. Vérifier les logs : chercher "ERROR" ou "WARNING"
3. Vérifier GROQ_API_KEY : `echo $GROQ_API_KEY`
4. Tester l'API directement : `/api/claude/ask`

### Pas de briefing le matin

1. Vérifier que le scheduler tourne : `/api/scheduler/status`
2. Vérifier le job : chercher "claude_briefing_daily" dans les jobs
3. Tester manuellement : `/brief` sur Telegram

### Quota emails dépassé

Claude arrête automatiquement à 50/jour.

Pour augmenter :
1. Migrer vers SendGrid (gratuit 100/jour)
2. Ou modifier `email_quota_daily` en mémoire

### Budget Pappers dépassé

Claude arrête automatiquement à 50€/jour.

Pour augmenter : modifier `AUTONOMY_RULES` dans `claude_autonomy.py`

---

## 📚 Ressources

- **Code** : `/app/agents/claude_*.py`
- **Mémoire** : PostgreSQL table `ai_memory`
- **Décisions** : PostgreSQL table `ai_decisions`
- **Logs** : PostgreSQL table `activity_logs`

---

## 🎯 Prochaines Améliorations

- [ ] WhatsApp Business (74% prospects ont phone, pas email)
- [ ] SendGrid integration (augmenter quota emails)
- [ ] Voice calling (Twilio pour appels automatiques)
- [ ] LinkedIn Sales Navigator
- [ ] Prédiction churn clients
- [ ] Expansion géographique auto

---

**Claude est maintenant opérationnelle. Bonne prospection ! 🚀**
