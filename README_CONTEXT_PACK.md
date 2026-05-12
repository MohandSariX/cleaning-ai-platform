# Proprexis Context Pack

Ce pack contient les fichiers à ajouter à la racine du projet Proprexis pour forcer Claude à reprendre le contexte correctement à chaque session.

## Fichiers inclus

```txt
CLAUDE.md
PROJECT_STATE.md
PROMPT_REPRISE_CONTEXTE.md
tasks/
  todo.md
  lessons.md
  session-review.md
```

## Installation

Dézipper le contenu à la racine du projet.

La racine doit ressembler à ceci :

```txt
proprexis/
  CLAUDE.md
  README.md
  PROJECT_STATE.md
  PROMPT_REPRISE_CONTEXTE.md
  tasks/
    todo.md
    lessons.md
    session-review.md
```

## Utilisation

Après avoir déposé les fichiers, ouvrir `PROMPT_REPRISE_CONTEXTE.md`, copier le prompt, puis le donner à Claude Code.

Claude devra :
1. Lire les fichiers de contexte
2. Auditer le code réel
3. Mettre à jour `PROJECT_STATE.md`
4. Mettre à jour `tasks/todo.md`
5. Proposer un plan Phase 7
6. S’arrêter avant de coder
