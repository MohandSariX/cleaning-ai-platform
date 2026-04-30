# Phase 5 — API Documentation

Documentation des endpoints API pour la Phase 5 : Chantiers Autonomes + Escalations + Optimisations IA.

---

## 🚨 Escalations API

Gestion des décisions nécessitant validation humaine.

### `GET /api/escalations/`

Récupère toutes les escalations.

**Query Parameters:**
- `status` (optional): `pending`, `approved`, `rejected`, `auto_resolved`
- `priority` (optional): `low`, `medium`, `high`
- `limit` (optional): nombre de résultats (défaut: 50)

**Response:**
```json
[
  {
    "id": 123,
    "decision_type": "devis_montant_eleve",
    "status": "pending",
    "priority": "high",
    "context": {
      "devis_id": 456,
      "montant_ht": 15000,
      "client": "Big Corp"
    },
    "ia_recommendation": "approve",
    "ia_confidence": 0.85,
    "ia_reasoning": "Client fiable, montant cohérent",
    "auto_resolve_at": "2026-04-30T12:00:00",
    "default_action": "approve",
    "created_at": "2026-04-29T10:00:00"
  }
]
```

### `GET /api/escalations/stats`

Statistiques des escalations.

**Response:**
```json
{
  "total": 45,
  "pending": 5,
  "approved": 30,
  "rejected": 8,
  "auto_resolved": 2,
  "by_priority": {
    "high": 12,
    "medium": 20,
    "low": 13
  },
  "by_type": {
    "devis_montant_eleve": 25,
    "discount_important": 15,
    "planning_conflict": 5
  },
  "avg_resolution_time_hours": 4.2
}
```

### `POST /api/escalations/{escalation_id}/decide`

Prend une décision sur une escalation.

**Request Body:**
```json
{
  "decision": "approved",  // ou "rejected"
  "approved_by": "Mohand",
  "note": "Client premium, validé"
}
```

**Response:**
```json
{
  "status": "approved",
  "escalation_id": 123,
  "decided_at": "2026-04-29T14:30:00",
  "decided_by": "Mohand"
}
```

### `GET /api/escalations/config/autonomy`

Récupère la configuration d'autonomie.

**Response:**
```json
{
  "devis_auto_threshold_ht": 10000,
  "discount_auto_max_pct": 15,
  "chantier_auto_planning": true,
  "chantier_notification_client": true,
  "planning_conflict_escalate": true
}
```

### `PATCH /api/escalations/config/autonomy`

Modifie la configuration d'autonomie.

**Request Body:**
```json
{
  "devis_auto_threshold_ht": 15000,
  "discount_auto_max_pct": 20
}
```

**Response:**
```json
{
  "status": "updated",
  "config": {
    "devis_auto_threshold_ht": 15000,
    "discount_auto_max_pct": 20,
    "chantier_auto_planning": true,
    "chantier_notification_client": true,
    "planning_conflict_escalate": true
  }
}
```

---

## 🤖 Optimizations API

Analyse et optimisation continue par IA.

### `GET /api/optimizations/suggestions`

Récupère les suggestions d'optimisation actuelles.

**Response:**
```json
[
  {
    "type": "email_timing",
    "priority": "high",
    "message": "Taux de réponse faible (1.2%). Recommandation: tester envois matinée",
    "action": "adjust_email_schedule",
    "params": {
      "suggested_hours": [9, 10, 11]
    }
  },
  {
    "type": "scoring",
    "priority": "medium",
    "message": "Prospects avec téléphone convertissent 2x plus",
    "action": "increase_phone_weight",
    "params": {
      "current_weight": 15,
      "suggested_weight": 25
    }
  }
]
```

### `GET /api/optimizations/email-performance`

Analyse des performances emails (7 derniers jours).

**Response:**
```json
{
  "total_sent": 156,
  "replied": 4,
  "reply_rate": 2.56,
  "best_day": "Mardi",
  "best_day_count": 2,
  "recommendations": [
    "Tester templates plus courts",
    "Personnaliser lignes de sujet"
  ]
}
```

### `GET /api/optimizations/lost-prospects`

Analyse des prospects perdus (30 derniers jours).

**Response:**
```json
{
  "total": 23,
  "avg_score": 62.4,
  "by_score_range": {
    "high": 5,
    "medium": 12,
    "low": 6
  },
  "top_lost_industries": [
    {"industry": "Restaurant", "count": 8},
    {"industry": "Bureau", "count": 6},
    {"industry": "Commerce", "count": 4}
  ],
  "recommendations": [
    "Revoir approche Restaurant (8 perdus)",
    "5 prospects high-score perdus - analyser pourquoi"
  ]
}
```

### `GET /api/optimizations/scoring-adjustments`

Suggestions d'ajustement des poids de scoring.

**Response:**
```json
{
  "status": "ready",
  "sample_size": {
    "won": 45,
    "lost": 23
  },
  "adjustments": [
    {
      "criteria": "phone",
      "current_weight": 15,
      "suggested_weight": 25,
      "reason": "Conversion 2.3x meilleure avec téléphone",
      "confidence": 0.87
    },
    {
      "criteria": "website",
      "current_weight": 20,
      "suggested_weight": 15,
      "reason": "Pas de corrélation significative",
      "confidence": 0.62
    }
  ]
}
```

### `GET /api/optimizations/ab-test`

Résultats des A/B tests en cours.

**Response (test en cours):**
```json
{
  "status": "running",
  "started": "2026-04-25T09:00:00",
  "variants": [
    {
      "name": "A_original",
      "sent": 78,
      "replied": 2,
      "reply_rate": 2.56
    },
    {
      "name": "B_short",
      "sent": 82,
      "replied": 5,
      "reply_rate": 6.10
    }
  ],
  "total_sent": 160,
  "winner": null
}
```

**Response (test terminé):**
```json
{
  "status": "completed",
  "started": "2026-04-20T09:00:00",
  "winner": "B_short",
  "results": {
    "A_original": {"sent": 250, "replied": 7, "reply_rate": 2.8},
    "B_short": {"sent": 248, "replied": 15, "reply_rate": 6.05}
  }
}
```

### `POST /api/optimizations/run-cycle`

Lance un cycle d'optimisation complet.

**Response:**
```json
{
  "status": "completed",
  "timestamp": "2026-04-29T20:00:00",
  "analyses": {
    "email_performance": {"reply_rate": 2.56},
    "lost_prospects": {"total": 23},
    "scoring_adjustments": {"suggestions": 2},
    "ab_test": {"status": "running"}
  },
  "actions_taken": [
    {
      "action": "store_learning",
      "priority": "high",
      "details": "Prospects avec téléphone convertissent mieux"
    }
  ]
}
```

### `GET /api/optimizations/learnings`

Récupère les learnings récents de Claude.

**Query Parameters:**
- `limit` (optional): nombre de résultats (défaut: 20)

**Response:**
```json
{
  "count": 12,
  "learnings": [
    {
      "id": 456,
      "key": "email_best_time",
      "value": "morning_9_11",
      "context": "Taux réponse 3.2% vs 1.8% après-midi",
      "meta_data": {"confidence": 0.82},
      "created_at": "2026-04-29T08:30:00"
    }
  ]
}
```

### `GET /api/optimizations/strategy`

Récupère la stratégie actuelle.

**Response:**
```json
{
  "priority_industry": "BTP",
  "priority_city": "Paris",
  "ab_test_active": "email_template_v2",
  "top_converting_industry": "Construction",
  "top_converting_city": "Lyon",
  "last_updated": "2026-04-29T20:00:00"
}
```

---

## 🏗️ Chantiers Auto API

Gestion autonome des chantiers (endpoints existants + nouveautés).

### `POST /api/chantiers/process-accepted-devis`

Traite un devis accepté (création auto ou escalation).

**Request Body:**
```json
{
  "devis_id": 456
}
```

**Response (création autonome):**
```json
{
  "status": "auto_created",
  "chantier_id": 789,
  "date_debut": "2026-05-05T09:00:00",
  "notification_sent": true
}
```

**Response (escalation):**
```json
{
  "status": "escalated",
  "escalation_id": 123,
  "reason": "Montant 15000€ HT > seuil 10000€",
  "ia_recommendation": "approve",
  "ia_confidence": 0.85
}
```

### `GET /api/chantiers/conflicts`

Vérifie les conflits de planning.

**Query Parameters:**
- `date_debut`: date proposée (ISO format)
- `date_fin` (optional): date fin (ISO format)

**Response:**
```json
{
  "has_conflicts": true,
  "conflicts": [
    {
      "chantier_id": 101,
      "client": "Client A",
      "date_debut": "2026-05-05T08:00:00",
      "date_fin": "2026-05-05T17:00:00"
    }
  ],
  "alternative_dates": [
    "2026-05-06T09:00:00",
    "2026-05-07T09:00:00"
  ]
}
```

---

## 🔧 Configuration

Tous les seuils d'autonomie sont configurables via l'interface Paramètres ou l'API.

### Seuils par défaut

| Paramètre | Valeur | Description |
|-----------|--------|-------------|
| `devis_auto_threshold_ht` | 10000€ | Montant max HT pour création autonome |
| `discount_auto_max_pct` | 15% | Remise max pour négociation autonome |
| `chantier_auto_planning` | true | Planning automatique activé |
| `chantier_notification_client` | true | Notifications clients activées |
| `planning_conflict_escalate` | true | Escalader si conflit planning |

### Modifier les seuils

Via l'interface `/parametres` section "Autonomie Claude" ou via l'API:

```bash
curl -X PATCH http://localhost:8000/api/escalations/config/autonomy \
  -H "Content-Type: application/json" \
  -d '{
    "devis_auto_threshold_ht": 15000,
    "discount_auto_max_pct": 20
  }'
```

---

## 📊 Activity Logging

Toutes les décisions IA sont loggées dans la table `activity_log`:

- `log_claude_decision()` - Décisions autonomes
- `log_claude_escalation()` - Escalations créées
- `log_claude_optimization()` - Cycles d'optimisation
- `log_chantier_created()` - Chantiers créés
- `log_chantier_updated()` - Modifications chantiers

Accessible via `/activite` dans l'interface.

---

## 🧪 Testing

Tests disponibles dans:
- `tests/test_phase5_escalations.py` - Tests escalations
- `tests/test_phase5_optimizations.py` - Tests optimisations
- `tests/test_phase5_chantier_auto.py` - Tests chantiers auto

Lancer les tests:
```bash
pytest tests/test_phase5_*.py -v
```
