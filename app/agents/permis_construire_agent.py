"""
Agent Permis de Construire — Scrape les permis accordés via data.gouv SITADEL
Source : https://www.data.gouv.fr/datasets/liste-des-permis-de-construire-et-autres-autorisations-durbanisme
Mise à jour mensuelle par le SDES.

Stratégie :
- Télécharge le CSV des permis de locaux non résidentiels (= entreprises)
- Filtre sur les départements IDF cibles
- Crée des prospects avec statut "permis_construire"
- Enrichit via Pappers pour trouver le dirigeant
"""

import io
import csv
import requests
import logging
from datetime import datetime, date, timedelta
from app.core.database import SessionLocal
from app.models.prospect import Prospect
from app.agents.activity_logger import log_system, log_error
from app.agents.telegram_notifier import send_message as tg

logger = logging.getLogger("proprexis.permis")

# URLs des CSV SITADEL sur data.gouv.fr
# Permis de construire de locaux non résidentiels (entreprises, commerces, bureaux...)
CSV_URLS = {
    "locaux": "https://www.data.gouv.fr/api/1/datasets/r/9db13a09-72a9-4871-b430-13872b4890b3",
    "logements": "https://www.data.gouv.fr/api/1/datasets/r/8f73cf2d-7bc4-4b5a-b912-718d6991f0a0",
}

# Départements IDF cibles
DEPTS_CIBLES = {"75", "77", "91", "92", "93", "94"}

# Types de projets pertinents pour nettoyage fin de chantier
TYPES_PERTINENTS = [
    "bureau", "commerce", "industrie", "entrepot", "service",
    "hotel", "restaurant", "enseignement", "sante", "logement",
    "immeuble", "résidence", "batiment", "local"
]


def download_csv(url: str) -> list[dict]:
    """Télécharge et parse un CSV SITADEL depuis data.gouv.fr"""
    try:
        logger.info(f"Téléchargement CSV : {url[:60]}")
        res = requests.get(url, timeout=60, headers={"User-Agent": "Proprexis/1.0"})
        if res.status_code != 200:
            logger.error(f"Erreur HTTP {res.status_code}")
            return []

        # Détecter l'encodage (souvent latin-1 pour les données françaises)
        content = res.content
        for encoding in ["utf-8", "latin-1", "iso-8859-1"]:
            try:
                text = content.decode(encoding)
                break
            except Exception:
                continue

        reader = csv.DictReader(io.StringIO(text), delimiter=";", quotechar='"')
        rows = list(reader)
        if rows:
            print(f"Colonnes détectées : {list(rows[0].keys())[:10]}")
        return rows

    except Exception as e:
        logger.error(f"Erreur téléchargement CSV : {e}")
        return []


def parse_permis(row: dict) -> dict | None:
    """
    Parse une ligne du CSV SITADEL (format réel data.gouv.fr).
    Colonnes réelles : DEP_CODE, COMM, DATE_REELLE_AUTORISATION, DENOM_DEM,
                       SIREN_DEM, LOCALITE_DEM, APE_DEM, etc.
    """
    try:
        # Code département
        dept = str(row.get("DEP_CODE", "") or "").strip().zfill(2)
        if dept not in DEPTS_CIBLES:
            return None

        # Nom du pétitionnaire (demandeur)
        nom = str(row.get("DENOM_DEM", "") or "").strip()
        if not nom or nom.upper() in ("", "N/A", "INCONNU", "NOM INCONNU"):
            return None

        # Filtrer particuliers (personnes physiques ont souvent CJ_DEM=1)
        cj = str(row.get("CJ_DEM", "") or "").strip()
        # CJ_DEM : 1000-1999 = personnes physiques → on garde uniquement entreprises
        try:
            cj_int = int(cj)
            if 1000 <= cj_int <= 1999:
                return None  # Particulier
        except Exception:
            pass

        # Ville
        commune = str(row.get("LOCALITE_DEM", "") or "").strip().title()
        if not commune:
            # Fallback sur commune du projet
            code_comm = str(row.get("COMM", "") or "").strip()
            commune = code_comm

        # Date autorisation
        date_aut = str(row.get("DATE_REELLE_AUTORISATION", "") or
                       row.get("DPC_AUT", "") or "").strip()

        # Filtrer permis > 18 mois
        if date_aut:
            try:
                if "-" in date_aut:
                    parts = date_aut.split("-")
                    year, month = int(parts[0]), int(parts[1])
                elif len(date_aut) == 7:  # Format YYYY-MM
                    year, month = int(date_aut[:4]), int(date_aut[5:])
                else:
                    year, month = int(date_aut[:4]), 1
                date_permis = date(year, month, 1)
                if (date.today() - date_permis).days > 548:  # 18 mois
                    return None
            except Exception:
                pass

        # Code APE / secteur — filtrer uniquement les secteurs pertinents
        ape = str(row.get("APE_DEM", "") or "").strip()

        # Codes APE acceptés (entreprises qui auront besoin de nettoyage)
        APE_ACCEPTES = {
            "41": ("construction batiment", "Promotion / Construction"),
            "43": ("construction batiment", "Travaux spécialisés"),
            "68": ("immobilier agence", "Immobilier"),
            "55": ("hotel", "Hôtellerie"),
            "56": ("restaurant", "Restauration"),
            "86": ("sante", "Santé"),
            "85": ("education", "Éducation / Formation"),
            "64": ("banque finance", "Banque / Finance"),
            "70": ("bureaux", "Direction entreprises"),
            "47": ("commerce", "Commerce de détail"),
            "46": ("commerce", "Commerce de gros"),
            "49": ("transport", "Transport"),
            "52": ("logistique", "Entreposage"),
        }

        ape_prefix = ape[:2] if len(ape) >= 2 else ""
        if ape_prefix not in APE_ACCEPTES and ape != "":
            return None  # Secteur non pertinent

        industry, secteur_label = APE_ACCEPTES.get(ape_prefix, ("construction batiment", "Autre"))

        # SIREN
        siren = str(row.get("SIREN_DEM", "") or "").strip()

        # Surface (SMOB ou SHON selon les fichiers)
        surf_keys = ["SSURFHAB", "SHO", "SHON", "SURF_LOC", "SMOB"]
        surf = 0
        for k in surf_keys:
            val = row.get(k, "")
            if val:
                try:
                    surf = float(str(val).replace(",", "."))
                    break
                except Exception:
                    pass

        # Nombre logements
        nb_log_keys = ["NB_LGT_TOT_CREES", "NB_LOG", "NBLOG"]
        nb_log = 0
        for k in nb_log_keys:
            val = row.get(k, "")
            if val:
                try:
                    nb_log = int(float(str(val).replace(",", ".")))
                    break
                except Exception:
                    pass

        return {
            "company_name": nom,
            "city": commune,
            "dept": dept,
            "nature": ape,
            "surface_m2": surf,
            "nb_logements": nb_log,
            "date_permis": date_aut,
            "industry": industry,
            "siren": siren,
            "source": "permis_construire",
        }

    except Exception as e:
        return None


def calculate_score(permis: dict) -> int:
    """Score spécifique aux permis de construire."""
    score = 60  # Base haute car signal fort

    # Surface
    surf = permis.get("surface_m2", 0)
    if surf > 1000: score += 20
    elif surf > 500: score += 15
    elif surf > 200: score += 10
    elif surf > 50: score += 5

    # Logements
    nb_log = permis.get("nb_logements", 0)
    if nb_log > 20: score += 15
    elif nb_log > 10: score += 10
    elif nb_log > 5: score += 5

    # Département prioritaire
    if permis.get("dept") in ("94", "93"):
        score += 5

    return min(100, score)


def run_permis_scraper() -> dict:
    """
    Lance le scraping des permis de construire.
    Télécharge les CSV, filtre IDF, crée les prospects.
    """
    db = SessionLocal()
    total_created = 0
    total_skipped = 0

    try:
        all_permis = []

        # Télécharger les deux fichiers (locaux + logements)
        for name, url in CSV_URLS.items():
            rows = download_csv(url)
            logger.info(f"CSV {name} : {len(rows)} lignes")

            for row in rows:
                parsed = parse_permis(row)
                if parsed:
                    all_permis.append(parsed)

        logger.info(f"Total permis IDF pertinents : {len(all_permis)}")

        # Dédupliquer par nom + ville
        seen = set()
        unique_permis = []
        for p in all_permis:
            key = f"{p['company_name'].lower()}_{p['city'].lower()}"
            if key not in seen:
                seen.add(key)
                unique_permis.append(p)

        logger.info(f"Après déduplication : {len(unique_permis)} permis")

        # Créer les prospects
        for permis in unique_permis:
            # Vérifier si déjà en base
            existing = db.query(Prospect).filter(
                Prospect.company_name == permis["company_name"],
                Prospect.city == permis["city"],
            ).first()

            if existing:
                total_skipped += 1
                continue

            score = calculate_score(permis)
            explanation = (
                f"Source : Permis de construire accordé\n"
                f"Nature : {permis.get('nature', 'N/A')}\n"
                f"Surface : {permis.get('surface_m2', 0)} m²\n"
                f"Logements : {permis.get('nb_logements', 0)}\n"
                f"Date permis : {permis.get('date_permis', 'N/A')}\n"
                f"Score {score}/100 — Signal fort : chantier imminent"
            )

            prospect = Prospect(
                company_name=permis["company_name"],
                city=permis["city"],
                industry=permis["industry"],
                lead_score=score,
                score_label="Haute priorité" if score >= 70 else "Priorité moyenne",
                score_explanation=explanation,
                status="scored",
            )
            db.add(prospect)
            total_created += 1

        db.commit()

        msg = f"🏗️ Permis de construire : {total_created} nouveaux prospects créés ({total_skipped} déjà en base)"
        logger.info(msg)
        log_system(msg, status="success", details={"created": total_created, "skipped": total_skipped})

        if total_created > 0:
            tg(
                f"🏗️ *Permis de construire*\n\n"
                f"{total_created} nouveaux prospects créés en IDF\n"
                f"Chantiers prévus dans 6-18 mois\n\n"
                f"→ [Voir les prospects](http://localhost:3000/prospects)"
            )

        return {"status": "success", "created": total_created, "skipped": total_skipped}

    except Exception as e:
        logger.error(f"Erreur permis scraper : {e}")
        log_error("permis_construire", str(e))
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()