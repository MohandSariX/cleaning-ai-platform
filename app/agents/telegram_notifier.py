"""
Telegram Notifier — Envoie des notifications au bot Proprexis
"""
import requests
import logging

logger = logging.getLogger("proprexis.telegram")

TELEGRAM_TOKEN  = "8617797267:AAHrlvj2MrNGO0VN9oltbUF-CPpSb5yjRuo"
TELEGRAM_CHAT_ID = "5074669846"
CRM_URL = "http://localhost:3000"  # URL de ton dashboard


def send_message(text: str) -> bool:
    """Envoie un message Telegram (supporte le Markdown)."""
    try:
        res = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            },
            timeout=10
        )
        return res.status_code == 200
    except Exception as e:
        logger.error(f"Telegram erreur : {e}")
        return False


def notify_rapport_matinal(stats: dict):
    """Rapport envoyé chaque matin à 7h00."""
    lignes = ["🌅 *Bonjour Mohand — Rapport Proprexis*\n"]

    if stats["factures_retard_count"] > 0:
        montant = stats["factures_retard_montant"]
        lignes.append(f"🔴 *{stats['factures_retard_count']} facture(s) en retard* — {montant:,.0f} € TTC à récupérer")
        lignes.append(f"   → [Voir les factures]({CRM_URL}/facturation)")

    if stats["prospects_relancer_count"] > 0:
        lignes.append(f"🟠 *{stats['prospects_relancer_count']} prospect(s) à relancer* — contactés il y a +7 jours")
        lignes.append(f"   → [Voir les prospects]({CRM_URL}/prospects)")

    if stats["chantiers_aujourd_hui_count"] > 0:
        lignes.append(f"🔵 *{stats['chantiers_aujourd_hui_count']} chantier(s) aujourd'hui*")
        lignes.append(f"   → [Voir le planning]({CRM_URL}/planning)")

    if stats["nouveaux_prospects_count"] > 0:
        lignes.append(f"🟢 *{stats['nouveaux_prospects_count']} nouveaux prospects* haute priorité cette nuit")
        lignes.append(f"   → [Voir les prospects]({CRM_URL}/prospects)")

    if len(lignes) == 1:
        lignes.append("✅ Tout est en ordre — bonne journée !")

    send_message("\n".join(lignes))


def notify_nouvelle_facture_retard(facture: dict):
    """Alerte immédiate quand une facture passe en retard."""
    msg = (
        f"⚠️ *Facture en retard*\n\n"
        f"Client : {facture['client_nom']}\n"
        f"Facture : {facture['numero']}\n"
        f"Montant : *{facture['montant_ttc']:,.0f} € TTC*\n"
        f"Retard : {facture['jours_retard']} jour(s)\n\n"
        f"→ [Voir la facture]({CRM_URL}/facturation)"
    )
    send_message(msg)


def notify_prospects_nuit(nouveaux: list):
    """Résumé des nouveaux prospects scrappés la nuit."""
    if not nouveaux:
        return
    top3 = nouveaux[:3]
    lignes = [f"🚀 *{len(nouveaux)} nouveaux prospects cette nuit !*\n"]
    for p in top3:
        lignes.append(f"• *{p['company_name']}* — {p['city']} ({p['lead_score']}/100)")
    if len(nouveaux) > 3:
        lignes.append(f"_...et {len(nouveaux) - 3} autres_")
    lignes.append(f"\n→ [Voir tous les prospects]({CRM_URL}/prospects)")
    send_message("\n".join(lignes))


def notify_chantier_rappel(chantier: dict):
    """Rappel 2h avant un chantier."""
    msg = (
        f"🔵 *Chantier dans 2h*\n\n"
        f"📋 {chantier['titre']}\n"
        f"👤 {chantier['client_nom']}\n"
        f"📍 {chantier['adresse']}, {chantier['ville']}\n"
        f"🕐 {chantier['heure_debut']}"
        + (f" ({chantier['duree_heures']}h)" if chantier.get('duree_heures') else "")
        + f"\n\n→ [Voir le planning]({CRM_URL}/planning)"
    )
    send_message(msg)


def notify_scraping_termine(dept: str, dept_name: str, stats: dict):
    """Notification quand le scraping nightly est terminé."""
    msg = (
        f"✅ *Scraping terminé — Dept {dept} ({dept_name})*\n\n"
        f"📊 {stats.get('queries_done', 0)} combinaisons traitées\n"
        f"🕐 Scoring automatique effectué\n\n"
        f"→ [Voir les nouveaux prospects]({CRM_URL}/prospects)"
    )
    send_message(msg)