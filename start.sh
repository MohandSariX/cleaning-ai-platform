#!/bin/bash
# Script de lancement Proprexis CRM
# Charge automatiquement le .env et lance uvicorn

set -a  # Auto-export toutes les variables
source .env
set +a

echo "🚀 Démarrage Proprexis CRM..."
echo "✅ Variables d'environnement chargées"
echo ""

uvicorn main:app --reload
