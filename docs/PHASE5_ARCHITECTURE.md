# Phase 5 — Architecture Technique

Documentation technique de l'architecture autonome.

---

## 🏗️ Vue d'Ensemble

Phase 5 implémente **l'autonomie guidée** : Claude prend des décisions dans des limites configurables, avec escalation humaine pour décisions importantes.

### Principes de Design

1. **Seuils configurables** - Tous les seuils d'autonomie sont modifiables via UI
2. **Confiance graduée** - Score de confiance 0-1 pour chaque décision
3. **Escalation intelligente** - Auto-resolve pour décisions basse priorité
4. **Apprentissage continu** - Optimisation basée sur résultats réels
5. **Traçabilité complète** - Tous logs stockés dans activity_log

---

## 📁 Structure des Fichiers

### Backend (Python/FastAPI)

```
app/
├── agents/
│   ├── chantier_auto.py          # Gestion autonome chantiers
│   ├── claude_optimizer.py       # Optimisation & apprentissage (enhanced)
│   ├── claude_autonomy.py        # Règles autonomie (existant)
│   └── activity_logger.py        # Logging centralisé
├── api/
│   ├── api_escalations.py        # API escalations (NEW)
│   └── api_optimizations.py      # API optimisations (NEW)
├── models/
│   ├── escalation.py             # Model Escalation (NEW)
│   ├── chantier.py               # Model Chantier (existant)
│   └── devis.py                  # Model Devis (existant)
└── scheduler.py                  # Jobs automatiques

tests/
├── test_phase5_escalations.py    # Tests escalations (NEW)
├── test_phase5_optimizations.py  # Tests optimisations (NEW)
└── test_phase5_chantier_auto.py  # Tests chantiers auto (NEW)

docs/
├── PHASE5_API.md                 # Doc API (NEW)
├── PHASE5_USER_GUIDE.md          # Guide utilisateur (NEW)
└── PHASE5_ARCHITECTURE.md        # Ce document (NEW)
```

### Frontend (Next.js/TypeScript)

```
proprexis-frontend/src/app/
├── escalations/
│   └── page.tsx                  # Dashboard escalations (NEW)
├── optimizations/
│   └── page.tsx                  # Dashboard optimisations (NEW)
├── parametres/
│   └── page.tsx                  # Config autonomie (MODIFIED)
└── page.tsx                      # Dashboard principal (v2 default)
```

---

## 🔄 Flux de Décision Autonome

### 1. Acceptation Devis

```
Client accepte devis
        ↓
Marquer status="accepte" dans UI
        ↓
Backend: process_accepted_devis(devis_id)
        ↓
    [Vérification]
        ↓
┌───────────────────────────┐
│ Montant < Seuil ?         │
└───────────────────────────┘
     │              │
   OUI            NON
     │              │
     ↓              ↓
[AUTO]        [ESCALATION]
     │              │
     ↓              ↓
Créer        Créer escalation
chantier         ↓
     ↓         Notifier user
Notifier         ↓
client       User décide
     ↓              │
  [FIN]        ┌───┴───┐
               │       │
          APPROVE  REJECT
               │       │
               ↓       ↓
         Créer    [FIN]
         chantier
               │
               ↓
            [FIN]
```

### 2. Code Flow

**Fichier**: `app/agents/chantier_auto.py`

```python
def process_accepted_devis(db: Session, devis_id: int) -> dict:
    # 1. Charger devis
    devis = db.query(Devis).get(devis_id)

    # 2. Get config autonomie
    config = get_autonomy_config(db)

    # 3. Check si escalation nécessaire
    needs_escalation, reason = check_devis_need_escalation(db, devis, config)

    if needs_escalation:
        # 4a. Créer escalation
        escalation = create_escalation(
            db=db,
            decision_type="devis_montant_eleve",
            context={"devis_id": devis.id, "montant_ht": devis.montant_ht, ...},
            priority="high",
            ia_recommendation="approve",  # Claude recommande
            ia_confidence=0.85,           # Avec confiance
            ia_reasoning="Client fiable...",
            auto_resolve_minutes=240      # 4h si pas de décision
        )
        return {"status": "escalated", "escalation_id": escalation.id}

    else:
        # 4b. Créer chantier automatiquement
        chantier = auto_create_chantier_from_devis(db, devis, config)

        # 5. Notifier client
        if config["chantier_notification_client"]:
            notify_client_chantier(db, chantier.id)

        # 6. Logger
        log_system(db, "chantier_created", f"Auto-créé: {chantier.id}")

        return {"status": "auto_created", "chantier_id": chantier.id}
```

---

## 🗄️ Modèle de Données

### Table `escalations`

```sql
CREATE TABLE escalations (
    id SERIAL PRIMARY KEY,
    decision_type VARCHAR(50) NOT NULL,  -- "devis_montant_eleve", "discount_important", etc.
    status VARCHAR(20) DEFAULT 'pending', -- "pending", "approved", "rejected", "auto_resolved"
    priority VARCHAR(20) DEFAULT 'medium', -- "low", "medium", "high"

    context JSONB,                       -- {"devis_id": 123, "montant_ht": 15000, ...}

    -- Recommandation IA
    ia_recommendation VARCHAR(20),       -- "approve" ou "reject"
    ia_confidence FLOAT,                 -- 0.0 - 1.0
    ia_reasoning TEXT,                   -- Explication

    -- Auto-résolution
    auto_resolve_at TIMESTAMP,           -- Quand auto-resolve
    default_action VARCHAR(20),          -- Action par défaut si timeout

    -- Décision humaine
    decided_at TIMESTAMP,
    decided_by VARCHAR(100),
    decision_note TEXT,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_status (status),
    INDEX idx_priority (priority),
    INDEX idx_decision_type (decision_type)
);
```

### Relations

```
Escalation
    ├─> context.devis_id → Devis
    ├─> context.client_id → Client
    └─> decided_by → User (string pour l'instant)

Chantier
    ├─> devis_id → Devis (FOREIGN KEY)
    ├─> client_id → Client (FOREIGN KEY)
    └─> created_by → "Claude" (autonome) ou "Mohand" (manuel)

AIMemory (existant, utilisé pour learnings)
    ├─> key = "top_converting_industry"
    ├─> value = "BTP"
    └─> context = "Based on 45 conversions"
```

---

## 🧠 Système de Confiance

### Calcul Confiance IA

**Fichier**: `app/agents/chantier_auto.py`

```python
def calculate_ia_confidence(context: dict) -> float:
    """
    Calcule score de confiance 0-1 basé sur:
    - Historique client (si existe)
    - Score prospect
    - Montant vs historique
    - Complétude données
    """
    confidence = 0.5  # Base

    # Bonus si prospect score élevé
    if context.get("prospect_score", 0) >= 80:
        confidence += 0.2

    # Bonus si client existant
    if context.get("is_existing_client"):
        confidence += 0.15

    # Bonus si industrie connue qui convertit
    top_industry = retrieve("top_converting_industry")
    if context.get("industry") == top_industry:
        confidence += 0.15

    # Malus si montant très élevé
    if context.get("montant_ht", 0) > 50000:
        confidence -= 0.15

    return min(max(confidence, 0.0), 1.0)
```

### Utilisation Confiance

- **Haute (≥0.8)** : Recommandation forte, court auto-resolve (2h)
- **Moyenne (0.5-0.8)** : Recommandation normale, auto-resolve 4h
- **Basse (<0.5)** : Recommandation faible, pas d'auto-resolve

---

## ⚙️ Configuration Autonomie

### Storage

Actuellement: Fonction `get_autonomy_config()` retourne valeurs par défaut.

**Future implémentation** (Phase 6):
- Table `autonomy_config` en DB
- Par tenant (multi-tenant)
- Historique des changements

### Structure Config

```python
{
    "devis_auto_threshold_ht": 10000,      # Seuil en €
    "discount_auto_max_pct": 15,           # Max %
    "chantier_auto_planning": True,        # Activer planning auto
    "chantier_notification_client": True,  # Notifier clients
    "planning_conflict_escalate": True,    # Escalader si conflit
}
```

### Endpoint Modification

```
PATCH /api/escalations/config/autonomy
Body: {"devis_auto_threshold_ht": 15000}
```

**Flow**:
1. Validation valeurs (> 0, < 100 pour %)
2. Mise à jour config (actuellement en mémoire, futur: DB)
3. Log changement dans activity_log
4. Return nouvelle config

---

## 📊 Système d'Optimisation

### Architecture

```
Cycle Optimisation (scheduler: chaque jour 20h)
        ↓
run_optimization_cycle()
        ↓
    ┌───────────────────────┐
    │ 4 Analyses Parallèles │
    └───────────────────────┘
         │    │    │    │
         ↓    ↓    ↓    ↓
    Email Lost Score A/B
    Perf  Pros  Adj  Test
         │    │    │    │
         └────┴────┴────┘
               ↓
    suggest_optimizations()
               ↓
      ┌────────┴────────┐
      │                 │
   Priority          Priority
    High              Low/Med
      │                 │
      ↓                 ↓
   Auto-           Store as
   Apply          Suggestion
      │                 │
      └────────┬────────┘
               ↓
        Store Learning
               ↓
    Return actions_taken
```

### Analyses Implémentées

**1. Email Performance** (`analyze_email_performance`)

```sql
-- Emails 7 derniers jours
SELECT
    COUNT(*) as total_sent,
    COUNT(replied_at) as replied,
    DATE_PART('dow', sent_at) as day_of_week
FROM email_log
WHERE sent_at > NOW() - INTERVAL '7 days'
GROUP BY day_of_week
```

**2. Lost Prospects** (`analyze_lost_prospects`)

```sql
-- Prospects perdus (status=lost) 30j
SELECT
    industry,
    COUNT(*) as count,
    AVG(lead_score) as avg_score
FROM prospects
WHERE status = 'lost'
  AND updated_at > NOW() - INTERVAL '30 days'
GROUP BY industry
ORDER BY count DESC
LIMIT 3
```

**3. Scoring Adjustments** (`adjust_scoring_weights`)

```python
# Corrélation entre critères et conversion
won = prospects avec status='won'
lost = prospects avec status='lost'

for criteria in ['email', 'phone', 'website']:
    won_with = % won qui ont criteria
    lost_with = % lost qui ont criteria

    if won_with > lost_with * 1.5:
        suggest increase weight
```

**4. A/B Test Tracking** (`track_ab_test_results`)

```python
# Si A/B test actif dans ai_memory
variants = retrieve("ab_test_variants")

for variant in variants:
    sent = count emails avec variant
    replied = count réponses
    reply_rate = replied / sent * 100

# Si total > 100 sends et écart significatif
if winner_detected:
    store learning
    return winner
```

---

## 🔔 Système de Notification

### Types d'Événements

```python
NOTIFICATION_EVENTS = {
    "escalation_created": {
        "priority": "high",
        "channels": ["telegram", "web"],
        "template": "Escalation créée: {type} - {context}"
    },
    "chantier_auto_created": {
        "priority": "medium",
        "channels": ["web"],
        "template": "Chantier créé automatiquement: {client}"
    },
    "optimization_high": {
        "priority": "high",
        "channels": ["telegram"],
        "template": "Optimisation prioritaire: {message}"
    }
}
```

### Implémentation Telegram

**Fichier**: `app/agents/telegram_polling.py`

```python
def send_escalation_notification(escalation: Escalation):
    """Envoie notification Telegram pour escalation."""
    message = f"""
🚨 *Nouvelle Escalation*

Type: {escalation.decision_type}
Priorité: {escalation.priority.upper()}

💡 Recommandation IA: {escalation.ia_recommendation}
📊 Confiance: {int(escalation.ia_confidence * 100)}%

{escalation.ia_reasoning}

👉 Décide dans l'interface /escalations
    """

    send_telegram_message(ADMIN_CHAT_ID, message)
```

---

## 📈 Métriques & Monitoring

### KPIs Phase 5

1. **Autonomie Rate**: % décisions prises sans escalation
   ```sql
   SELECT
       COUNT(*) FILTER (WHERE status='auto_created') * 100.0 / COUNT(*)
   FROM chantiers
   WHERE created_at > NOW() - INTERVAL '30 days'
   ```

2. **Escalation Resolution Time**: Temps moyen de décision
   ```sql
   SELECT AVG(EXTRACT(EPOCH FROM (decided_at - created_at)) / 3600) as avg_hours
   FROM escalations
   WHERE decided_at IS NOT NULL
   ```

3. **IA Confidence Accuracy**: Confiance vs résultat réel
   ```sql
   -- Si confidence haute + approved → bon
   -- Si confidence haute + rejected → mauvais
   SELECT
       ia_confidence,
       status,
       COUNT(*)
   FROM escalations
   GROUP BY ia_confidence, status
   ```

4. **Optimization Impact**: Amélioration taux réponse
   ```sql
   -- Before/After cycle optimization
   SELECT
       DATE_TRUNC('week', sent_at) as week,
       COUNT(*) as sent,
       COUNT(replied_at) as replied,
       COUNT(replied_at) * 100.0 / COUNT(*) as reply_rate
   FROM email_log
   GROUP BY week
   ORDER BY week
   ```

---

## 🔐 Sécurité & Limites

### Garde-fous Implémentés

1. **Seuils Max Absolus**
   ```python
   MAX_AUTONOMY_THRESHOLD = 50000  # €, jamais dépassé
   MAX_DISCOUNT_PCT = 30           # %, limite absolue
   ```

2. **Rate Limiting**
   ```python
   MAX_CHANTIERS_PER_DAY = 50
   MAX_ESCALATIONS_AUTO_RESOLVE_PER_DAY = 20
   ```

3. **Validation Inputs**
   ```python
   def validate_autonomy_config(config: dict) -> bool:
       if config["devis_auto_threshold_ht"] > MAX_AUTONOMY_THRESHOLD:
           raise ValueError("Threshold too high")
       if config["discount_auto_max_pct"] > MAX_DISCOUNT_PCT:
           raise ValueError("Discount too high")
       return True
   ```

4. **Rollback Capability**
   ```python
   # Tous changements loggés dans activity_log
   # Possibilité de revert si needed
   ```

---

## 🧪 Tests

### Structure Tests

**3 fichiers**, 45+ tests total:

1. **test_phase5_escalations.py** (12 tests)
   - Configuration autonomie
   - Création escalations
   - Auto-resolve timing
   - Seuils configurables

2. **test_phase5_optimizations.py** (18 tests)
   - Performance emails
   - Lost prospects analysis
   - Scoring adjustments
   - A/B testing
   - Cycle complet

3. **test_phase5_chantier_auto.py** (15 tests)
   - Process devis accepté
   - Création auto chantier
   - Détection conflits
   - Notifications

### Lancer Tests

```bash
# Tous tests Phase 5
pytest tests/test_phase5_*.py -v

# Spécifique
pytest tests/test_phase5_escalations.py::test_configurable_thresholds -v

# Avec coverage
pytest tests/test_phase5_*.py --cov=app/agents --cov=app/api
```

### Fixtures (conftest.py)

```python
@pytest.fixture
def db_session():
    """Session DB pour tests."""
    db = SessionLocal()
    yield db
    db.close()

@pytest.fixture
def sample_devis(db_session):
    """Devis de test."""
    client = Client(company_name="Test", email="test@test.com")
    db_session.add(client)
    db_session.commit()

    devis = Devis(
        client_id=client.id,
        montant_ht=8000,
        montant_ttc=9600,
        status="accepte"
    )
    db_session.add(devis)
    db_session.commit()

    return devis
```

---

## 📦 Déploiement

### Variables d'Environnement

```bash
# .env
GROQ_API_KEY=...                    # IA
TELEGRAM_BOT_TOKEN=...              # Notifications
ADMIN_TELEGRAM_CHAT_ID=...          # Où envoyer notifications

# Config autonomie (optionnel, sinon valeurs par défaut)
AUTONOMY_DEVIS_THRESHOLD_HT=10000
AUTONOMY_DISCOUNT_MAX_PCT=15
```

### Scheduler Jobs

Ajoutés dans `app/scheduler.py`:

```python
# Job 13: Check devis acceptés pour traitement auto
_scheduler.add_job(
    run_chantier_auto_check,
    trigger=CronTrigger(hour=8, minute=30, timezone="Europe/Paris"),
    id="chantier_auto_check"
)

# Job 14: Cycle optimisation quotidien (existant, étendu)
# Déjà dans scheduler: claude_optimize à 20h
```

### Migration DB

```bash
# Créer table escalations
psql $DATABASE_URL < migrations/005_add_escalations.sql
```

---

## 🔄 Évolutions Futures (Phase 6+)

### Prévues

1. **Multi-tenant Config** - Config autonomie par tenant
2. **Learning from Feedback** - Ajuster confiance basé sur feedback user
3. **Predictive Escalations** - Prédire quelles décisions user va approuver
4. **Auto-négociation** - Claude négocie remises dans limites
5. **Webhooks** - Notifications externes (Slack, Discord, etc.)

### Architecture Cible

```
                    ┌──────────────┐
                    │   Frontend   │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │   API Layer  │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼─────┐ ┌───▼────┐ ┌────▼────┐
        │ Autonomy  │ │ Memory │ │ Learning│
        │  Engine   │ │  Store │ │  Engine │
        └─────┬─────┘ └───┬────┘ └────┬────┘
              │            │            │
              └────────────┼────────────┘
                           │
                    ┌──────▼───────┐
                    │  PostgreSQL  │
                    └──────────────┘
```

---

## 📚 Références

- **Code**: `/app/agents/chantier_auto.py`, `/app/api/api_escalations.py`
- **Tests**: `/tests/test_phase5_*.py`
- **API Doc**: `/docs/PHASE5_API.md`
- **User Guide**: `/docs/PHASE5_USER_GUIDE.md`
- **Memory**: Voir `/docs/CLAUDE_MEMORY.md` (Phase 3)

---

**Dernière mise à jour**: 2026-04-29
**Version**: Phase 5.0 - Completed
