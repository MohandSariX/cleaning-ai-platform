# CLAUDE.md — Proprexis

## Session Startup Protocol — Obligatoire

Au début de CHAQUE session, avant toute modification de code ou décision technique :

1. Lire ces fichiers dans cet ordre :
   - `CLAUDE.md`
   - `PROJECT_STATE.md`
   - `README.md`
   - `tasks/todo.md`
   - `tasks/lessons.md`

2. Si un fichier manque :
   - Le créer immédiatement avec une structure propre
   - Ne pas ignorer son absence
   - Ne pas continuer comme si le contexte était complet

3. Résumer l’état courant du projet en 5 lignes maximum :
   - Phase actuelle
   - Dernière phase complétée
   - Prochaine tâche logique
   - Risque ou incohérence éventuelle
   - Plan proposé

4. Ne jamais demander à Mohand “où on en est” avant d’avoir lu les fichiers ci-dessus.

5. Si `README.md`, `PROJECT_STATE.md` et `tasks/todo.md` se contredisent :
   - Signaler l’incohérence
   - Proposer une correction
   - Mettre à jour les fichiers après validation ou selon l’évidence du code

6. Ne jamais marquer une tâche comme terminée sans preuve :
   - Tests passés
   - Commande exécutée
   - Diff vérifié
   - Comportement démontré

7. À la fin de chaque session :
   - Mettre à jour `tasks/todo.md`
   - Mettre à jour `PROJECT_STATE.md` si l’état du projet a changé
   - Ajouter un résumé dans `tasks/session-review.md`
   - Ajouter une règle dans `tasks/lessons.md` uniquement si une erreur, correction ou préférence utilisateur a été identifiée

---

## Source of Truth

Les fichiers de référence sont, dans cet ordre :

1. `CLAUDE.md` — règles de travail obligatoires
2. `PROJECT_STATE.md` — état réel et synthétique du projet
3. `tasks/todo.md` — plan actif de développement
4. `tasks/lessons.md` — erreurs à ne pas répéter
5. `README.md` — roadmap complète et historique

Le README est la roadmap globale.  
`PROJECT_STATE.md` est l’état court actuel.  
`tasks/todo.md` est la vérité opérationnelle de la session en cours.

Ne jamais se baser uniquement sur la mémoire du modèle.

---

# Workflow Orchestration

## 1. Plan Mode Default

- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately — don't keep pushing
- Use plan mode for verification steps, not just building
- Write detailed specs upfront to reduce ambiguity

## 2. Subagent Strategy

- Use subagents liberally to keep main context window clean
- Offload research, exploration, and parallel analysis to subagents
- For complex problems, throw more compute at it via subagents
- One task per subagent for focused execution

## 3. Self-Improvement Loop

- After ANY correction from the user: update `tasks/lessons.md` with the pattern
- Write rules for yourself that prevent the same mistake
- Ruthlessly iterate on these lessons until mistake rate drops
- Review lessons at session start for relevant project

## 4. Verification Before Done

- Never mark a task complete without proving it works
- Diff behavior between main and your changes when relevant
- Ask yourself: "Would a staff engineer approve this?"
- Run tests, check logs, demonstrate correctness

## 5. Demand Elegance — Balanced

- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution"
- Skip this for simple, obvious fixes — don't over-engineer
- Challenge your own work before presenting it

## 6. Autonomous Bug Fixing

- When given a bug report: just fix it. Don't ask for hand-holding
- Point at logs, errors, failing tests — then resolve them
- Zero context switching required from the user
- Go fix failing CI tests without being told how

---

# Task Management

1. **Plan First**: Write plan to `tasks/todo.md` with checkable items
2. **Verify Plan**: Check in before starting implementation
3. **Track Progress**: Mark items complete as you go
4. **Explain Changes**: High-level summary at each step
5. **Document Results**: Add review section to `tasks/todo.md`
6. **Capture Lessons**: Update `tasks/lessons.md` after corrections

---

# Core Principles

## Simplicity First

Make every change as simple as possible. Impact minimal code.

## No Laziness

Find root causes. No temporary fixes. Senior developer standards.

## Minimal Impact

Changes should only touch what's necessary. Avoid introducing bugs.

---

# Proprexis Operating Rules

## Business Context

Proprexis est une entreprise de nettoyage professionnel en cours de développement, fondée par Mohand Sari.

Statut actuel :
- Développement informatique en cours
- Société pas encore créée
- Les phases nécessitant SAS, SIRET, TVA, Qonto réel ou RC Pro ne doivent pas être implémentées en production sans validation explicite

## Current Development Focus

La phase actuelle prévue est :

**Phase 7 — Tests & Optimisations**

Objectif :
- Stabiliser le code
- Compléter les tests
- Améliorer la couverture
- Optimiser performance et sécurité
- Préparer CI/CD
- Préparer le projet avant création de société

## Do Not Start Without Explicit Validation

Ne pas démarrer ces sujets sans validation explicite de Mohand :

- Création SAS réelle
- Intégration Qonto production
- Facturation légale réelle
- TVA réelle
- Expert-comptable réel
- Déploiement public du site
- Publication Google My Business
- Données SIRET/TVA définitives
- Phases 9 à 13

---

# Required Session Output Format

Après la reprise de contexte, répondre avec ce format :

```md
## État actuel
- Phase :
- Dernière phase complétée :
- Prochaine priorité :
- Risques/incohérences :
- Plan proposé :

## Fichiers lus
- [ ] CLAUDE.md
- [ ] PROJECT_STATE.md
- [ ] README.md
- [ ] tasks/todo.md
- [ ] tasks/lessons.md

## Action recommandée
...
```

Pour toute tâche non triviale, créer ou mettre à jour `tasks/todo.md` avant de coder.

---

# Done Definition

Une tâche est terminée uniquement si :

- Le code est modifié proprement
- Les tests pertinents sont lancés
- Le résultat des tests est communiqué
- Les fichiers de suivi sont mis à jour
- Les limites ou risques restants sont documentés

Ne jamais écrire “terminé” sans preuve.
