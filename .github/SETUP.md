# GitHub CI/CD Setup Guide

## 1. Activer GitHub Actions

Les workflows sont déjà configurés dans `.github/workflows/`. Ils se déclencheront automatiquement lors du prochain push.

### Vérifier que Actions est activé

1. Aller sur GitHub → Settings → Actions → General
2. Vérifier que "Allow all actions and reusable workflows" est sélectionné
3. Workflow permissions : "Read and write permissions"

## 2. Configurer Branch Protection (Recommandé)

### Pour la branche `main`

Settings → Branches → Add branch protection rule

**Pattern** : `main`

**Cocher** :
- ✅ Require a pull request before merging
  - Require approvals: 1
- ✅ Require status checks to pass before merging
  - Require branches to be up to date before merging
  - Status checks that are required:
    - `test` (du workflow tests.yml)
    - `lint-backend` (du workflow lint.yml)
    - `build` (du workflow frontend-build.yml)
- ✅ Require conversation resolution before merging

**Note** : Les status checks n'apparaîtront dans la liste qu'après le premier run.

### Pour la branche `develop` (si utilisée)

Même configuration mais sans "Require approvals".

## 3. Ajouter Codecov (Optionnel)

Pour le suivi de coverage dans les PRs :

1. Aller sur [codecov.io](https://codecov.io)
2. Se connecter avec GitHub
3. Ajouter le repo `cleaning-ai-platform`
4. Copier le token CODECOV_TOKEN
5. GitHub → Settings → Secrets → Actions → New secret
   - Name: `CODECOV_TOKEN`
   - Value: [coller le token]

## 4. Tester les workflows

### Option 1 : Push direct

```bash
git add .github/
git commit -m "ci: add GitHub Actions workflows"
git push origin main
```

→ Les 3 workflows se lanceront automatiquement

### Option 2 : Via Pull Request (Recommandé)

```bash
git checkout -b ci/setup-github-actions
git add .github/ docs/CI_CD_GUIDE.md
git commit -m "ci: add GitHub Actions workflows + documentation"
git push origin ci/setup-github-actions
```

Puis créer une PR sur GitHub → Les workflows tourneront sur la PR

## 5. Voir les résultats

GitHub → Actions tab

Vous verrez :
- **Tests & Coverage** : 658 tests, coverage 80%
- **Linting & Code Quality** : Backend + Frontend + Security
- **Frontend Build** : Build Next.js

## 6. Ajouter des badges au README (Optionnel)

Ajouter en haut du README.md :

```markdown
![Tests](https://github.com/YOUR_USERNAME/cleaning-ai-platform/workflows/Tests%20%26%20Coverage/badge.svg)
![Linting](https://github.com/YOUR_USERNAME/cleaning-ai-platform/workflows/Linting%20%26%20Code%20Quality/badge.svg)
```

Remplacer `YOUR_USERNAME` par votre username GitHub.

## Dépannage

### Workflow ne se lance pas

- Vérifier que Actions est activé (voir étape 1)
- Vérifier que les fichiers `.github/workflows/*.yml` sont bien sur la branche

### Tests échouent sur CI

- Voir logs détaillés : Actions → Run en échec → test job → logs
- Reproduire en local : voir `docs/CI_CD_GUIDE.md` section "Debugging"

### Coverage < 80%

- Lancer localement : `pytest --cov=. --cov-fail-under=80`
- Identifier modules à tester : `pytest --cov=. --cov-report=term-missing`

---

**Pour plus de détails** : voir `docs/CI_CD_GUIDE.md`
