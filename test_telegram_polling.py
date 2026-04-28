"""
Script de test pour le polling Telegram
Lance le polling pendant 30 secondes et affiche les messages reçus
"""
import time
from app.agents.telegram_polling import start_polling, stop_polling, get_polling_status

print("🧪 Test Telegram Polling")
print("=" * 50)
print("\n📱 Envoie un message au bot Telegram maintenant !")
print("   (tu as 30 secondes)\n")

# Démarrer le polling
start_polling()

# Attendre 30 secondes
for i in range(30, 0, -1):
    status = get_polling_status()
    print(f"\r⏱  {i:2d}s restantes | Polling actif: {status['active']} | Thread: {status['thread_alive']}", end="", flush=True)
    time.sleep(1)

print("\n\n⏹ Arrêt du polling...")
stop_polling()

print("\n✅ Test terminé !")
print("\nSi tu as envoyé un message, tu devrais avoir reçu une réponse.")
print("Vérifie ton bot Telegram.")
