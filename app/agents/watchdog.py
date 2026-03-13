"""
Agent Watchdog — Surveillance quotidienne automatique
Tourne toutes les heures et génère un rapport matinal à 7h00.

Actions automatiques :
- Factures envoyées dont date_echeance dépassée → statut "en_retard"
- Prospects contactés depuis +7 jours → statut "à relancer"

Rapport généré :
- Factures en retard
- Prospects à relancer
- Chantiers du jour
- Nouveaux prospects haute priorité (scorés la nuit)
"""

from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.facture import Facture
from app.models.prospect import Prospect
from app.models.chantier import Chantier
from app.models.client import Client
import logging
from app.agents.telegram_notifier import notify_rapport_matinal, notify_nouvelle_facture_retard, notify_chantier_rappel

logger = logging.getLogger("proprexis.watchdog")

# État du rapport (exposé via API)
rapport_status = {
    "last_update": None,
    "factures_retard": [],
    "prospects_relancer": [],
    "chantiers_aujourd_hui": [],
    "nouveaux_prospects": [],
    "stats": {
        "factures_retard_count": 0,
        "factures_retard_montant": 0.0,
        "prospects_relancer_count": 0,
        "chantiers_aujourd_hui_count": 0,
        "nouveaux_prospects_count": 0,
    }
}


def run_watchdog():
    """
    Lance toutes les vérifications et met à jour le rapport.
    Appelé automatiquement chaque heure + à 7h00 pour le rapport matinal.
    """
    logger.info("🔍 Watchdog démarré")
    db = SessionLocal()
    today = date.today()

    try:
        # ── 1. Factures en retard ─────────────────────────────────────
        factures_retard = []
        factures_a_checker = db.query(Facture).filter(
            Facture.status == "envoyee",
            Facture.date_echeance != None,
            Facture.date_echeance < today
        ).all()

        for f in factures_a_checker:
            f.status = "en_retard"
            jours = (today - f.date_echeance).days
            entry = {
                "id": f.id,
                "numero": f.numero,
                "client_id": f.client_id,
                "client_nom": f.client.company_name if f.client else "—",
                "montant_ttc": round(f.montant_ht * (1 + f.tva_pct / 100), 2),
                "date_echeance": str(f.date_echeance),
                "jours_retard": jours,
            }
            factures_retard.append(entry)
            notify_nouvelle_facture_retard(entry)  # Alerte Telegram immédiate

        # Factures déjà en retard (déjà marquées)
        factures_deja_retard = db.query(Facture).filter(
            Facture.status == "en_retard"
        ).all()
        for f in factures_deja_retard:
            if not any(x["id"] == f.id for x in factures_retard):
                jours = (today - f.date_echeance).days if f.date_echeance else 0
                factures_retard.append({
                    "id": f.id,
                    "numero": f.numero,
                    "client_id": f.client_id,
                    "client_nom": f.client.company_name if f.client else "—",
                    "montant_ttc": round(f.montant_ht * (1 + f.tva_pct / 100), 2),
                    "date_echeance": str(f.date_echeance) if f.date_echeance else "—",
                    "jours_retard": jours,
                })

        db.commit()

        # ── 2. Prospects à relancer ───────────────────────────────────
        seuil_relance = datetime.now() - timedelta(days=7)
        prospects_relancer = []

        prospects_contacted = db.query(Prospect).filter(
            Prospect.status == "contacted",
            Prospect.last_contacted != None,
            Prospect.last_contacted < seuil_relance
        ).all()

        for p in prospects_contacted:
            p.status = "to_followup"
            jours = (datetime.now() - p.last_contacted).days
            prospects_relancer.append({
                "id": p.id,
                "company_name": p.company_name,
                "city": p.city,
                "email": p.email,
                "phone": p.phone,
                "lead_score": p.lead_score,
                "score_label": p.score_label,
                "jours_depuis_contact": jours,
            })

        # Prospects déjà marqués to_followup
        prospects_deja = db.query(Prospect).filter(
            Prospect.status == "to_followup"
        ).order_by(Prospect.lead_score.desc()).all()

        for p in prospects_deja:
            if not any(x["id"] == p.id for x in prospects_relancer):
                jours = (datetime.now() - p.last_contacted).days if p.last_contacted else 0
                prospects_relancer.append({
                    "id": p.id,
                    "company_name": p.company_name,
                    "city": p.city,
                    "email": p.email,
                    "phone": p.phone,
                    "lead_score": p.lead_score,
                    "score_label": p.score_label,
                    "jours_depuis_contact": jours,
                })

        db.commit()

        # ── 3. Chantiers du jour ──────────────────────────────────────
        chantiers_aujourd_hui = []
        chantiers = db.query(Chantier).filter(
            Chantier.date_debut == today,
            Chantier.status.in_(["planifie", "en_cours"])
        ).all()

        for c in chantiers:
            chantiers_aujourd_hui.append({
                "id": c.id,
                "titre": c.titre,
                "client_nom": c.client.company_name if c.client else "—",
                "adresse": c.adresse,
                "ville": c.ville,
                "heure_debut": c.heure_debut,
                "duree_heures": c.duree_heures,
                "type": c.type,
                "status": c.status,
            })

        # ── 3b. Rappels chantiers 2h avant ──────────────────────────
        from datetime import time as dtime
        now_hour = datetime.now().hour
        now_minute = datetime.now().minute
        for c in chantiers_aujourd_hui:
            if c.get("heure_debut"):
                try:
                    h, m = map(int, c["heure_debut"].split(":"))
                    chantier_minutes = h * 60 + m
                    now_minutes = now_hour * 60 + now_minute
                    if 115 <= chantier_minutes - now_minutes <= 125:
                        notify_chantier_rappel(c)
                except:
                    pass

        # ── 4. Nouveaux prospects haute priorité ──────────────────────
        hier = datetime.now() - timedelta(hours=24)
        nouveaux = db.query(Prospect).filter(
            Prospect.lead_score >= 70,
            Prospect.status == "scored",
            Prospect.created_at >= hier
        ).order_by(Prospect.lead_score.desc()).limit(20).all()

        nouveaux_prospects = [{
            "id": p.id,
            "company_name": p.company_name,
            "city": p.city,
            "email": p.email,
            "phone": p.phone,
            "lead_score": p.lead_score,
            "score_label": p.score_label,
            "industry": p.industry,
        } for p in nouveaux]

        # ── Mise à jour du rapport ────────────────────────────────────
        montant_total = sum(f["montant_ttc"] for f in factures_retard)

        rapport_status.update({
            "last_update": datetime.now().isoformat(),
            "factures_retard": sorted(factures_retard, key=lambda x: x["jours_retard"], reverse=True),
            "prospects_relancer": sorted(prospects_relancer, key=lambda x: x["lead_score"], reverse=True),
            "chantiers_aujourd_hui": sorted(chantiers_aujourd_hui, key=lambda x: x["heure_debut"] or ""),
            "nouveaux_prospects": nouveaux_prospects,
            "stats": {
                "factures_retard_count": len(factures_retard),
                "factures_retard_montant": round(montant_total, 2),
                "prospects_relancer_count": len(prospects_relancer),
                "chantiers_aujourd_hui_count": len(chantiers_aujourd_hui),
                "nouveaux_prospects_count": len(nouveaux_prospects),
            }
        })

        # Rapport matinal à 7h
        if datetime.now().hour == 7:
            notify_rapport_matinal(rapport_status["stats"])

        logger.info(f"✅ Watchdog terminé — {len(factures_retard)} factures retard, {len(prospects_relancer)} relances, {len(chantiers_aujourd_hui)} chantiers aujourd'hui, {len(nouveaux_prospects)} nouveaux prospects")

    except Exception as e:
        logger.error(f"❌ Watchdog erreur : {e}")
    finally:
        db.close()