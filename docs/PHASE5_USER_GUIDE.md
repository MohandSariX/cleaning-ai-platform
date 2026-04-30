# Phase 5 — Guide Utilisateur

Guide d'utilisation des fonctionnalités autonomes de Claude.

---

## 📋 Vue d'ensemble

La Phase 5 introduit **l'autonomie intelligente** de Claude avec 3 piliers:

1. **Chantiers Autonomes** - Création automatique dès qu'un devis est accepté
2. **Escalations** - Validation humaine pour décisions importantes
3. **Optimisations IA** - Apprentissage continu et amélioration automatique

---

## 🚨 Escalations — Validation Humaine

### Accès

Menu latéral → **Escalations** (icône ⚠️)

### Qu'est-ce qu'une escalation ?

Une escalation est créée quand Claude doit prendre une décision importante qui dépasse ses seuils d'autonomie:

- **Devis élevé** : >10 000€ HT (configurable)
- **Remise importante** : >15% (configurable)
- **Conflit planning** : Deux chantiers qui se chevauchent

### Interface Escalations

L'interface affiche:

1. **Statistiques** (en haut):
   - Total escalations
   - En attente / Approuvées / Rejetées
   - Temps moyen de résolution

2. **Liste des escalations** avec:
   - **Type** : devis_montant_eleve, discount_important, etc.
   - **Priorité** : 🔴 High, 🟠 Medium, 🔵 Low
   - **Contexte** : Détails de la décision (client, montant, etc.)
   - **Recommandation IA** : Approve ✅ ou Reject ❌
   - **Confiance** : Score 0-100%
   - **Raisonnement** : Explication de Claude

3. **Actions** :
   - Bouton **Approuver** (vert)
   - Bouton **Rejeter** (blanc)
   - Champ **Note** pour commentaire

### Workflow Escalation

1. **Claude détecte** une décision importante
2. **Escalation créée** automatiquement
3. **Notification** (Telegram si configuré)
4. **Vous décidez** : Approuver ou Rejeter
5. **Action appliquée** selon votre décision
6. **Logging** dans l'activité

### Auto-résolution

Certaines escalations basse priorité ont un **auto-resolve** après X heures:

- Un compte à rebours s'affiche
- Si pas de décision, Claude applique l'action par défaut
- Vous pouvez décider avant l'expiration

**Exemple**: Remise 16% → auto-approve dans 4h si pas de réponse.

### Configuration des Seuils

Menu **Paramètres** → Section **Autonomie Claude**

Vous pouvez modifier:

- **Seuil devis autonome** : Montant max HT (défaut: 10 000€)
- **Remise max autonome** : Pourcentage max (défaut: 15%)
- **Planning automatique** : Activer/désactiver
- **Notifications client** : Activer/désactiver
- **Escalader conflits planning** : Oui/Non

**💡 Conseil**: Commencez avec les valeurs par défaut, puis ajustez selon votre confiance.

---

## 🏗️ Chantiers Autonomes

### Comment ça marche ?

1. **Client accepte un devis** (email, téléphone, etc.)
2. **Vous marquez le devis** comme "Accepté" dans l'interface
3. **Claude analyse** le montant et les paramètres
4. **Deux scénarios**:

   **Scénario A — Création autonome** (montant < seuil):
   - Chantier créé automatiquement
   - Planning défini (date début calculée)
   - Client notifié par email
   - Vous recevez une notification
   - Visible dans **Chantiers**

   **Scénario B — Escalation** (montant ≥ seuil):
   - Escalation créée
   - Vous recevez notification
   - Claude recommande Approve/Reject avec confiance
   - Vous décidez
   - Si approuvé → chantier créé

### Vérifier un chantier créé

Menu **Chantiers** → Nouveau chantier visible avec:
- Status: **Planifié**
- Date début calculée
- Client et devis liés
- Détails prestation

### Planning Automatique

Claude calcule la date de début basée sur:
- Disponibilité équipe (simulée)
- Type prestation (urgence fin chantier vs régulier)
- Conflits planning existants

**Si conflit détecté**:
- Escalation créée si config activée
- Dates alternatives proposées

---

## 🤖 Optimisations IA

### Accès

Menu latéral → **Optimisations** (icône ⚡)

### Vue d'ensemble

Claude apprend en continu de vos résultats et optimise automatiquement:

1. **Performance emails** - Taux de réponse, meilleur jour
2. **Prospects perdus** - Analyse patterns et industries problématiques
3. **Scoring** - Ajustement des poids selon conversion réelle
4. **A/B Testing** - Test automatique de variants

### Interface Optimisations

#### 1. Stratégie Actuelle

Affiche en haut:
- **Top industrie convertie** : Quelle industrie converti le mieux
- **Top ville convertie** : Quelle ville convertit le mieux
- **A/B test en cours** : Quel test est actif

#### 2. Performance Emails (7 jours)

- **Envoyés** : Nombre total
- **Réponses** : Nombre de réponses
- **Taux réponse** : Pourcentage (coloré selon performance)
  - 🟢 Vert : ≥3%
  - 🟠 Orange : 2-3%
  - 🔴 Rouge : <2%
- **Meilleur jour** : Jour de la semaine optimal

#### 3. Prospects Perdus (30 jours)

- **Total perdus** : Nombre
- **Score moyen** : Score moyen des perdus (important!)
- **Industries problématiques** : Top 3 avec nombre de pertes

**💡 Si score moyen élevé** (>70): Vous perdez des bons prospects → Analysez pourquoi!

#### 4. Suggestions d'Optimisation

Liste des recommandations avec:
- **Priorité** : High (rouge), Medium (orange), Low (gris)
- **Type** : email_timing, scoring, industry_focus, etc.
- **Message** : Description actionnable

**Exemples**:
- "Taux réponse 1.2% - tester envois matinée"
- "Prospects avec téléphone convertissent 2x plus"
- "8 Restaurants perdus - revoir approche"

### Cycle d'Optimisation

Bouton **Lancer cycle d'optimisation** (en haut à droite):

- Lance analyse complète
- Génère nouvelles suggestions
- Auto-applique optimisations haute priorité
- Store learnings dans mémoire Claude

**Automatique** : Exécuté chaque soir à 20h par le scheduler.

### Learnings

Claude mémorise ce qu'il apprend:
- Meilleur jour/heure pour emails
- Industries qui convertissent
- Poids scoring optimaux
- Patterns de succès

Visible dans `/activite` → Filtrer par "claude_learning".

---

## 📊 Dashboard — Vue Quotidienne

Le dashboard principal (`/`) affiche:

### Activité du Jour

4 cartes avec stats today:
- **💰 Montant généré** (featured orange) - Total devis TTC
- **📧 Emails envoyés**
- **📄 Devis générés**
- **⚡ Réponses reçues**

### Pipeline

5 étapes visualisées:
- Nouveaux → Contactés → Répondus → Devis envoyés → Gagnés

### Graphique Évolution

Graphique 7 jours montrant progression du pipeline.

### Top Prospects (score >80)

Top 5 prospects haute priorité avec:
- Nom entreprise
- Ville + source
- Score coloré (🟢 ≥90, 🟠 85-89, 🟡 80-84)

### Timeline Activité

Flux temps réel des 10 dernières actions:
- Timestamp
- Type événement (badge coloré)
- Message descriptif

---

## 🔔 Notifications

### Types de Notifications

1. **Escalations** - Décision requise
2. **Chantiers créés** - Confirmation création auto
3. **Optimisations** - Suggestions haute priorité
4. **Erreurs** - Problèmes à résoudre

### Canaux

- **Interface web** : Badge sur "Escalations"
- **Telegram** (si configuré) : Message instantané
- **Email** (futur) : Résumé quotidien

---

## 📈 Activité — Historique Complet

Menu **Activité** → Vue complète de tout ce que fait Claude:

### Filtres

- **Type** : decision, escalation, email, enrichment, optimization, etc.
- **Status** : success, error, pending
- **Date** : Aujourd'hui, 7j, 30j, custom

### Logs Importants

- `claude_decision` - Décisions autonomes prises
- `claude_escalation` - Escalations créées
- `claude_optimization` - Cycles d'optimisation
- `claude_learning` - Nouveaux learnings
- `chantier_created` - Chantiers créés auto

### Export

Bouton **Exporter CSV** pour analyse externe.

---

## ⚙️ Configuration — Personnalisation

Menu **Paramètres** → Plusieurs sections.

### Section Autonomie Claude

**Seuils de décision**:
- Montant max devis autonome (€ HT)
- Remise max autonome (%)

**Planning**:
- ☑️ Planning automatique activé
- ☑️ Notifications client activées
- ☑️ Escalader conflits planning

**Bouton "Sauvegarder config autonomie"** en bas.

### Section Emails (existante)

Configuration Gmail, SMTP, templates.

### Section Entreprise (existante)

Infos société, coordonnées.

---

## 🎯 Bonnes Pratiques

### 1. Commencer Progressif

- **Semaine 1** : Seuils bas (5000€), surveiller toutes escalations
- **Semaine 2** : Augmenter à 8000€ si confiance OK
- **Semaine 3+** : 10 000€+ selon votre confort

### 2. Monitorer Escalations

- Répondre rapidement aux escalations high priority
- Laisser auto-resolve pour low priority si confiance haute
- Ajouter notes pour traçabilité

### 3. Analyser Optimisations

- Consulter page Optimisations 1x/semaine
- Vérifier si taux réponse email s'améliore
- Identifier patterns dans prospects perdus

### 4. Valider Learnings

Dans `/activite`, vérifier learnings Claude:
- Sont-ils cohérents avec votre expérience ?
- Ajuster si Claude tire mauvaises conclusions

### 5. Feedback à Claude

Via Telegram (si configuré):
- "Ce devis 12k€ était OK, pas besoin escalation"
- → Claude apprendra et ajustera confiance

---

## 🆘 Troubleshooting

### Escalation pas créée pour gros devis

✅ **Vérifier** : Paramètres → Seuil devis autonome. Si seuil > montant, pas d'escalation.

### Chantier pas créé automatiquement

✅ **Vérifier** :
1. Devis bien marqué "Accepté"
2. Paramètres → Planning automatique activé
3. `/activite` pour voir si erreur

### Taux réponse email toujours bas

✅ **Actions** :
1. Page Optimisations → Lire suggestions
2. Tester meilleur jour/heure recommandé
3. Lancer A/B test via cycle optimisation

### Beaucoup de prospects perdus score élevé

✅ **Analyser** :
1. Page Optimisations → Section Prospects Perdus
2. Identifier industrie problématique
3. Ajuster approche ou scoring pour cette industrie

---

## 📞 Support

- **Issues** : Créer ticket dans interface
- **Feedback** : Via Telegram ou `/activite` → Note
- **Documentation** : `/docs` pour guides techniques

---

## 🚀 Prochaines Étapes (Phase 6)

- Tests automatisés complets
- Documentation technique avancée
- Formation équipe
- Monitoring performance long terme
