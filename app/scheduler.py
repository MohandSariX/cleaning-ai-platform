"""
Scheduler Proprexis — Agent de prospection automatique
Tourne en arrière-plan avec FastAPI (APScheduler)

Planning hebdomadaire à 23h00 :
  Lundi     → Villes du 94 (Val-de-Marne)
  Mardi     → Villes du 93 (Seine-Saint-Denis)
  Mercredi  → Villes du 92 (Hauts-de-Seine)
  Jeudi     → Villes du 77 (Seine-et-Marne)
  Vendredi  → Villes du 75 (Paris)
  Samedi    → Villes du 91 (Essonne)
  Dimanche  → Villes du 78 (Yvelines)
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from app.agents.lead_scraper import run_lead_scraper
from app.agents.lead_scorer import run_lead_scoring
from app.agents.watchdog import run_watchdog
from app.agents.telegram_notifier import notify_scraping_termine, notify_prospects_nuit
from app.agents.gmail_agent import check_inbox
from app.agents.email_outreach_agent import run_outreach_batch, run_relances
from app.agents.pappers_agent import enrich_batch as pappers_enrich_batch
from app.agents.permis_construire_agent import run_permis_scraper
from app.agents.email_finder import find_emails_batch
from app.agents.activity_logger import log_scraping, log_scheduler_job, log_system
import logging

logger = logging.getLogger("proprexis.scheduler")

# ══════════════════════════════════════════════════════════════
#  CONFIGURATION DES ZONES
# ══════════════════════════════════════════════════════════════

ZONES = {
    "94": [  # Val-de-Marne — Lundi
        "Créteil", "Vincennes", "Saint-Maur-des-Fossés", "Champigny-sur-Marne",
        "Ivry-sur-Seine", "Vitry-sur-Seine", "Charenton-le-Pont", "Alfortville",
        "Maisons-Alfort", "Joinville-le-Pont", "Nogent-sur-Marne", "Fontenay-sous-Bois",
        "Sucy-en-Brie", "Boissy-Saint-Léger", "Orly", "Thiais", "Rungis",
        "Chennevières-sur-Marne", "Villiers-sur-Marne", "Le Perreux-sur-Marne",
        "Bonneuil-sur-Marne", "Choisy-le-Roi", "L'Haÿ-les-Roses", "Gentilly",
    ],
    "93": [  # Seine-Saint-Denis — Mardi
        "Saint-Denis", "Montreuil", "Aubervilliers", "Noisy-le-Grand",
        "Aulnay-sous-Bois", "Vitry-le-François", "Pantin", "Épinay-sur-Seine",
        "Bobigny", "Rosny-sous-Bois", "Drancy", "Livry-Gargan",
        "Le Blanc-Mesnil", "Neuilly-sur-Marne", "Gagny", "Bondy",
        "Noisy-le-Sec", "Romainville", "Les Lilas", "Bagnolet",
        "Saint-Ouen-sur-Seine", "La Courneuve", "Stains", "Villepinte",
    ],
    "92": [  # Hauts-de-Seine — Mercredi
        "Nanterre", "Boulogne-Billancourt", "Colombes", "Asnières-sur-Seine",
        "Courbevoie", "Rueil-Malmaison", "Issy-les-Moulineaux", "Levallois-Perret",
        "Neuilly-sur-Seine", "Clichy", "Clamart", "Antony",
        "Châtenay-Malabry", "Sceaux", "Bagneux", "Montrouge",
        "Vanves", "Malakoff", "Châtillon", "Meudon",
        "Garches", "Vaucresson", "La Garenne-Colombes", "Gennevilliers",
    ],
    "77": [  # Seine-et-Marne — Jeudi (villes proches de Champigny-sur-Marne)
        "Chelles", "Lagny-sur-Marne", "Torcy", "Noisiel",
        "Lognes", "Pontault-Combault", "Roissy-en-Brie", "Bussy-Saint-Georges",
        "Montévrain", "Chessy", "Ozoir-la-Ferrière", "Noisy-le-Grand",
        "Neuilly-sur-Marne", "Gagny", "Le Perreux-sur-Marne", "Villiers-sur-Marne",
        "Gournay-sur-Marne", "Emerainville", "Croissy-Beaubourg", "Gouvernes",
    ],
    "75": ["Paris"],  # Paris — Vendredi (une seule recherche, Pages Jaunes couvre tout)
    "91": [  # Essonne — Samedi
        "Évry-Courcouronnes", "Corbeil-Essonnes", "Massy", "Palaiseau",
        "Igny", "Longjumeau", "Juvisy-sur-Orge", "Viry-Châtillon",
        "Sainte-Geneviève-des-Bois", "Gif-sur-Yvette", "Les Ulis", "Orsay",
        "Brunoy", "Montgeron", "Yerres", "Draveil",
        "Grigny", "Ris-Orangis", "Athis-Mons", "Morangis",
    ],
    "78": [],  # Yvelines — retiré (trop loin)
}

# Types d'entreprises à scraper (requêtes Pages Jaunes)
QUERY_TYPES = [
    "construction batiment",
    "promoteur immobilier",
    "agence immobiliere",
    "syndic copropriete",
    "architecte",
    "renovation travaux",
]

# Pages par ville selon le département (Paris limité car très dense)
MAX_PAGES_DEFAULT = 20
MAX_PAGES_PARIS   = 50

# ── Mode test — passe à True pour un run rapide (1 ville, 1 type, 2 pages) ──
TEST_MODE = False
TEST_CITY  = "Créteil"
TEST_QUERY = "construction batiment"
TEST_PAGES = 2

# Mapping jour → département
DAY_TO_DEPT = {
    0: "94",  # Lundi
    1: "93",  # Mardi
    2: "92",  # Mercredi
    3: "77",  # Jeudi
    4: "75",  # Vendredi
    5: "91",  # Samedi
    6: "94",  # Dimanche (2ème passage Val-de-Marne — priorité zone)
}

# ══════════════════════════════════════════════════════════════
#  ÉTAT DU SCHEDULER (exposé via API)
# ══════════════════════════════════════════════════════════════

scheduler_status = {
    "running": False,
    "current_dept": None,
    "current_query": None,
    "current_city": None,
    "log": [],
    "last_run": None,
    "next_run": None,
    "stats": {
        "total_scraped_session": 0,
        "queries_done": 0,
        "queries_total": 0,
    }
}


def _log(msg: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {msg}"
    logger.info(line)
    scheduler_status["log"].append(line)
    # Garder seulement les 200 dernières lignes
    if len(scheduler_status["log"]) > 200:
        scheduler_status["log"] = scheduler_status["log"][-200:]


def run_nightly_scrape():
    """
    Tâche principale — lancée automatiquement chaque soir à 23h.
    Détermine le département du jour et scrape tous les types d'entreprises.
    """
    day_of_week = datetime.now().weekday()
    dept = DAY_TO_DEPT[day_of_week]
    cities = ZONES[dept]
    day_names = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

    scheduler_status["running"] = True
    scheduler_status["current_dept"] = dept
    scheduler_status["last_run"] = datetime.now().isoformat()
    scheduler_status["stats"] = {
        "total_scraped_session": 0,
        "queries_done": 0,
        "queries_total": len(QUERY_TYPES) * len(cities),
    }

    _log(f"🚀 Démarrage scraping nuit — {day_names[day_of_week]} | Département {dept}")
    _log(f"   {len(cities)} villes × {len(QUERY_TYPES)} types = {len(cities) * len(QUERY_TYPES)} combinaisons")
    pages_info = MAX_PAGES_PARIS if dept == "75" else MAX_PAGES_DEFAULT
    _log(f"   {pages_info} pages max par combinaison")

    # Mode test — run rapide pour vérifier le pipeline
    if TEST_MODE:
        _log("⚠️  MODE TEST — 1 ville, 1 type, 2 pages")
        active_queries = [TEST_QUERY]
        active_cities  = [TEST_CITY]
        active_pages   = TEST_PAGES
    else:
        active_queries = QUERY_TYPES
        active_cities  = cities
        active_pages   = MAX_PAGES_PARIS if dept == "75" else MAX_PAGES_DEFAULT

    try:
        for query in active_queries:
            scheduler_status["current_query"] = query
            _log(f"\n📂 Type : « {query} »")

            for city in active_cities:
                scheduler_status["current_city"] = city
                _log(f"   🏙 {city}...")
                try:
                    run_lead_scraper(
                        query=query,
                        locations=[city],
                        max_pages=active_pages
                    )
                    scheduler_status["stats"]["queries_done"] += 1
                except Exception as e:
                    _log(f"   ⚠️ Erreur {city}/{query} : {str(e)[:80]}")

        _log("\n⚙️ Scoring de tous les nouveaux prospects...")
        run_lead_scoring()
        _log("✅ Scoring terminé")
        _log(f"🎉 Nuit terminée ! Dept {dept} complet.")
        log_scraping(dept, dept_names.get(dept, dept), scheduler_status["stats"].get("prospects_scraped", 0), scheduler_status["stats"].get("queries_done", 0))

        # Notification Telegram fin de scraping
        dept_names = {
            "94": "Val-de-Marne", "93": "Seine-Saint-Denis", "92": "Hauts-de-Seine",
            "77": "Seine-et-Marne", "75": "Paris", "91": "Essonne",
        }
        notify_scraping_termine(dept, dept_names.get(dept, dept), scheduler_status["stats"])

        # Notification nouveaux prospects haute priorité
        from app.core.database import SessionLocal
        from app.models.prospect import Prospect as ProspectModel
        from datetime import timedelta
        db = SessionLocal()
        try:
            hier = datetime.now() - timedelta(hours=8)
            nouveaux = db.query(ProspectModel).filter(
                ProspectModel.lead_score >= 70,
                ProspectModel.status == "scored",
                ProspectModel.created_at >= hier
            ).order_by(ProspectModel.lead_score.desc()).limit(10).all()
            if nouveaux:
                notify_prospects_nuit([{
                    "company_name": p.company_name,
                    "city": p.city,
                    "lead_score": p.lead_score,
                } for p in nouveaux])
        finally:
            db.close()

    except Exception as e:
        _log(f"❌ Erreur critique : {str(e)}")
    finally:
        scheduler_status["running"] = False
        scheduler_status["current_dept"] = None
        scheduler_status["current_query"] = None
        scheduler_status["current_city"] = None


# ══════════════════════════════════════════════════════════════
#  INITIALISATION DU SCHEDULER
# ══════════════════════════════════════════════════════════════

_scheduler = BackgroundScheduler(timezone="Europe/Paris")


def start_scheduler():
    """Démarre le scheduler APScheduler — appelé au démarrage de FastAPI."""
    # Job 1 — Scraping nightly à 23h00
    _scheduler.add_job(
        run_nightly_scrape,
        trigger=CronTrigger(hour=23, minute=0, timezone="Europe/Paris"),
        id="nightly_scrape",
        replace_existing=True,
    )

    # Job 2 — Watchdog toutes les heures
    _scheduler.add_job(
        run_watchdog,
        trigger=CronTrigger(minute=0, timezone="Europe/Paris"),
        id="watchdog_hourly",
        replace_existing=True,
    )

    # Job 3 — Vérification boîte Gmail toutes les 15 minutes
    _scheduler.add_job(
        check_inbox,
        trigger=CronTrigger(minute="*/15", timezone="Europe/Paris"),
        id="gmail_check",
        replace_existing=True,
    )

    # Job 4 — Envoi emails prospection toutes les 10 min (9h-18h)
    _scheduler.add_job(
        run_outreach_batch,
        trigger=CronTrigger(minute="*/10", timezone="Europe/Paris"),
        id="outreach_batch",
        replace_existing=True,
    )

    # Job 5 — Relances J+3 chaque jour à 10h
    _scheduler.add_job(
        run_relances,
        trigger=CronTrigger(hour=10, minute=0, timezone="Europe/Paris"),
        id="relances",
        replace_existing=True,
    )

    # Job 6 — Enrichissement Pappers quotidien à 6h
    _scheduler.add_job(
        pappers_enrich_batch,
        trigger=CronTrigger(hour=6, minute=0, timezone="Europe/Paris"),
        id="pappers_enrich",
        replace_existing=True,
    )

    # Job 7 — Permis de construire : 1er de chaque mois à 5h
    _scheduler.add_job(
        run_permis_scraper,
        trigger=CronTrigger(day=1, hour=5, minute=0, timezone="Europe/Paris"),
        id="permis_construire",
        replace_existing=True,
    )

    # Job 8 — Email finder quotidien à 7h
    _scheduler.add_job(
        find_emails_batch,
        trigger=CronTrigger(hour=7, minute=0, timezone="Europe/Paris"),
        id="email_finder",
        replace_existing=True,
    )


    _scheduler.start()
    run_watchdog()  # Rapport immédiat au démarrage
    log_system("🚀 Scheduler Proprexis démarré", status="info")

    next_job = _scheduler.get_job("nightly_scrape")
    if next_job:
        scheduler_status["next_run"] = str(next_job.next_run_time)

    logger.info("✅ Scheduler Proprexis démarré — scraping nightly à 23h00")


def stop_scheduler():
    """Arrête proprement le scheduler — appelé à l'arrêt de FastAPI."""
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler arrêté")


def get_scheduler():
    return _scheduler