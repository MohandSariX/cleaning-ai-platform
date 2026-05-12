# CI/CD Guide — Proprexis

## Vue d'ensemble

Le projet utilise GitHub Actions pour l'intégration et le déploiement continus.

## Workflows disponibles

### 1. Tests & Coverage (`tests.yml`)

**Trigger** : Push sur main/develop/feature/fix branches + Pull Requests

**Actions** :
- Setup Python 3.11
- PostgreSQL 15 service container
- Installation dépendances Python
- Initialisation base de données de test
- Exécution `pytest --cov=. --cov-report=xml --cov-fail-under=80`
- Upload coverage vers Codecov
- Upload coverage report en artifact

**Seuil critique** : Coverage < 80% → workflow échoue

**Variables d'environnement requises** :
- `DATABASE_URL` : configuré automatiquement
- `TEST_MODE=true`
- `GROQ_API_KEY=test_key`
- `PAPPERS_API_KEY=test_key`
- `TELEGRAM_BOT_TOKEN=test_token`
- `TELEGRAM_CHAT_ID=123456789`

### 2. Linting & Code Quality (`lint.yml`)

**Trigger** : Push + Pull Requests

**Actions Backend** :
- Ruff (linter rapide)
- Black (formatage)
- isort (tri imports)
- Flake8 (erreurs critiques)

**Actions Frontend** :
- ESLint
- TypeScript type checking

**Actions Security** :
- Safety (vulnérabilités dépendances Python)

**Note** : Tous les checks sont en mode warning (`|| true`), ne bloquent pas le CI.

### 3. Frontend Build (`frontend-build.yml`)

**Trigger** : Push sur main/develop quand `frontend/**` modifié

**Actions** :
- Setup Node.js 20
- `npm ci`
- `npm run build`
- Upload build artifacts (.next)

**Retention** : 7 jours

## Configuration GitHub Secrets

### Secrets recommandés (pour production)

```
CODECOV_TOKEN         # Token Codecov pour upload coverage
DATABASE_URL_PROD     # URL PostgreSQL production
GROQ_API_KEY_PROD     # Clé Groq API production
PAPPERS_API_KEY_PROD  # Clé Pappers production
TELEGRAM_BOT_TOKEN    # Token bot Telegram production
```

**Configurer** : Settings → Secrets and variables → Actions → New repository secret

## Branch Protection Rules

### Configuration recommandée pour `main`

Settings → Branches → Add branch protection rule

```yaml
Branch name pattern: main

Protect matching branches:
  ✅ Require a pull request before merging
    ✅ Require approvals: 1
    ✅ Dismiss stale pull request approvals when new commits are pushed
  
  ✅ Require status checks to pass before merging
    ✅ Require branches to be up to date before merging
    Status checks required:
      - test (tests.yml)
      - lint-backend (lint.yml)
      - build (frontend-build.yml)
  
  ✅ Require conversation resolution before merging
  
  ✅ Do not allow bypassing the above settings
```

### Configuration pour `develop`

```yaml
Branch name pattern: develop

Protect matching branches:
  ✅ Require a pull request before merging
  ✅ Require status checks to pass before merging
    Status checks required:
      - test
```

## Workflow de développement

### Feature branch

```bash
# Créer une branche
git checkout -b feature/nouvelle-fonctionnalite

# Développer + tests
# ...

# Commit
git add .
git commit -m "feat: ajout nouvelle fonctionnalité"

# Push
git push origin feature/nouvelle-fonctionnalite
```

**GitHub Actions** : Lance automatiquement `tests.yml` + `lint.yml`

### Pull Request

1. Créer PR depuis feature → develop (ou main)
2. GitHub Actions lance tous les workflows
3. Vérifier que tous les checks passent ✅
4. Review code
5. Merge si approuvé

### Merge main

```bash
git checkout main
git merge develop
git push origin main
```

**GitHub Actions** : Lance tous les workflows + build frontend

## Debugging CI/CD

### Tests échouent sur CI mais passent en local

**Causes fréquentes** :
1. Variables d'environnement manquantes
2. Base de données non initialisée
3. Dépendances manquantes dans requirements.txt
4. Différence Python version (local vs CI)

**Solution** :
```bash
# Reproduire l'environnement CI en local
docker run -d --name postgres-test \
  -e POSTGRES_USER=proprexis_user \
  -e POSTGRES_PASSWORD=proprexis_password \
  -e POSTGRES_DB=proprexis_test \
  -p 5432:5432 postgres:15

export DATABASE_URL=postgresql://proprexis_user:proprexis_password@localhost:5432/proprexis_test
export TEST_MODE=true

pytest --cov=. --cov-report=term-missing --cov-fail-under=80
```

### Coverage drop

Si coverage passe sous 80% :

1. Identifier modules non couverts :
```bash
pytest --cov=. --cov-report=term-missing | grep "0%"
```

2. Ajouter tests manquants dans `tests/`

3. Vérifier localement :
```bash
pytest --cov=. --cov-fail-under=80
```

### Lint warnings

```bash
# Fixer automatiquement
black .
isort .
ruff check . --fix
```

## Monitoring

### Voir les runs

GitHub → Actions tab → Sélectionner workflow

### Télécharger artifacts

GitHub → Actions → Sélectionner run → Artifacts section

**Disponible** :
- `coverage-report` (coverage.xml)
- `frontend-build` (.next build)

### Badges

Ajouter dans README.md :

```markdown
![Tests](https://github.com/username/repo/workflows/Tests%20&%20Coverage/badge.svg)
![Linting](https://github.com/username/repo/workflows/Linting%20&%20Code%20Quality/badge.svg)
[![codecov](https://codecov.io/gh/username/repo/branch/main/graph/badge.svg)](https://codecov.io/gh/username/repo)
```

## Optimisations

### Cache dependencies

Les workflows utilisent déjà :
- `cache: 'pip'` pour Python
- `cache: 'npm'` pour Node.js

### Matrix strategy (avancé)

Pour tester sur plusieurs versions Python :

```yaml
strategy:
  matrix:
    python-version: [3.10, 3.11, 3.12]
```

### Skip CI

Pour commits documentation uniquement :

```bash
git commit -m "docs: mise à jour README [skip ci]"
```

## Maintenance

### Mettre à jour actions

Vérifier versions actions GitHub :
- `actions/checkout@v4` → dernière : v4
- `actions/setup-python@v5` → dernière : v5
- `actions/setup-node@v4` → dernière : v4

Mettre à jour si nouvelles versions disponibles.

### Nettoyer artifacts

Settings → Actions → General → Artifact and log retention

**Recommandé** : 7 jours (par défaut dans workflows)

---

**Créé** : 2026-05-12  
**Dernière mise à jour** : 2026-05-12
